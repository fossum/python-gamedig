import asyncio
import socket
import struct
import time


class Core:
    def __init__(self, gamedig, options):
        self.gamedig = gamedig
        self.options = options

        self.encoding = options.get('encoding', 'utf-8')
        self.host = options.get('host')
        self.port = options.get('port', 0)
        self.maxAttempts = options.get('maxAttempts', 3)
        self.socketTimeout = options.get('socketTimeout', 5)

    async def query(self, request_packet, response_packet_length):

        packets = []
        got_packets = False
        attempt = 0
        start = time.monotonic()

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(self.socketTimeout)

        while attempt < self.maxAttempts and time.monotonic() - start < self.options['givenTimeout']:
            try:
                s.sendto(request_packet, (self.host, self.port))

                while True: # Keep reading packets until an error or timeout
                    packet, _ = s.recvfrom(4096)
                    packets.append(packet)

                    got_packets = True

                    # Check if all expected packets have arrived
                    if (self.can_parse(packets, response_packet_length)):
                        return self.parse_packets(packets)

            except socket.timeout:
                pass  # Just retry

            except Exception as e: # Catch generic exceptions during packet handling
                print(f"Error during query: {e}")
                return None # Or raise the exception depending on desired error handling

            finally:
                attempt += 1

    def can_parse(self, packets, response_packet_length):
        return len(packets) > 0 and len(packets[0]) >= response_packet_length

    def parse_packets(self, packets):
        raise NotImplementedError("Subclasses must implement this method.")

    def _read_string(self, buffer, offset=0):
        """Reads a null-terminated string from a buffer."""
        end = buffer.find(b'\0', offset)
        if end == -1:
            raise ValueError("Unterminated String")
        result = buffer[offset:end].decode(self.encoding)

        return result, end + 1

    def _read_short(self, buffer, offset=0):
        """Reads a short (2 bytes) from the buffer."""
        try:
            value = struct.unpack('<h', buffer[offset:offset + 2])[0]
            return value, offset + 2
        except struct.error as exc:
            raise ValueError("Invalid Short") from exc

    def _read_long(self, buffer, offset=0):
        """Reads a long (4 bytes) from the buffer."""
        try:
            value = struct.unpack('<l', buffer[offset:offset + 4])[0]  # Little-Endian
            return value, offset + 4

        except struct.error as exc:
            raise ValueError("Invalid Long") from exc

    def _read_byte(self, buffer, offset):
        try:
            value = buffer[offset]
            return value, offset + 1
        except IndexError as exc:
            raise ValueError("Invalid Byte") from exc

    def _read_float(self, buffer, offset):
        try:
            value = struct.unpack('<f', buffer[offset:offset + 4])[0]  # Little-Endian
            return value, offset + 4
        except struct.error as exc:
            raise ValueError("Invalid Float") from exc
