import hashlib
import socket
import threading
from typing import Iterable, Union

from PyQt5 import QtCore, QtWidgets, QtGui

from clientside import config
from message import Message
from room import Room
from ui.info import CustomDialog
from ui.items import MessageWidgetItem
from ui.menu import ThemeAction
from ui.rooms import RoomDropdown
from ui.themes import ThemeUpdater
from user import User
from utils import fmt, update
from utils.cache import Cache

HOST = "18.217.109.81"  # AWS hosting the server
PORT = 65501  # Server listening to connections on this port

NULL_BYTE = "\x00"

style = ThemeUpdater()


class Client(QtWidgets.QMainWindow):
    """
    The main client interface with which the
    user will be interacting.
    """

    # Typehints, as proposed by:
    # PEP-483
    # PEP-484
    # PEP-526

    ERRS: Union[str, None]
    HOST: str
    PORT: int
    SRV_UUID: str

    conn_thread: threading.Thread
    current_font: QtGui.QFont
    default_font: QtGui.QFont
    kicked: bool
    login: "LoginDialog"
    msgs_received: threading.Event
    stop_event: threading.Event
    user: Union[User, None]

    _socket: Union[socket.socket, None]

    def __init__(self, host, port):
        super().__init__()

        self.ADDRESS = (host, port)
        self.PORT = port
        self.HOST = host
        self.ERRS = None

        self.check_for_updates = False

        self.current_font = QtGui.QFont()
        self.current_font.setFamily("Microsoft New Tai Lue")
        self.default_font = QtGui.QFont()
        self.default_font.setFamily("Microsoft New Tai Lue")

        self.current_room = None
        self.email = None
        self.kicked = False
        self.most_recent_message: Message
        self.msgs_received = threading.Event()
        self.user = None

        self._current_room: Union[Room, None]
        self._msg_cache = Cache(max_size=2 ** 10)
        self._socket = None

    def __recursive_font_change(self, parent: Union[
        QtWidgets.QMenu, QtCore.QObject]) -> None:
        if hasattr(parent, "children"):
            for child in parent.children():
                self.__recursive_font_change(child)
        if hasattr(parent, "actions"):
            for action in parent.actions():
                if action != self.toggleCoolMode:
                    action.setFont(self.current_font)

    @staticmethod
    def _send(sock: socket.socket, data: Union[Message, dict]) -> None:
        if isinstance(data, Message):
            print(f"{data!r}")
            encoded = bytes(data)
        elif isinstance(data, dict):
            msg = fmt.do_friendly_conversion_to(Message, data)
            print(f"{msg!r}")
            encoded = bytes(msg)
        try:
            sock.sendall((str(len(encoded)) + NULL_BYTE).encode("utf-8"))
            sock.sendall(encoded)
        except Exception as e:
            print("Exception whilst sending message:", e)

    def __set_up_rooms(self, rooms: Iterable[Room]):
        # TODO: LOAD LAST ROOM FROM config.ini?!

        self.current_room = rooms[0]
        self.chatroomComboBox.add_rooms(*rooms)

    def toggle_alternate_row_colours(self):
        """
        For a11y and easy differentiation of messages.

        :return:
        """
        self.msgList.setAlternatingRowColors(not self.msgList.alternatingRowColors())
        self.userList.setAlternatingRowColors(not self.userList.alternatingRowColors())

    def toggle_comic_sans(self) -> None:
        """
        [CHANGE ALL WIDGETS' FONTS]

        :return: None
        """
        if self.toggleCoolMode.isChecked():
            self.chatroomComboBox.setStyleSheet(
                self.chatroomComboBox.styleSheet() \
                    .replace(f"font-family: \"{self.current_font.family()}\"",
                             "font-family: \"Comic Sans MS\"")
            )
            self.current_font.setFamily("Comic Sans MS")
        else:
            self.chatroomComboBox.setStyleSheet(
                self.chatroomComboBox.styleSheet() \
                    .replace(f"font-family: \"{self.current_font.family()}\"",
                             f"font-family: \"{self.default_font.family()}\"")
            )
            self.current_font.setFamily(self.default_font.family())

        for child in self.menubar.children():
            self.__recursive_font_change(child)

        for message in [self.msgList.item(i) for i in
                        range(self.msgList.count())]:
            message.setFont(self.current_font)

        for user in [self.userList.item(i) for i in
                     range(self.userList.count())]:
            user.setFont(self.current_font)

        # FIX COMBOBOX VIEW
        # p = self.chatroomComboBox.palette()
        # p.setFont(self.current_font)

    def toggle_user_list(self):
        self.usersGroupBox.setVisible(not self.toggleUserList.isChecked())
        if not self.toggleUserList.isChecked():
            self.chatroomSizePolicy.setVerticalPolicy(
                QtWidgets.QSizePolicy.Fixed)
            self.chatroomGroupBox.setSizePolicy(self.chatroomSizePolicy)
        else:
            self.chatroomSizePolicy.setVerticalPolicy(
                QtWidgets.QSizePolicy.Expanding)
            self.chatroomGroupBox.setSizePolicy(self.chatroomSizePolicy)

    def toggle_user_buttons(self):
        self.friendButton.setVisible(
            not self.toggleUserActionButtons.isChecked())
        self.muteButton.setVisible(
            not self.toggleUserActionButtons.isChecked())

    def check_password(self, password: str, salt: str) -> bool:
        """
        Compares the server-side hashed password and the hash for
        the password the user just entered.

        :param password: The user's input.
        :param salt: The UUID of the user.
        :return: A boolean indicating whether the hashes match.
        """

        attempted_pw_hash = hashlib.pbkdf2_hmac("sha256",
                                                password.encode("utf-8"),
                                                salt.encode("utf-8"), 200000)

        pw_q = {
            "content"       : "Query",
            "system_message": True,
            "data"          : self.email,
            "datatype"      : "email",
            "get"           : "password"
        }

        self._send(self._socket, pw_q)

        pw_hash = fmt.decode_bytes(self._socket.recv(4096))

        return attempted_pw_hash.hex() == pw_hash

    def check_fields(self) -> bool:
        if len(self.login.inputUsername.text().strip()) == 0 and \
                self.login.inputUsername.isVisible():
            errdialog = CustomDialog(window_title="Username",
                                     message="Please enter your username",
                                     font=self.default_font)
        elif len(self.login.inputEmail.text().strip()) == 0:
            errdialog = CustomDialog(window_title="Email",
                                     message="Please enter your email",
                                     font=self.default_font)
        elif not fmt.is_valid_email(self.login.inputEmail.text()):
            errdialog = CustomDialog(window_title="Email",
                                     message="Please enter a valid email address",
                                     font=self.default_font)
        elif len(self.login.inputPassword.text().strip()) == 0:
            errdialog = CustomDialog(window_title="Password",
                                     message="Please enter your password",
                                     font=self.default_font)
        else:
            return True

        errdialog.exec_()

        return False

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.stop_event.set()
        super().closeEvent(event)

    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if self._socket:
                self._socket.close()
            s.connect((self.HOST, self.PORT))
            self._socket = s

            initial_content = {
                "content"       : "Initial connection.",
                "system_message": True,
                "user"          : self.user
            }

            self._send(self._socket, initial_content)

            while not self.stop_event.is_set():
                read_length = ""
                recv_data = None

                while recv_data not in [b"\x00", b""]:
                    recv_data = s.recv(1)
                    read_length += recv_data.decode("utf-8") if recv_data != b"\x00" else ""

                if read_length != "":
                    recv_data = s.recv(int(read_length))

                if recv_data:
                    data = fmt.decode_bytes(recv_data)
                    if isinstance(data, bytes):
                        data = fmt.decode_bytes(data)
                    print(f"RECV: {data}")
                    if isinstance(data, dict):
                        messages = data.pop("messages", None)

                        if data["system_message"]:
                            content = data.pop("content", None)
                            rooms: [] = data.pop("rooms", [])
                            srv_user = data.pop("SRV", None)

                            if srv_user:
                                self.SRV_UUID = srv_user.uuid

                            if content == "You have been kicked.":
                                # Modify kicked flag for showing kicked dialog on
                                # connection abortion
                                self.kicked = True
                                self.stop_event.set()
                                self._socket.close()
                                self.close()  # Close the current window

                            if messages is not False:
                                pos = "top"

                                if messages[0] in {"top", "bottom"}:
                                    pos = messages[0]
                                    messages = messages[1:]

                                fmt.update_msg_list(self, messages,
                                                    cache=self._msg_cache,
                                                    pos=pos)

                                # Set a thread-safe flag's state
                                # based on whether messages were
                                # received
                                if not self.msgs_received.is_set():
                                    self.msgs_received.set()

                            else:
                                self.msgs_received.clear()

                            if not self._msg_cache.is_ready:
                                self._msg_cache.is_ready = True

                            if rooms:
                                self.__set_up_rooms(rooms)

                                for r in rooms:
                                    try:
                                        r.most_recent_message = list(self._msg_cache[r])[0][1]
                                    except IndexError:
                                        print("No messages yet")

                            if "content" in data.keys() and data["content"] == "Initial connection." or \
                                    "userlist" in data.keys():
                                fmt.update_user_list(self, data)

                        if "content" in data.keys():
                            fmt.update_msg_list(self, data,
                                                cache=self._msg_cache)

                            if str(data["user"].uuid) != self.SRV_UUID:
                                msg = fmt.do_friendly_conversion_to(Message,
                                                                    data)

                                self.update_recent_message(msg)

    def create_anon_user(self):
        if self.login.buttonAnon.hasFocus() or self.login.inputNickname.hasFocus():
            try:
                fmt.is_valid_anon_username(
                    self.login.inputNickname.text().strip())
                if len(self.login.inputNickname.text().strip()) > 0:
                    self.user = User(f"[ANON] {self.login.inputNickname.text().strip()}")
                    print(self.user.uuid)
                    self.login.close()

                    return
                elif len(self.login.inputNickname.text().strip()) == 0:
                    errdialog = CustomDialog(window_title="Error",
                                             message="Please enter a nickname",
                                             font=self.default_font)
                    errdialog.exec_()

            except NameError as e:
                errdialog = CustomDialog(window_title=f"{type(e)}",
                                         message=f"{e}",
                                         font=self.default_font)
                errdialog.exec_()

    @property
    def current_room(self) -> Room:
        return self._current_room

    @current_room.setter
    def current_room(self, room: Room):
        self._current_room = room

    def do_account_setup(self):
        self.login = LoginDialog()
        self.login.buttonAnon.clicked.connect(self.create_anon_user)
        self.login.buttonLoginRegister.clicked.connect(self.inspect_button)
        self.login.toggleExistingAcc.toggled.connect(
            self.login.display_username_input)
        self.login.toggleExistingAcc.toggled.connect(
            self.login.toggle_register_button)
        self.login.inputNickname.textEdited.connect(
            self.login.disable_account_inputs)

        for i in {self.login.inputEmail,
                  self.login.inputPassword,
                  self.login.inputUsername}:
            i.textEdited.connect(self.login.disable_anon_input)
            i.returnPressed.connect(self.inspect_button)

        return self.login.exec_()

    def do_login(self):
        if self.check_fields():
            self.email = self.login.inputEmail.text()

            def _do_user_login(_client: Client):
                if not _client._socket:
                    _client._socket = socket.socket(socket.AF_INET,
                                                    socket.SOCK_STREAM)
                    _client._socket.connect((_client.HOST, _client.PORT))

                email_q = {
                    "content"       : "Query",
                    "system_message": True,
                    "get"           : "user",
                    "data"          : _client.email,
                    "datatype"      : "email"
                }

                _client._send(_client._socket, email_q)
                user = fmt.decode_bytes(_client._socket.recv(4096))

                if user is not None:
                    pw = _client.login.inputPassword.text()

                    if _client.check_password(pw, str(user.uuid)):
                        _client.user = user
                    else:
                        _client.email = None
                        _client.ERRS = "password"
                else:
                    _client.email = None
                    _client.ERRS = "username"

            c_thread = threading.Thread(target=_do_user_login,
                                        args=[self])
            c_thread.setDaemon(True)
            c_thread.start()
            c_thread.join()

    def do_registration(self):
        if self.check_fields():
            self.email = self.login.inputEmail.text()

            def _register_user(_client: Client):
                """
                Set up a connection with the server to query
                a user account's existence, dependant on
                an email being found in the database.

                If an email is found, an error window will be
                shown; "user already exists".

                :param _client: The QMainWindow instance.
                :return:
                """
                if not _client._socket:
                    _client._socket = socket.socket(socket.AF_INET,
                                                    socket.SOCK_STREAM)
                    _client._socket.connect((_client.HOST, _client.PORT))

                existing_user_q = {
                    "content"       : "Query",
                    "system_message": True,
                    "get"           : "user",
                    "data"          : _client.email,
                    "datatype"      : "email"
                }

                _client._send(_client._socket, existing_user_q)
                email_was_found = fmt.decode_bytes(_client._socket.recv(4096))

                if email_was_found == "":
                    _client.email = None
                else:
                    pw = _client.login.inputPassword.text()
                    username = _client.login.inputUsername.text()

                    register_user_q = {
                        "content"       : "Query",
                        "system_message": True,
                        "create"        : "user",
                        "data"          : fmt.encode_str(
                            (_client.email, username, pw)),
                        "datatype"      : "email, username, pw"
                    }

                    _client._send(_client._socket, register_user_q)
                    registered_user = fmt.decode_bytes(
                        _client._socket.recv(4096))

                    if registered_user in {"email", "username"}:
                        _client.ERRS = registered_user
                        _client.email = None
                    else:
                        _client.user = registered_user

            c_thread = threading.Thread(target=_register_user,
                                        args=[self])
            # Check for valid ascii characters
            c_thread.start()
            c_thread.join()

    def inspect_button(self):
        errdialog: Union[None, CustomDialog] = None

        if self.login.buttonLoginRegister.text() == "Log in":
            self.do_login()
            if self.ERRS == "password":
                errdialog = CustomDialog(window_title="Login Failed",
                                         message="Incorrect password",
                                         font=self.default_font)
            elif self.ERRS == "username":
                errdialog = CustomDialog(window_title="Login Failed",
                                         message="Account with that email not found",
                                         font=self.default_font)
        else:
            try:
                fmt.is_valid_username(self.login.inputUsername.text().strip())
            except NameError as e:
                errdialog = CustomDialog(window_title=f"{type(e)}",
                                         message=f"{e}",
                                         font=self.default_font)
                errdialog.exec_()
                return

            self.do_registration()
            if self.ERRS in {"email", "username"}:
                errdialog = CustomDialog(window_title="Registration Failed",
                                         message=f"An account with that "
                                                 f"{self.ERRS} already exists.",
                                         font=self.default_font)
        if self.ERRS and errdialog:
            errdialog.exec_()
            self.ERRS = None
        if self.login_successful():
            self._socket.close()
            self.login.close()

    def load_unload_messages(self, x):
        if not self._msg_cache.is_ready:
            return

        if x <= 2:
            for i in range(3):
                top_msg = self.msgList.item(0)
                print(top_msg.uuid == self._msg_cache.obj_at("top", room=self.current_room).uuid)
                if top_msg.uuid == self._msg_cache.obj_at("top",
                                                          room=self.current_room).uuid:

                    msg_query = {
                        "content"       : "Query",
                        "data"          : (100,
                                           self.current_room,
                                           self._msg_cache.get(top_msg.uuid),
                                           "above"),
                        "get"           : "messages",
                        "system_message": True
                    }

                    try:
                        self._send(self._socket, msg_query)

                        if self.msgs_received.wait(0.1):
                            self.msgList.verticalScrollBar().setSliderPosition(3)
                        else:
                            break

                    except Exception as e:
                        break
                else:
                    try:
                        next_msg = self._msg_cache.next_obj(relative="above",
                                                            target=top_msg.uuid,
                                                            room=self.current_room)
                        fmt.update_msg_list(self, dict(next_msg),
                                            cache=self._msg_cache, pos="top")
                        self.msgList.verticalScrollBar().setSliderPosition(3)
                    except Exception as e:
                        print("a")
                        print(e)

        elif x >= self.msgList.verticalScrollBar().maximum() - 2:
            for i in range(3):
                
                bottom_msg = self.msgList.item(self.msgList.count() - 1)

                if self._msg_cache.obj_at("bottom", room=self.current_room).uuid == bottom_msg.uuid:
                    msg_query = {
                        "content"       : "Query",
                        "data"          : (100,
                                           self.current_room,
                                           bottom_msg.uuid,
                                           "below"),
                        "get"           : "messages",
                        "system_message": True
                    }
                    self._send(self._socket, msg_query)

                    if self.msgs_received.wait(0.1) and len(self._msg_cache) > 200:
                        self.msgList.verticalScrollBar().setSliderPosition(self.msgList.verticalScrollBar().maximum() - 3)
                    else:
                        break
                else:
                    try:
                        next_msg = self._msg_cache.next_obj(
                            relative="below",
                            target=bottom_msg.uuid,
                            room=self.current_room)

                        fmt.update_msg_list(self, dict(next_msg),
                                            cache=self._msg_cache)
                        self.msgList.verticalScrollBar().setSliderPosition(self.msgList.verticalScrollBar().maximum() - 3)
                    except Exception as e:
                        print(type(e), e)

    def login_successful(self) -> bool:
        """
        Detects whether a user's account has been found
        (anonymous and registered users), or whether an
        email has been found (registered users).

        :return: A boolean indicating the current login status.
        """
        return any(condition is not None for condition in {
            self.email,
            self.user
        })

    def on_key(self) -> None:
        """
        Resets the message box when a message
        has been sent, signalling to the user
        that it's been dealt with.

        :return:
        """
        msg = self.sendMsgBox.toPlainText()

        if self.sendMsgBox.hasFocus() and \
                msg.strip() != "":
            self.send_message(msg)
            self.sendMsgBox.setPlainText("")

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate

        self.setWindowTitle(_translate("self", "Client"))
        self.usersGroupBox.setTitle(_translate("self", "Users"))
        self.muteButton.setText(_translate("self", "Mute"))
        self.friendButton.setText(_translate("self", "Add friend"))
        self.userList.setSortingEnabled(False)

        self.chatroomGroupBox.setTitle(_translate("self", "Chatroom"))
        self.pushButton.setText(_translate("self", "Leave"))
        self.msgListGroupBox.setTitle(_translate("self", "Messages"))

        self.msgList.setSortingEnabled(False)
        self.sendMsgBox.setPlaceholderText(
            _translate("self", "Send a message..."))

        self.menuView.setTitle(_translate("self", "&View"))
        self.menuHelp.setTitle(_translate("self", "&Help"))

        if not self.user.is_anonymous():
            self.menuFriends.setTitle(_translate("self", "&Friends"))
            self.menuProfile.setTitle(_translate("self", "&Profile"))

            # INFO: FRIENDS MENU
            self.addFriend.setText(_translate("self", "Add friend"))
            self.removeFriend.setText(_translate("self", "Remove friend"))
            self.blockFriend.setText(_translate("self", "Block user"))
            self.viewFriends.setText(_translate("self", "View friends"))

            # INFO: PROFILE MENU
            self.editName.setText(_translate("self", "Edit name"))
            self.editStatus.setText(_translate("self", "Change status"))

        # INFO: VIEW MENU
        self.toggleExplicitLanguageFilter.setText(
            _translate("self", "Toggle Explicit Language Filter"))
        self.toggleUserActionButtons.setText(
            _translate("self", "Toggle User Action Buttons"))
        self.toggleUserList.setText(_translate("self", "Toggle User List"))
        self.toggleAlternateRowColours.setText(
            _translate("self", "Toggle Alternating row colours"))
        self.toggleCoolMode.setText(_translate("self", "Cool mode"))
        self.editFontSize.setText(_translate("self", "Edit font size"))
        self.menuThemes.setTitle(_translate("self", "Themes..."))

        # INFO: THEME SUB-MENU
        for theme in self.menuThemes.actions():
            theme.setText(_translate("self", theme.objectName()))
        self.createTheme.setText(_translate("self", "Create theme..."))

        # INFO: HELP MENU
        self.leave.setText(_translate("self", "Leave"))
        self.FAQ.setText(_translate("self", "FAQ"))
        self.reportABug.setText(_translate("self", "Report a bug"))
        self.aboutChatroom.setText(_translate("self", "About Chatroom"))

    def setup_ui(self):
        from clientside.actionslots import HelpSlots, FriendsSlots, ViewSlots

        self.setObjectName("self")
        self.resize(578, 363)

        # sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        # self.setSizePolicy(sizePolicy)

        self.centralwidget = QtWidgets.QWidget(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(
            self.centralwidget.sizePolicy().hasHeightForWidth())

        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setSizeIncrement(QtCore.QSize(1, 1))
        self.centralwidget.setMouseTracking(False)

        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.usersGroupBox = QtWidgets.QGroupBox(self.centralwidget)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.usersGroupBox.sizePolicy().hasHeightForWidth())

        self.usersGroupBox.setSizePolicy(sizePolicy)
        self.usersGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.usersGroupBox.setCheckable(False)
        self.usersGroupBox.setObjectName("usersGroupBox")

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.usersGroupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.usersGridLayout = QtWidgets.QGridLayout()
        self.usersGridLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.usersGridLayout.setObjectName("usersGridLayout")
        self.muteButton = QtWidgets.QPushButton(self.usersGroupBox)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.muteButton.sizePolicy().hasHeightForWidth())

        self.muteButton.setSizePolicy(sizePolicy)
        self.muteButton.setCheckable(True)
        self.muteButton.setObjectName("muteButton")
        self.usersGridLayout.addWidget(self.muteButton, 1, 1, 1, 1)
        self.friendButton = QtWidgets.QPushButton(self.usersGroupBox)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.friendButton.sizePolicy().hasHeightForWidth())

        self.friendButton.setSizePolicy(sizePolicy)
        self.friendButton.setCheckable(False)
        self.friendButton.setDefault(False)
        self.friendButton.setFlat(False)
        self.friendButton.setObjectName("friendButton")
        self.usersGridLayout.addWidget(self.friendButton, 1, 0, 1, 1)

        self.userList = ListWidget(self.usersGroupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.userList.sizePolicy().hasHeightForWidth())
        self.userList.setSizePolicy(sizePolicy)
        self.userList.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        self.userList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.userList.setTabKeyNavigation(False)
        self.userList.setObjectName("userList")
        self.usersGridLayout.addWidget(self.userList, 0, 0, 1, 2)
        self.horizontalLayout.addLayout(self.usersGridLayout)
        self.gridLayout.addWidget(self.usersGroupBox, 0, 1, 1, 1)
        self.chatroomGroupBox = QtWidgets.QGroupBox(self.centralwidget)

        self.chatroomSizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.chatroomSizePolicy.setHorizontalStretch(1)
        self.chatroomSizePolicy.setVerticalStretch(1)
        self.chatroomSizePolicy.setHeightForWidth(
            self.chatroomGroupBox.sizePolicy().hasHeightForWidth())

        self.chatroomGroupBox.setSizePolicy(self.chatroomSizePolicy)
        self.chatroomGroupBox.setSizeIncrement(QtCore.QSize(1, 1))
        self.chatroomGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.chatroomGroupBox.setObjectName("chatroomGroupBox")

        self.gridLayout_4 = QtWidgets.QGridLayout(self.chatroomGroupBox)
        self.gridLayout_4.setObjectName("gridLayout_4")

        self.chatroomComboBox = RoomDropdown(self.chatroomGroupBox, anonymous=self.user.is_anonymous())
        #self.chatroomComboBox.setAutoFillBackground(False)

        #self.chatroomComboBox.setEditable(False)
        #self.chatroomComboBox.setFrame(True)
        self.chatroomComboBox.setObjectName("chatroomComboBox")

        self.gridLayout_4.addWidget(self.chatroomComboBox, 0, 0, 1, 1)
        self.pushButton = QtWidgets.QPushButton(self.chatroomGroupBox)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout_4.addWidget(self.pushButton, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.chatroomGroupBox, 1, 1, 1, 1)
        self.msgListGroupBox = QtWidgets.QGroupBox(self.centralwidget)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.msgListGroupBox.sizePolicy().hasHeightForWidth())

        self.msgListGroupBox.setSizePolicy(sizePolicy)
        self.msgListGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.msgListGroupBox.setObjectName("msgListGroupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.msgListGroupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")

        self.msgList = ListWidget(self.msgListGroupBox, cache=self._msg_cache)
        self.msgList.setWrapping(True)
        self.msgList.setWordWrap(True)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.msgList.sizePolicy().hasHeightForWidth())

        self.msgList.setSizePolicy(sizePolicy)
        self.msgList.setAutoFillBackground(False)

        self.msgList.setLineWidth(0)
        self.msgList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.msgList.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        self.msgList.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.msgList.setMovement(QtWidgets.QListView.Static)
        self.msgList.setProperty("isWrapping", False)
        self.msgList.setResizeMode(QtWidgets.QListView.Adjust)
        self.msgList.setViewMode(QtWidgets.QListView.ListMode)
        self.msgList.setObjectName("msgList")

        # INFO: EVENT TRIGGERS FOR MESSAGES
        self.msgList.model().rowsInserted.connect(self.msgList.scrollToBottom)
        self.msgList.verticalScrollBar().valueChanged.connect(
            lambda x=self: self.load_unload_messages(x))

        # TODO: ADDING MESSAGES TO THE LIST \/
        item = QtWidgets.QListWidgetItem()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setBackground(brush)
        item.setFlags(QtCore.Qt.ItemIsSelectable)
        item.setFlags(QtCore.Qt.ItemIsDragEnabled)

        self.gridLayout_2.addWidget(self.msgList, 0, 0, 1, 1)
        self.sendMsgBox = MessageBox(self, self.msgListGroupBox)
        self.sendMsgBox.setEnabled(True)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.sendMsgBox.sizePolicy().hasHeightForWidth())

        self.sendMsgBox.setSizePolicy(sizePolicy)
        self.sendMsgBox.setMaximumSize(QtCore.QSize(16777215, 50))

        self.sendMsgBox.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.sendMsgBox.setFrameShadow(QtWidgets.QFrame.Plain)
        self.sendMsgBox.setLineWidth(0)
        self.sendMsgBox.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.sendMsgBox.setTabChangesFocus(True)
        self.sendMsgBox.setDocumentTitle("")
        self.sendMsgBox.setBackgroundVisible(True)
        self.sendMsgBox.setCenterOnScroll(True)
        self.sendMsgBox.setObjectName("sendMsgBox")
        self.gridLayout_2.addWidget(self.sendMsgBox, 1, 0, 1, 1)

        self.gridLayout.addWidget(self.msgListGroupBox, 0, 0, 2, 1)
        self.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 578, 23))
        self.menubar.setDefaultUp(False)
        self.menubar.setNativeMenuBar(True)
        self.menubar.setObjectName("menu_bar")

        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setAutoFillBackground(False)
        self.menuView.setTearOffEnabled(False)
        self.menuView.setSeparatorsCollapsible(True)
        self.menuView.setObjectName("menuView")
        self.menuThemes = QtWidgets.QMenu(self.menuView)
        self.menuThemes.setObjectName("menuThemes")
        self.menuFriends = QtWidgets.QMenu(self.menubar)
        self.menuFriends.setObjectName("menuFriends")
        self.menuProfile = QtWidgets.QMenu(self.menubar)
        self.menuProfile.setObjectName("menuProfile")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.setMenuBar(self.menubar)

        self.toggleUserList = QtWidgets.QAction(self)
        self.toggleUserList.setCheckable(True)
        self.toggleUserList.setObjectName("toggleUserList")
        self.toggleUserList.triggered.connect(
            lambda x: ViewSlots.toggle_user_list(self))

        self.toggleUserActionButtons = QtWidgets.QAction(self)
        self.toggleUserActionButtons.setCheckable(True)
        self.toggleUserActionButtons.setObjectName("toggleUserActionButtons")
        self.toggleUserActionButtons.triggered.connect(
            lambda x: ViewSlots.toggle_user_action_buttons(self))

        self.toggleAlternateRowColours = QtWidgets.QAction(self)
        self.toggleAlternateRowColours.setCheckable(True)
        self.toggleAlternateRowColours.triggered.connect(
            lambda x: ViewSlots.toggle_alternate_row_colours(self))

        self.toggleCoolMode = QtWidgets.QAction(self)
        self.toggleCoolMode.setCheckable(True)
        self.toggleCoolMode.triggered.connect(
            lambda x: ViewSlots.change_fonts(self))

        font = QtGui.QFont()
        font.setFamily("Comic Sans MS")

        self.toggleCoolMode.setFont(font)
        self.toggleCoolMode.setObjectName("toggleCoolMode")

        self.createTheme = QtWidgets.QAction(self)
        self.createTheme.setObjectName("createTheme")
        self.createTheme.triggered.connect(
            lambda x: ViewSlots.create_theme(self))

        self.addFriend = QtWidgets.QAction(self)
        self.addFriend.setObjectName("addFriend")

        self.editName = QtWidgets.QAction(self)
        self.editName.setObjectName("editName")

        self.editStatus = QtWidgets.QAction(self)
        self.editStatus.setObjectName("editStatus")

        self.removeFriend = QtWidgets.QAction(self)
        self.removeFriend.setObjectName("removeFriend")

        self.blockFriend = QtWidgets.QAction(self)
        self.blockFriend.setObjectName("blockFriend")

        self.viewFriends = QtWidgets.QAction(self)
        self.viewFriends.setObjectName("viewFriends")
        self.viewFriends.triggered.connect(
            lambda: FriendsSlots.view_friends(self))

        self.editFontSize = QtWidgets.QAction(self)
        self.editFontSize.setObjectName("editFontSize")

        self.leave = QtWidgets.QAction(self)
        self.leave.setObjectName("leave")

        self.FAQ = QtWidgets.QAction(self)
        self.FAQ.setObjectName("FAQ")
        self.FAQ.triggered.connect(lambda x=self: HelpSlots.faq(self))

        self.reportABug = QtWidgets.QAction(self)
        self.reportABug.setObjectName("reportABug")
        self.reportABug.triggered.connect(HelpSlots.report_a_bug)

        self.toggleExplicitLanguageFilter = QtWidgets.QAction(self)
        self.toggleExplicitLanguageFilter.setCheckable(True)
        self.toggleExplicitLanguageFilter.setObjectName(
            "toggleExplicitLanguageFilter")

        self.aboutChatroom = QtWidgets.QAction(self)
        self.aboutChatroom.setObjectName("aboutChatroom")
        self.aboutChatroom.triggered.connect(lambda x=self: HelpSlots.about_chatroom(self))

        for theme in config.get_theme_names():
            action = ThemeAction(self)
            action.setObjectName(theme[6:])
            action.setText(theme[6:])
            action.setup_trigger()
            self.menuThemes.addAction(action)

        self.menuThemes.addSeparator()
        self.menuThemes.addAction(self.createTheme)

        self.menuView.addAction(self.toggleAlternateRowColours)
        self.menuView.addAction(self.toggleExplicitLanguageFilter)
        self.menuView.addAction(self.toggleUserActionButtons)
        self.menuView.addAction(self.toggleUserList)
        self.menuView.addSeparator()
        self.menuView.addAction(self.toggleCoolMode)
        self.menuView.addAction(self.editFontSize)
        self.menuView.addAction(self.menuThemes.menuAction())

        self.menuFriends.addAction(self.addFriend)
        self.menuFriends.addAction(self.removeFriend)
        self.menuFriends.addAction(self.blockFriend)
        self.menuFriends.addSeparator()
        self.menuFriends.addAction(self.viewFriends)

        self.menuProfile.addAction(self.editName)
        self.menuProfile.addAction(self.editStatus)

        self.menuHelp.addAction(self.FAQ)
        self.menuHelp.addAction(self.reportABug)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.aboutChatroom)

        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuFriends.menuAction())
        self.menubar.addAction(self.menuProfile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslate_ui()
        QtCore.QMetaObject.connectSlotsByName(self)

        self.setTabOrder(self.msgList, self.sendMsgBox)
        self.setTabOrder(self.sendMsgBox, self.userList)
        self.setTabOrder(self.userList, self.friendButton)
        self.setTabOrder(self.friendButton, self.muteButton)
        self.setTabOrder(self.muteButton, self.chatroomComboBox)
        self.setTabOrder(self.chatroomComboBox, self.pushButton)

        style.to_current_theme(self)

    def send_message(self, content):
        msg = Message(content=content, room=self.current_room,
                      user=self.user, system_message=False)

        self._msg_cache.cache_to("bottom", msg)
        self.update_recent_message(msg)
        self._send(self._socket, msg)

    def show(self):
        """
        Overriding the default show method from QMainWindow
        for some prerequisite checks
        :return:
        """
        ret_code = 1

        if self.check_for_updates and update.is_update_available(show_window=True):
            from utils.update import start_download

            start_download()

        if not self.check_for_updates or not update.is_update_available():
            ret_code = self.do_account_setup()

        if self.login_successful():
            self.setup_ui()

            self.stop_event = threading.Event()
            self.conn_thread = threading.Thread(target=self.connect)

            # Allows main thread to exit when
            # only daemon threads are left
            self.conn_thread.setDaemon(True)
            self.conn_thread.start()

            super().showMaximized()
        else:
            # Handles the user closing the login dialog
            sys.exit(ret_code)

    def update_recent_message(self, message: Message):
        """
        Get the room that the message belongs to,
        updating its most recent message, so then
        the client knows where to stop scrolling
        when switching rooms.

        :param message:
        :return:
        """

        if message.room.uuid == self.current_room.uuid:
            self.current_room.most_recent_message = message
            return

        try:
            for r in self.user.rooms:
                if r.uuid == message.room.uuid:
                    r.most_recent_message = message
        except Exception as e:
            print(f"[[ ERROR ]] :: Unable to update recent message :: {e}")


class LoginDialog(QtWidgets.QDialog):
    """
    First dialog to prompt user to either continue without
    an account, or to register to create a new one, or log
    in with an existing account.

    The chatroom(s) won't be accessible until a successful
    login is detected.
    """

    def __init__(self):
        super().__init__()
        self.setup_ui()
        style.to_current_theme(self)

    def disable_account_inputs(self):
        if len(self.inputNickname.text()) > 0 and self.inputUsername.isEnabled():
            self.inputUsername.setEnabled(False)
            self.inputPassword.setEnabled(False)
            self.inputEmail.setEnabled(False)
            self.buttonLoginRegister.setEnabled(False)

        elif len(self.inputNickname.text()) == 0 and not self.inputUsername.isEnabled():
            self.inputUsername.setEnabled(True)
            self.inputPassword.setEnabled(True)
            self.inputEmail.setEnabled(True)
            self.buttonLoginRegister.setEnabled(True)

    def disable_anon_input(self):
        total_length = len(self.inputEmail.text() +
                           self.inputPassword.text() +
                           self.inputUsername.text())
        if total_length > 0 and self.inputNickname.isEnabled():
            self.inputNickname.setEnabled(False)
            self.buttonAnon.setEnabled(False)
        elif total_length == 0:
            self.inputNickname.setEnabled(True)
            self.buttonAnon.setEnabled(True)

    def display_username_input(self):
        self.inputUsername.setVisible(not self.inputUsername.isVisible())

    def setup_ui(self):
        self.setObjectName("self")

        self.resize(461, 238)
        self.setMinimumSize(QtCore.QSize(461, 238))
        self.setMaximumSize(QtCore.QSize(461, 238))

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonAnon = QtWidgets.QPushButton(self)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.buttonAnon.sizePolicy().hasHeightForWidth())

        self.buttonAnon.setSizePolicy(sizePolicy)
        self.buttonAnon.setObjectName("buttonAnon")
        self.gridLayout.addWidget(self.buttonAnon, 6, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 19,
                                           QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Preferred)
        self.gridLayout.addItem(spacerItem, 5, 0, 1, 1)

        self.inputNickname = QtWidgets.QLineEdit(self)
        self.inputNickname.setEnabled(True)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.inputNickname.sizePolicy().hasHeightForWidth())

        self.inputNickname.setSizePolicy(sizePolicy)
        self.inputNickname.setText("")
        self.inputNickname.setObjectName("inputNickname")
        self.inputNickname.setMaxLength(10)

        self.gridLayout.addWidget(self.inputNickname, 6, 0, 1, 1)
        self.labelContAnon = QtWidgets.QLabel(self)
        self.labelContAnon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelContAnon.setObjectName("labelContAnon")
        self.gridLayout.addWidget(self.labelContAnon, 2, 0, 1, 2)
        self.buttonLoginRegister = QtWidgets.QPushButton(self)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.buttonLoginRegister.sizePolicy().hasHeightForWidth())

        self.buttonLoginRegister.setSizePolicy(sizePolicy)
        self.buttonLoginRegister.setObjectName("buttonLoginRegister")
        self.gridLayout.addWidget(self.buttonLoginRegister, 7, 5, 1, 1)

        self.inputEmail = QtWidgets.QLineEdit()
        self.inputEmail.setObjectName("inputEmail")
        self.inputEmail.setPlaceholderText("Email")
        self.gridLayout.addWidget(self.inputEmail, 6, 4, 1, 2)

        self.inputUsername = QtWidgets.QLineEdit(self)
        self.inputUsername.setObjectName("inputUsername")
        self.inputUsername.setMaxLength(24)
        self.gridLayout.addWidget(self.inputUsername, 5, 4, 1, 2)
        self.inputPassword = QtWidgets.QLineEdit(self)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.inputPassword.sizePolicy().hasHeightForWidth())

        self.inputPassword.setSizePolicy(sizePolicy)
        self.inputPassword.setFrame(True)
        self.inputPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.inputPassword.setObjectName("inputPassword")

        self.gridLayout.addWidget(self.inputPassword, 7, 4, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40,
                                            QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 8, 0, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40,
                                            QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Preferred)
        self.gridLayout.addItem(spacerItem2, 0, 1, 1, 1)
        self.verticalDivider = QtWidgets.QFrame(self)
        self.verticalDivider.setFrameShape(QtWidgets.QFrame.VLine)
        self.verticalDivider.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalDivider.setObjectName("verticalDivider")
        self.gridLayout.addWidget(self.verticalDivider, 0, 2, 9, 1)
        self.toggleExistingAcc = QtWidgets.QCheckBox(self)
        self.toggleExistingAcc.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.toggleExistingAcc.setObjectName("toggleExistingAcc")
        self.gridLayout.addWidget(self.toggleExistingAcc, 2, 4, 1, 2)

        self.retranslate_ui()

        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslate_ui(self):
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("self", "Account Setup"))
        self.buttonAnon.setText(_translate("self", "Go!"))
        self.inputNickname.setPlaceholderText(_translate("self", "Nickname"))
        self.labelContAnon.setText(_translate("self", "Continue anonymously"))
        self.buttonLoginRegister.setText(_translate("self", "Register"))
        self.inputUsername.setPlaceholderText(_translate("self", "Username"))
        self.inputPassword.setPlaceholderText(_translate("self", "Password"))
        self.toggleExistingAcc.setText(
            _translate("self", "Already got an account?            "))

        self.inputNickname.setTabOrder(self.inputNickname, self.buttonAnon)
        self.buttonAnon.setTabOrder(self.buttonAnon, self.toggleExistingAcc)
        self.toggleExistingAcc.setTabOrder(self.toggleExistingAcc,
                                           self.inputUsername)
        self.inputUsername.setTabOrder(self.inputUsername, self.inputEmail)
        self.inputEmail.setTabOrder(self.inputEmail, self.inputPassword)
        self.inputPassword.setTabOrder(self.inputPassword,
                                       self.buttonLoginRegister)

    def toggle_register_button(self):
        if self.buttonLoginRegister.text() == "Log in":
            self.buttonLoginRegister.setText("Register")
        else:
            self.buttonLoginRegister.setText("Log in")


