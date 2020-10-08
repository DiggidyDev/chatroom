import selectors
import socket
import types

PORT = 65501
HOST = "127.0.0.1"


def accept_wrapper(sock: socket.socket, sel: selectors.DefaultSelector):
    # Accept the incoming connection
    conn, addr = sock.accept()
    print(f"Connection successfully made from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(sock, events=events, data=data)


def conn_multi():
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


def conn_single():
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


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            print(f"Received {repr(recv_data)} from {data.connid}")
            data.recv_total += len(recv_data)
        if not recv_data or data.recv_total == data.msg_total:
            print(f"Closing connection with {data.connid}")


conn_single()
