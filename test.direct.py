import socket

server_port = 2456
# server_ip_address = "192.168.1.65"
server_ip_address = "thefoss.org"
server_address = (server_ip_address, server_port)

# Construct A2S_INFO request packet
request_packet = b'\xFF\xFF\xFF\xFFTSource Engine Query\0'

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)  # Set a timeout of 5 seconds

try:
    # Send the packet
    sent = sock.sendto(request_packet, server_address)

    # Receive the response (with a buffer size, e.g., 4096)
    data, server = sock.recvfrom(4096)

    # Parse the response (This part is highly complex and omitted here)
    # ...  (You'd need to decode the byte array according to the A2S_INFO response format) ...

    print(f"Received {len(data)} bytes from {server}")
    # ... (Process the parsed data) ...

except socket.timeout:
    print("Request timed out")
finally:
    sock.close()