class MessageBox(QtWidgets.QPlainTextEdit):
    """
    Subclassing the QPlainTextEdit widget as it independently
    detects keyPressEvent and will not emit the keyPressEvent
    in the client's QMainWindow; it'll be swallowed otherwise.

    Passing the caller's class instance in order to access the
    client's other widgets, useful for displaying messages.
    """

    CHAR_LIMIT: int = 512

    sendmsg = QtCore.pyqtSignal(int)

    def __init__(self, window: Client, *args):
        super().__init__(*args)
        self.mainWindow = window
        self.sendmsg.connect(self.mainWindow.on_key)
        self.shiftPressed = False

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Used for allowing shift-returning for new lines,
        and specific case-checking means that a new line
        isn't added to the next message after sending one.

        If the character limit is exceeded, it will prevent
        all character-related inputs and if necessary, trim
        the message to the character limit (i.e. if the
        user pasted characters into the field and surpassed
        said limit).

        :param event: The QKeyEvent object emitted, used for
                      fetching the pressed key.
        :return: None
        """
        if len(
                self.toPlainText()) >= self.CHAR_LIMIT and event.key().real < 2 ** 24:
            self.setPlainText(self.toPlainText()[:self.CHAR_LIMIT])

            return

        if not self.shiftPressed and event.key() == QtCore.Qt.Key_Shift:
            self.shiftPressed = True
        elif not self.shiftPressed and event.key() == QtCore.Qt.Key_Return:
            self.sendmsg.emit(event.key())
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Modifying the shiftPressed flag in use for
        shift-returning for new lines.

        :param event:
        :return:
        """
        if event.key() == QtCore.Qt.Key_Shift:
            self.shiftPressed = False
        super().keyReleaseEvent(event)


