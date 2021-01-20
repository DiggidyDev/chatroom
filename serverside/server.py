import datetime
import selectors
import socket
import threading
import types
from typing import Union

from PyQt5 import QtCore, QtWidgets

from serverside import query
from serverside.enotify import Emailer
from user import User
from utils import fmt
from utils.cache import Cache
from utils.fmt import update_msg_list

PORT = 65501
HOST = socket.gethostbyname(socket.gethostname())

NULL_BYTE = "\x00"


msg_cache = Cache(max_size=2**15)
room_cache = Cache()
user_cache = Cache()

msg_query = query.MessageQuery(cache=msg_cache)
room_query = query.RoomQuery(cache=room_cache)
user_query = query.UserQuery(cache=user_cache)

msg_query.room_query, msg_query.user_query = room_query, user_query
room_query.msg_query, room_query.user_query = msg_query, user_query
user_query.msg_query, user_query.room_query = msg_query, room_query


class Server(QtWidgets.QMainWindow):

    SCKT_TYPE = Union[int, "HasFileno"]

    def __init__(self, host: str, port: int):
        super().__init__()

        self.conn = (host, port)
        self.clients = []
        self.host = host
        self.mailer: Emailer = Emailer()
        self.port = port
        self.sel = selectors.DefaultSelector()
        self.user = User("Server")

        self.setup_ui()

    def accept_wrapper(self, sock: SCKT_TYPE) -> None:
        # Accept the incoming connection
        conn, addr = sock.accept()
        print(f"Connection successfully made from {':'.join(str(i) for i in addr)}")

        sock.settimeout(0.5)

        data = types.SimpleNamespace(addr=addr, outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events=events, data=data)

    def conn_multi(self) -> None:
        # Create and bind the socket
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind(("", PORT))

        # Listen, use blocking calls
        lsock.listen()
        lsock.settimeout(0.5)

        # Socket registration
        self.sel.register(lsock, selectors.EVENT_READ, data=None)
        while True:

            try:
                events = self.sel.select()
            except Exception as e:
                print(e)
                events = []

            for k, mask in events:

                if not k.data:
                    self.accept_wrapper(k.fileobj)
                else:
                    self.handle_conn(k, mask)

    @staticmethod
    def conn_single() -> None:
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

    def handle_conn(self, key: selectors.SelectorKey, mask: int):
        sock: Union[Server.SCKT_TYPE, socket.socket] = key.fileobj
        data = key.data

        # Incoming data
        if mask & selectors.EVENT_READ:
            recv_bytes = None
            try:
                read_length = ""
                received = None

                while received not in [b"\x00", b""]:
                    received = sock.recv(1)
                    read_length += received.decode("utf-8") if received != b"\x00" else ""

                if read_length != "":
                    recv_bytes = sock.recv(int(read_length))

            except Exception as e:
                print(e)
                print(f"Closing connection with {data.addr}")
                client = self.get_client_by("conn", sock)
                self.userList.takeItem(self.clients.index(client))
                self.sel.unregister(sock)  # No longer monitored by the selector
                sock.close()
                self.clients.remove(client)

                if client['user'] is not None:
                    client['user'].status = 0
                    user_query.update_user_status(client['user'])

                    self.send_message(f"{client['user']} left.")
                    msg = fmt.content(message_content=f"{client['user']} left.",
                                                      user=client['user'],
                                                      system_message=True)
                    update_msg_list(self, msg)
                    msg["content"] = "User left."
                    msg_query.add_message(msg)

                    if client['user'].is_anonymous():
                        client['user'].nickname = "$DELETED_USER"
                        user_query.delete_user(client["user"])

            if recv_bytes:
                recv_content = fmt.decode_bytes(recv_bytes)
                # print(f"RECV: {recv_content['content']} from {user.get_uuid()} - {user.nickname}")
                if recv_content['system_message']:
                    if recv_content['content'] == "Query":
                        self.handle_query(recv_content, sock)

                    elif recv_content['content'] == "Initial connection.":
                        sender: User = recv_content["user"]

                        # Reserve UUID for when initial connection message is received
                        # But fill in other necessary details
                        client_details = {
                            "conn": sock,
                            "user": None
                        }

                        self.clients.append(client_details)
                        item = QtWidgets.QListWidgetItem()
                        item.setText(f"{sender}")
                        self.get_client_by("conn", sock)["user"]: User = sender
                        self.userList.addItem(item)

                        if sender.is_anonymous():
                            user_query.add_user(sender)

                        msg_query.add_message(recv_content)

                        recv_content["userlist"] = [
                            self.userList.item(x).text() for x in range(self.userList.count())
                        ]

                        recv_content["SRV"] = self.user
                        recv_content["rooms"] = user_query.fetch_all_rooms_for(sender)
                        recv_content["messages"] = msg_query.fetch_recent_messages()
                else:
                    msg_query.add_message(recv_content)

                data.outb += fmt.encode_str(recv_content) if "Query" not in recv_content["content"] else b""

        # Outgoing data
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                if isinstance(data.outb, bytes):
                    to_send = fmt.decode_bytes(data.outb)
                else:
                    to_send = data.outb
                sent = self.send_message(to_send)
                print(f"ECHO: {to_send} to {data.addr}")
                print(msg_cache.obj_at("top", room=to_send["room"]).timestamp)
                update_msg_list(self, to_send)
                try:
                    data.outb = data.outb[sent:]  # Remove bytes from send buffer
                except:
                    print("oh no")

    def handle_query(self, recv_content: dict, sock: socket.socket):
        if "get" in recv_content.keys():
            if recv_content["get"] == "user":
                user_tuple = user_query.fetch_user_by(recv_content["datatype"],
                                                      recv_content["data"])
                sock.sendall(fmt.encode_str(user_tuple))
            elif recv_content["get"] == "password":
                pw_hash_tuple = user_query.fetch_pw_hash_by(recv_content["datatype"],
                                                            recv_content["data"])
                sock.sendall(fmt.encode_str(pw_hash_tuple[0]))

        elif "create" in recv_content.keys():
            if recv_content["create"] == "user":
                if isinstance(fmt.decode_bytes(recv_content["data"]), tuple):
                    recv_content["data"] = fmt.decode_bytes(recv_content["data"])
                    email = recv_content["data"][0]

                    email_exists = user_query.does_user_email_exist(email)

                    if email_exists:
                        sock.sendall(fmt.encode_str("email"))
                        return

                    username = recv_content["data"][1]
                    username_available = user_query.is_username_available(username)

                    if not username_available:
                        sock.sendall(fmt.encode_str("username"))
                        return

                    pw = recv_content["data"][2]
                    new_user = User(nickname=username,
                                    registered_user=True)
                    new_user.email = email
                    user_query.add_user(new_user, password=pw)

                    sock.sendall(fmt.encode_str(new_user))

                    self.mailer.send_welcome_email_to(new_user)

    def kick(self):
        current_user = self.userList.currentItem()
        if current_user is not None:
            client = self.get_client_by("name", current_user.text())
            self.send_message("You have been kicked.", client)
            try:
                self.sel.unregister(client["conn"])
                client["conn"].close()
            except Exception as e:
                print(e)
            finally:
                self.clients.remove(client)
                self.userList.takeItem(self.userList.selectedIndexes()[0].row())
                kicked_msg = fmt.content(message_content=f"{client['user']} was kicked.",
                                         user=self.user,
                                         system_message=True)
                self.send_message(kicked_msg)
                update_msg_list(self, kicked_msg)
                print("done")

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("self", "Server", None))
        self.serverInfoGroupBox.setTitle(_translate("self", "Server info", None))
        self.IPLabel.setText(
            _translate("self", f"<html><head/><body><p align=\"center\">IP: {self.host}</p></body></html>", None))
        self.PORTLabel.setText(
            _translate("self", f"<html><head/><body><p align=\"center\">PORT: {self.port}</p></body></html>", None))
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
        sent = 0
        if isinstance(msg, bytes):
            msg = fmt.decode_bytes(msg)
        if isinstance(msg, str):
            msg = fmt.content(message_content=msg,
                              system_message=True,
                              user=self.user)
        if client:
            client["conn"].send((str(len(fmt.encode_str(msg))) + NULL_BYTE).encode("utf-8"))
            sent = client["conn"].send(fmt.encode_str(msg))
        elif not client:
            for c in self.clients:
                c["conn"].send((str(len(fmt.encode_str(msg))) + NULL_BYTE).encode("utf-8"))
                sent = c["conn"].send(fmt.encode_str(msg))
        else:
            print(msg, type(msg))

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

        self.menu_bar = QtWidgets.QMenuBar(self)
        self.menu_bar.setObjectName("menu_bar")
        self.menu_bar.setGeometry(QtCore.QRect(0, 0, 437, 21))
        self.setMenuBar(self.menu_bar)

        self.status_bar = QtWidgets.QStatusBar(self)
        self.status_bar.setObjectName("status_bar")
        self.setStatusBar(self.status_bar)

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
    try:
        import sys

        app = QtWidgets.QApplication(sys.argv)
        server = Server(HOST, PORT)
        server.show()
        sys.exit(app.exec_())
    finally:
        input()
