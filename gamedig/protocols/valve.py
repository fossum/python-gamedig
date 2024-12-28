from gamedig.protocols.core import Core
import socket
import struct

class Valve(Core):
    async def query(self):
        request = b'\xFF\xFF\xFF\xFFTSource Engine Query\0'
        response = await self._query(request, 5) # Expecting a short (2 bytes) response initially

        # Check for challenge response (0x41)
        if response.get('challenge'): # If challenge, re-query with the challenge
            request += response['challenge'] # Append challenge to the request
            response = await self._query(request, None)  # No specific packet length expected now

        return response.get('info', {}) # Extract and return 'info' if present, else {}

    async def _query(self, request, response_packet_length): # Handles the actual querying and retry logic
        return await super().query(request, response_packet_length)

    def can_parse(self, packets, response_packet_length):
        if len(packets) > 0:
            packet = packets[0]
            if response_packet_length is not None:
                return len(packet) >= response_packet_length # For the initial handshake

            # If it is split packet response (goldsrc or source)
            return len(packet) > 6 and packet[4] in [0x49, 0x6D] # Check if it has the header and a valid response type

        return False

    def parse_packets(self, packets):
        packet = packets[0]
        header = packet[0:4]
        payload = packet[4:] # Valve protocols start after first 4 bytes

        if header == b'\xFF\xFF\xFF\xFF' and payload.startswith((b'I', b'm', b'T')):

            state = {} # Create a dict to hold the parsed response

            # GoldSrc or Source servers
            if payload.startswith(b'I'):  # Information packet for GoldSrc and Source
                state['info'] = self._parse_info(payload[1:]) # Skip initial byte for parsing
            elif payload.startswith(b'm'):  # Multiple packets
                state['info'] = self._parse_info(b''.join(packets)[1:]) # Combine the packet payloads for parsing
            elif payload.startswith(b'T'):
                state['challenge'] = payload[1:]
            else:
                print(f"Unexpected payload: {payload}")  # Add a print statement to inspect the unexpected response

            return state

        else:
            print(f"Unexpected header: {header}") # Add a print statement to inspect the unexpected header

            return None



    def _parse_info(self, buffer): # The data from the first packet
        info = {}
        offset = 0

        info['protocol'], offset = self._read_byte(buffer, offset)
        info['name'], offset = self._read_string(buffer, offset)
        info['map'], offset = self._read_string(buffer, offset)
        info['game_dir'], offset = self._read_string(buffer, offset)
        info['game_desc'], offset = self._read_string(buffer, offset)
        info['app_id'], offset = self._read_short(buffer, offset)
        info['num_players'], offset = self._read_byte(buffer, offset)
        info['max_players'], offset = self._read_byte(buffer, offset)
        info['num_bots'], offset = self._read_byte(buffer, offset)
        info['dedicated'], offset = self._read_byte(buffer, offset)
        info['os'], offset = self._read_byte(buffer, offset)
        info['password'], offset = self._read_byte(buffer, offset)  # boolean 0/1
        info['secure'], offset = self._read_byte(buffer, offset)  # boolean 0/1
        # ... other fields as needed

        return info

