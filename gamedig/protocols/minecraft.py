import asyncio
import json
import struct

from gamedig.protocols.core import Core
from gamedig.utils import process_packets


class Minecraft(Core):  # Inherit from Core
    async def query(self):
        full_stat_request = b"\x00\x00\x00\x00"  # Placeholder request.  We'll populate session id after the first response.

        async def _handle_packet(data, address, state, udp_socket):

            if not state:  # Initialize state
                state = {}

            # Parse Handshake Response to get session ID
            if "session_id" not in state:
                session_id = struct.unpack(">l", data[5:9])[0]
                # print("Session ID:", session_id)
                state["session_id"] = session_id

                # Prepare Full Stat request (0x00 packet type + session ID + padding)
                # print(struct.pack('>lb', 0, state['session_id']))

                full_stat_request = struct.pack(">lb", 0, state["session_id"])
                udp_socket.sendto(full_stat_request + b"\x00\x00\x00\x00", address)

                return state

            # Parse Full Stat Response
            else:

                # Parse the null-byte-separated fields
                try:

                    data_str = data.decode(self.encoding)
                    fields = data_str.split("\x00\x00")  # Split by double null byte

                    if fields[0] == "\x01\x01\x00\x00":
                        fields[0] = "\x00"  # Strip the initial bytes for query mode

                    # Handle if server responds in status mode (json data) or query mode (legacy string data)

                    if fields[0].startswith(b"\xa7"):  # JSON response if b'\xa7{'
                        json_data = json.loads(fields[0][1:])
                        info = self._process_json_response(json_data)

                    else:  # Legacy string response
                        info = self._process_legacy_response(fields)

                    state["info"] = info
                    return state

                except (IndexError, ValueError, UnicodeDecodeError) as e:
                    print(f"Error parsing Minecraft response: {e}")
                    return None  # Or handle the error as needed

        response = await process_packets(
            self.gamedig.host,
            self.gamedig.port,
            b"\xFE\x01",
            _handle_packet,
            lambda state: state and "info" in state,
        )
        return response.get("info", {})

    def _process_legacy_response(self, fields):
        info = {}
        try:
            info["motd"] = fields[3].replace("\xa7", "§")
            info["game_type"] = fields[5]
            info["map"] = fields[7]
            info["numplayers"] = int(fields[9])
            info["maxplayers"] = int(fields[11])
            info["hostip"] = fields[
                13
            ]  # This will be the internal IP, not useful usually
            info["hostport"] = int(fields[15])
            info["version"] = fields[2]  # e.g. 1.19.2
        except (IndexError, ValueError) as e:
            print(f"Error processing legacy response: {e}")

        return info

    def _process_json_response(self, json_data):
        info = {}
        info["version"] = json_data.get("version", {}).get("name")
        info["motd"] = json_data.get("description", {}).get(
            "text"
        )  # Use 'text' for consistency

        players = json_data.get("players", {})
        info["numplayers"] = players.get("online", 0)
        info["maxplayers"] = players.get("max", 0)

        # Additional fields can be extracted as needed
        return info
