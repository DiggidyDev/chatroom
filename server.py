import selectors
import socket
import types

PORT = 65501
HOST = "127.0.0.1"


def accept_wrapper(sock, sel: selectors.DefaultSelector):
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
        for k, mask in events:
            if not k.data:
                accept_wrapper(k.fileobj, sel)
            else:
                service_connection(k, mask, sel)


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


def service_connection(key, mask, sel: selectors.DefaultSelector):
    sock = key.fileobj
    data = key.data

    # Incoming data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            print(f"Received {repr(recv_data)} from {data.connid}")
            data.recv_total += len(recv_data)

        # Client's socket closed, so we do as well
        if not recv_data or data.recv_total == data.msg_total:
            print(f"Closing connection with {data.connid}")
            sel.unregister(sock)  # No longer monitored by the selector
            sock.close()

    # Outgoing data
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {repr(data.outb)} to {data.connid}")
            sent = sock.send(data.outb)  # Returns the number of bytes sent
            data.outb = data.outb[sent:]  # Remove bytes from send buffer


conn_single()