class ListWidget(QtWidgets.QListWidget):

    def __init__(self, parent: QtWidgets.QWidget, *, cache=None):
        super().__init__(parent)
        self.cache = cache

    def item(self, row: int) -> MessageWidgetItem:
        return super().item(row)

    def focusOutEvent(self, event: QtGui.QFocusEvent) -> None:
        for item in self.selectedItems():
            item.setSelected(False)
        super().focusOutEvent(event)

    def scrollToBottom(self) -> None:
        """
        Only scrolls to the bottom if a new item is added
        and the user is already at the bottom of the list,
        otherwise stay in its current position.

        :return:
        """

        if self.verticalScrollBar().maximum() == self.verticalScrollBar().sliderPosition():
            super().scrollToBottom()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    icon = QtGui.QIcon("../assets/window_icon.png")
    app.setWindowIcon(icon)

    client = Client(HOST, PORT)
    try:
        client.show()

        # Allow for a clean exit
        sys.exit(app.exec_())
    except Exception as ex:
        print(ex)
        if client._socket:
            client._socket.close()
    finally:
        if client.kicked:
            kickWindow = CustomDialog(window_title="Kicked",
                                      message="You were kicked from the server.",
                                      font=client.default_font)
            kickWindow.show()

            sys.exit(app.exec_())
