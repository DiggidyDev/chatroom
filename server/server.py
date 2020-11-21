import datetime
import pickle
import selectors
import socket
import threading
import types

from PyQt5 import QtCore, QtWidgets

from clientside.user import User
from utils import fmt
from utils.debug import debug
from utils.update import update_msg_list

PORT = 65501
HOST = socket.gethostbyname(socket.gethostname())


class Server(QtWidgets.QMainWindow):

    def __init__(self, host: str, port: int):
        super().__init__()

        self.conn = (host, port)
        self.clients = []
        self.host = host
        self.port = port
        self.sel = selectors.DefaultSelector()
        self.user = User("Server")
        
        self.setup_ui()

    @debug(verbose=True)
    def accept_wrapper(self, sock: socket.socket) -> None:
        # Accept the incoming connection
        conn, addr = sock.accept()
        print(f"Connection successfully made from {':'.join(str(i) for i in addr)}")

        # Reserve UUID for when initial connection message is received
        # But fill in other necessary details
        client_details = {
            "conn": conn,
            "user": None
        }
        self.clients.append(client_details)

        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events=events, data=data)

    @debug(verbose=True)
    def conn_multi(self) -> None:
        # Create and bind the socket
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind(("", PORT))

        # Listen, don't use blocking calls
        lsock.listen()
        lsock.setblocking(False)

        # Socket registration
        self.sel.register(lsock, selectors.EVENT_READ, data=None)
        while True:
            events = self.sel.select(timeout=None)
            for k, mask in events:

                if not k.data:
                    self.accept_wrapper(k.fileobj)
                else:
                    self.handle_conn(k, mask)

    @debug(verbose=True)
    def conn_single(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))

            s.listen()
            conn, addr = s.accept()

            with conn:
                print(f"Connection made from {addr}")
                while True:
                    data = conn.recv(4096)

                    if not data:
                        break

                    conn.sendall(f"Hello {addr[0]}!".encode("utf-8"))

    def get_client_by(self, criteria: str, value) -> dict:
        for client in self.clients:
            for k, v in client.items():

                if k == criteria and value == v:
                    return client

                elif isinstance(v, User) and str(v) == value:
                    return client

    def handle_conn(self, key, mask):
        sock = key.fileobj
        data = key.data

        # Incoming data
        if mask & selectors.EVENT_READ:
            recv_bytes = None
            try:
                recv_bytes = sock.recv(4096)
            except ConnectionResetError:
                print(f"Closing connection with {data.addr}")
                client = self.get_client_by("conn", sock)
                self.userList.takeItem(self.clients.index(client))
                self.sel.unregister(sock)  # No longer monitored by the selector
                sock.close()
                self.clients.remove(client)
                self.send_message(f"{client['user']} left.")
                update_msg_list(self, fmt.content(content=f"{client['user']} left.",
                                                  user=self.user,
                                                  system_message=True))

            if recv_bytes:
                recv_content = pickle.loads(recv_bytes)
                sender = recv_content["user"]
                print(f"RECV: {recv_content['content']} from {sender.get_uuid()} - {sender.nickname}")
                if recv_content['system-message'] and \
                        recv_content['content'] == "Initial connection.":
                    item = QtWidgets.QListWidgetItem()
                    item.setText(f"{sender}")
                    self.get_client_by("conn", sock)["user"] = sender
                    self.userList.addItem(item)
                data.outb += recv_bytes

        # Outgoing data
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                sent = self.send_message(data.outb)
                print(f"ECHO: {pickle.loads(data.outb)} to {data.addr}")
                update_msg_list(self, pickle.loads(data.outb))
                try:
                    data.outb = data.outb[sent:]  # Remove bytes from send buffer
                except ReferenceError:
                    print("oh no")

    def kick(self):
        current_user = self.userList.currentItem()
        if current_user is not None:
            client = self.get_client_by("name", current_user.text())
            self.send_message("You have been kicked.", client)
            try:
                self.sel.unregister(client["conn"])
                client["conn"].close()
            except BaseException as e:
                pass
            finally:
                self.clients.remove(client)
                self.userList.takeItem(self.userList.selectedIndexes()[0].row())
                self.send_message(f"{client['user']} was kicked.")
                update_msg_list(self, fmt.content(content=f"{client['user']} was kicked.",
                                                  user=self.user,
                                                  system_message=True))

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("self", "Server", None))
        self.serverInfoGroupBox.setTitle(_translate("self", "Server info", None))
        self.IPLabel.setText(_translate("self", f"<html><head/><body><p align=\"center\">IP: {self.host}</p></body></html>", None))
        self.PORTLabel.setText(_translate("self", f"<html><head/><body><p align=\"center\">PORT: {self.port}</p></body></html>", None))
        self.usersGroupBox.setTitle(_translate("self", "Users", None))
        self.muteButton.setText(_translate("self", "Mute", None))
        self.kickButton.setText(_translate("self", "Kick", None))
        self.msgListGroupBox.setTitle(_translate("self", "Messages", None))
        self.msgList.setSortingEnabled(False)
        current_time = datetime.datetime.now()
        item = self.msgList.item(0)
        item.setText(_translate("MyWindow", f"{current_time.strftime('[%Y/%m/%d  -  %H:%M %p]')}"))
        self.msgList.setSortingEnabled(False)

    def send_message(self, msg, client=None):
        if not client:
            sent = 0
            if isinstance(msg, bytes):
                for client in self.clients:
                    sent = client["conn"].send(pickle.dumps(msg))
            else:
                for client in self.clients:
                    final_msg = fmt.content(content=msg,
                                            system_message=True,
                                            user=self.user)
                    sent = client["conn"].send(pickle.dumps(final_msg))
        else:
            if isinstance(msg, bytes):
                sent = client["conn"].send(pickle.dumps(msg))
            else:
                final_msg = fmt.content(content=msg,
                                        system_message=True,
                                        user=self.user)
                sent = client["conn"].send(pickle.dumps(final_msg))
        return sent

    def setup_ui(self):
        self.setObjectName("Server")
        self.resize(437, 316)
        self.setMinimumSize(QtCore.QSize(437, 316))
        self.setMaximumSize(QtCore.QSize(437, 316))
        
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.serverInfoGroupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.serverInfoGroupBox.setObjectName("serverInfoGroupBox")
        self.serverInfoGroupBox.setGeometry(QtCore.QRect(10, 230, 421, 61))

        self.horizontalLayoutWidget = QtWidgets.QWidget(self.serverInfoGroupBox)
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 20, 411, 31))

        self.serverInfoBoxLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.serverInfoBoxLayout.setObjectName("serverInfoBoxLayout")
        self.serverInfoBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.IPLabel = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.IPLabel.setObjectName("IPLabel")

        self.serverInfoBoxLayout.addWidget(self.IPLabel)

        self.PORTLabel = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.PORTLabel.setObjectName("PORTLabel")

        self.serverInfoBoxLayout.addWidget(self.PORTLabel)

        self.usersGroupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.usersGroupBox.setObjectName("usersGroupBox")
        self.usersGroupBox.setGeometry(QtCore.QRect(220, 0, 211, 221))

        self.gridLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QtCore.QRect(230, 20, 191, 191))

        self.usersGridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.usersGridLayout.setObjectName("usersGridLayout")
        self.usersGridLayout.setContentsMargins(0, 0, 0, 0)

        self.muteButton = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.muteButton.setObjectName("muteButton")

        self.usersGridLayout.addWidget(self.muteButton, 1, 1, 1, 1)

        self.kickButton = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.kickButton.setObjectName("kickButton")

        self.usersGridLayout.addWidget(self.kickButton, 1, 0, 1, 1)

        self.userList = QtWidgets.QListWidget(self.gridLayoutWidget)
        self.userList.setObjectName("userList")

        self.usersGridLayout.addWidget(self.userList, 0, 0, 1, 2)

        self.msgListGroupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.msgListGroupBox.setObjectName("msgListGroupBox")
        self.msgListGroupBox.setGeometry(QtCore.QRect(10, 0, 201, 221))

        self.msgList = QtWidgets.QListWidget(self.msgListGroupBox)
        self.msgList.setObjectName("msgList")
        self.msgList.setGeometry(QtCore.QRect(10, 20, 181, 191))

        item = QtWidgets.QListWidgetItem()
        self.msgList.addItem(item)

        self.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QtCore.QRect(0, 0, 437, 21))
        self.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        self.retranslate_ui()

        # Adding actions to omit when specific events are triggered
        self.kickButton.clicked.connect(self.kick)

        QtCore.QMetaObject.connectSlotsByName(self)

    def show(self):
        host_thread = threading.Thread(target=self.conn_multi)
        host_thread.setDaemon(True)
        host_thread.start()

        super().show()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    server = Server(HOST, PORT)
    server.show()
    sys.exit(app.exec_())
