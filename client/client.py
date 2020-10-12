import socket

from user import User
from utils.debug import debug

PORT = 65501
HOST = "127.0.0.1"

u = User("Nickname")


@debug(verbose=True)
def connect():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(f"Hello from {u}".encode("utf-8"))
        data = s.recv(1024)

        print(f"Received: {data.decode('utf-8')}")


connect()
