import pickle
import selectors
import socket
import types
from concurrent.futures import ThreadPoolExecutor

from ui.cnslserver import ConsoleWindow
from utils.debug import debug

PORT = 65501
HOST = "127.0.0.1"


class Server:

    def __init__(self, host: str, port: int):
        self.conn = (host, port)
        self.clients = []
        self.host = host
        self.port = port

    @debug(verbose=True)
    def accept_wrapper(self, sock, sel: selectors.DefaultSelector) -> None:
        # Accept the incoming connection
        conn, addr = sock.accept()
        print(f"Connection successfully made from {':'.join(str(i) for i in addr)}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        sel.register(conn, events=events, data=data)

    @debug(verbose=True)
    def conn_multi(self) -> None:
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
                    self.accept_wrapper(k.fileobj, sel)
                else:
                    self.service_connection(k, mask, sel)

    def conn_single(self):
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

    def parse_content(self):
        pass

    def service_connection(self, key, mask, sel: selectors.DefaultSelector):
        sock = key.fileobj
        data = key.data

        # Incoming data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)
            if recv_data:
                sender = pickle.loads(recv_data)["user"]
                print(f"RECV: {pickle.loads(recv_data)['content']} from {sender.get_uuid()} - {sender.nickname}")
                data.outb += recv_data

            # Client's socket closed, so we do as well
            else:
                print(f"Closing connection with {data.addr}")
                sel.unregister(sock)  # No longer monitored by the selector
                sock.close()

        # Outgoing data
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                print(f"ECHO: {pickle.loads(data.outb)} to {data.addr}")
                sent = sock.send(pickle.dumps(data.outb))  # Returns the number of bytes sent
                data.outb = data.outb[sent:]  # Remove bytes from send buffer


server = Server(HOST, PORT)


def startConsole():
    import sys
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    ConsoleWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as t:
        t.submit(server.conn_multi)
        t.submit(startConsole)
