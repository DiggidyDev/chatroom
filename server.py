import selectors
import socket

PORT = 65501
HOST = "127.0.0.1"


def accept_wrapper(fileobj):
    pass

def multi_conn():
    sel = selectors.DefaultSelector()

    # Create and bind the socket
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))

    # Listen, don't use blocking calls
    lsock.listen()
    lsock.setblocking(False)

    # Socket registration
    sel.register(lsock, selectors.EVENT_READ, data=None)

    while True:
        events = sel.select(timeout=None)
        for k, m in events:
            if not k.data:
                accept_wrapper(k.fileobj)


def single_conn():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))

        s.listen()
        conn, addr = s.accept()

        with conn:
            print(f"Connection made from {addr}")
            while True:
                data = conn.recv(1024)

                if not data:
                    break

                conn.sendall(f"Hello {addr[0]}!".encode("utf-8"))


single_conn()