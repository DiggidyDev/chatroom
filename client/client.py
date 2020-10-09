import socket

PORT = 65501
HOST = "127.0.0.1"


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    a = s.sendall(b"Hello :)")
    data = s.recv(1024)

    print(f"Received: {data.decode('utf-8')}")
