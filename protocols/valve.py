import socket
import struct
from gamedig.protocols.base import Base
from gamedig.utils import process_packets

class Valve(Base):
    async def query(self):
        request = b'\xFF\xFF\xFF\xFFTSource Engine Query\0'

        response = await process_packets(
            self.gamedig.host, self.gamedig.port, request, self._handle_packet, 
            lambda state: state and state.get('done', False)
        )

        return response.get('info', {})

    async def _handle_packet(self, data, address, state, udp_socket):
        if not state:
            state = {
                'goldsrc': False,
                'response_type': None,
                'num_packets': 0,
                'packets': [],
                'challenge': None,
                'done': False,
                'info': {}
            }

        header = data[0:5]
        payload = data[5:]

        # Is GoldSrc (old version of the protocol, pre-2008)
        if header == b'\xFF\xFF\xFF\xFF\x49' and not state['challenge']:
            state['goldsrc'] = True
        elif header == b'\xFF\xFF\xFF\xFF\x41':
            state['goldsrc'] = True

        # GoldSrc response
        if state['goldsrc']:
            # GoldSrc without the challenge
            if header == b'\xFF\xFF\xFF\xFF\x49':
                state['response_type'] = header[4]
                state['info'] = self._parse_goldsrc_info_packet(payload)
                state['done'] = True
                return state
            # GoldSrc with the challenge
            elif header == b'\xFF\xFF\xFF\xFF\x41':
                state['response_type'] = header[4]
                state['challenge'] = payload
                request = b'\xFF\xFF\xFF\xFFTSource Engine Query\0' + state['challenge']
                # Send the challenge request to the server
                udp_socket.sendto(request, (self.gamedig.host, self.gamedig.port))
                return state

        # Source response
        if not state['goldsrc']:
            response_type = payload[0:1]

            # Check if the response is a simple (uncompressed) packet
            if response_type == b'\x49' or response_type == b'\x41':
                # If it's a challenge packet, send a new request with the challenge number
                if response_type == b'\x41':
                    state['challenge'] = payload[1:]
                    request = b'\xFF\xFF\xFF\xFFTSource Engine Query\0' + state['challenge']
                    udp_socket.sendto(request, (self.gamedig.host, self.gamedig.port))
                    return state
                # If it's an info packet, parse it and mark as done
                else:
                    state['response_type'] = response_type
                    state['info'] = self._parse_source_info_packet(payload[1:])
                    state['done'] = True
                    return state

            # Check if the response is a multi-packet
            elif response_type == b'\x30':
                if not state['packets']:
                    # Read header information from the first packet
                    packet_id, num_packets, packet_num, max_packet_size = struct.unpack('<lBBH', payload[1:9])
                    state['num_packets'] = num_packets
                    state['packets'] = [None] * num_packets

                packet_id, num_packets, packet_num, max_packet_size = struct.unpack('<lBBH', payload[1:9])

                # Extract and store the payload of the current packet
                packet_payload = payload[9:]
                state['packets'][packet_num] = packet_payload

                # If all packets have been received, combine and parse them
                if all(state['packets']):
                    combined_payload = b''.join(state['packets'])
                    state['info'] = self._parse_source_info_packet(combined_payload[4:])
                    state['done'] = True
                    return state
                else:
                    return state

        # Default case: return the current state unchanged if no conditions are met
        return state

    def _parse_goldsrc_info_packet(self, data):
        info = {}
        info['ip'], data = self._read_string(data)
        info['name'], data = self._read_string(data)
        info['map'], data = self._read_string(data)
        info['game_dir'], data = self._read_string(data)
        info['game_desc'], data = self._read_string(data)
        info['num_players'] = data[0]
        info['max_players'] = data[1]
        info['protocol'] = data[2]
        info['dedicated'] = chr(data[3])
        info['os'] = chr(data[4])
        info['password'] = data[5] == 1
        info['is_mod'] = data[6] == 1
        data = data[7:]

        if info['is_mod']:
            mod_info = {}
            mod_info['url_info'], data = self._read_string(data)
            mod_info['url_dl'], data = self._read_string(data)
            data = data[1:]  # null byte
            mod_info['mod_version'] = struct.unpack('<i', data[:4])[0]
            mod_info['mod_size'] = struct.unpack('<i', data[4:8])[0]
            mod_info['sv_only'] = data[8] == 1
            mod_info['dll'] = data[9] == 1
            data = data[10:]
            info['mod_info'] = mod_info

        info['secure'] = data[0] == 1
        info['num_bots'] = data[1]

        return info

    def _parse_source_info_packet(self, data):
        info = {}
        info['protocol'] = data[0]
        info['name'], data = self._read_string(data)
        info['map'], data = self._read_string(data)
        info['game_dir'], data = self._read_string(data)
        info['game_desc'], data = self._read_string(data)
        info['app_id'] = struct.unpack('<h', data[:2])[0]
        info['num_players'] = data[2]
        info['max_players'] = data[3]
        info['num_bots'] = data[4]
        info['dedicated'] = chr(data[5])
        info['os'] = chr(data[6])
        info['password'] = data[7] == 1
        info['secure'] = data[8] == 1
        data = data[9:]

        if info['app_id'] == 2400:  # The Ship
            info['mode'] = data[0]
            info['witnesses'] = data[1]