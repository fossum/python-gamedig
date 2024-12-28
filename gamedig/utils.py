
from dataclasses import dataclass
import socket
from typing import Callable


@dataclass
class GameDefinition:
    name: str
    protocol: str
    port: int
    options: dict[str, str | int]


async def process_packets(
    host: str,
    port: int,
    request: bytes,
    packet_handler: Callable,
    is_finished: Callable[[None], bool],
    timeout: float = 5.0,
    max_attempts: int = 3,
    encoding: str = "utf8",
) -> dict:
    """Processes UDP packets for game server queries.

    Args:
        host: The server hostname or IP address.
        port: The server port.
        request: The initial request to send.
        packet_handler: A function to handle each received packet.
        is_finished: A function to check if the query is finished.
        timeout: Timeout in seconds.
        max_attempts: Maximum number of attempts to query the server.
        encoding: Encoding to use for string values.

    Returns:
        A dictionary containing the server information.
    """
    attempts = 0
    state = None

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.settimeout(timeout)
        udp_socket.sendto(request, (host, port))

        while attempts < max_attempts:
            try:
                data, address = udp_socket.recvfrom(65535)
                state = await packet_handler(data, address, state, udp_socket)

                if is_finished(state):
                    return state

            except socket.timeout:
                attempts += 1
                if attempts < max_attempts:
                    # Resend the request on timeout
                    udp_socket.sendto(request, (host, port))

    raise TimeoutError("Max attempts reached, server did not respond in time.")
