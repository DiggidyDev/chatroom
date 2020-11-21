import datetime
import pickle
import socket
import threading

from PyQt5 import QtCore, QtWidgets, QtGui

from clientside.user import User
from utils.debug import debug
from utils import fmt

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65501


class Client(QtWidgets.QMainWindow):

    def __init__(self, host, port):
        super().__init__()

        self.PORT = port
        self.HOST = host

        self.socket = None
        self.user = User(input("Enter your username: "))

        self.setup_ui()

    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.HOST, self.PORT))
            self.socket = s

            initialcontent = {
                "content": "Initial connection.",
                "system-message": True,
                "user": self.user
            }

            s.sendall(pickle.dumps(initialcontent))

            while not self.stop_event.is_set():
                recv_data = s.recv(4096)
                if recv_data:
                    data = pickle.loads(recv_data)
                    if isinstance(data, bytes):
                        data = pickle.loads(data)
                    print(f"RECV: {data}")
                    if data["system-message"]:
                        if data["content"] == "You have been kicked.":
                            self.stop_event.set()
                            self.close()

                    from utils.update import update_msg_list
                    update_msg_list(self, data)

    def on_key(self, key: QtCore.Qt.Key):
        msg = self.sendMsgBox.toPlainText()

        if key == QtCore.Qt.Key_Return and \
                self.sendMsgBox.hasFocus() and \
                msg.strip() != "":

            self.send_message(msg)
            self.sendMsgBox.setPlainText("")

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("self", "Client"))
        self.usersGroupBox.setTitle(_translate("self", "Users"))
        self.muteButton.setText(_translate("self", "Mute"))
        self.friendButton.setText(_translate("self", "Add friend"))
        __sortingEnabled = self.userList.isSortingEnabled()
        self.userList.setSortingEnabled(False)

        item = self.userList.item(0)
        item.setText(_translate("self", "User1"))
        item = self.userList.item(1)
        item.setText(_translate("self", "User2"))

        self.userList.setSortingEnabled(__sortingEnabled)
        self.chatroomGroupBox.setTitle(_translate("self", "Chatroom"))
        self.chatroomComboBox.setItemText(0, _translate("self", "Main"))
        self.chatroomComboBox.setItemText(1, _translate("self", "Game 1"))
        self.chatroomComboBox.setItemText(2, _translate("self", "Game 2"))
        self.chatroomComboBox.setItemText(3, _translate("self", "Groupchat 1"))
        self.chatroomComboBox.setItemText(4, _translate("self", "Groupchat 2"))
        self.pushButton.setText(_translate("self", "Leave"))
        self.msgListGroupBox.setTitle(_translate("self", "Messages"))

        self.msgList.setSortingEnabled(False)
        self.sendMsgBox.setPlaceholderText(_translate("self", "Send a message..."))
        self.menuView.setTitle(_translate("self", "&View"))
        self.menuThemes.setTitle(_translate("self", "Themes..."))
        self.menuFriends.setTitle(_translate("self", "&Friends"))
        self.menuProfile.setTitle(_translate("self", "&Profile"))
        self.menuHelp.setTitle(_translate("self", "&Help"))

        self.theme1.setText(_translate("self", "Theme 1"))
        self.theme2.setText(_translate("self", "Theme 2"))
        self.theme3.setText(_translate("self", "Theme 3"))
        self.toggleUserList.setText(_translate("self", "Toggle User List"))
        self.toggleUserActionButtons.setText(_translate("self", "Toggle User Action Buttons"))
        self.toggleCoolMode.setText(_translate("self", "Cool mode"))
        self.createTheme.setText(_translate("self", "Create theme..."))
        self.addFriend.setText(_translate("self", "Add friend"))
        self.editName.setText(_translate("self", "Edit name"))
        self.editStatus.setText(_translate("self", "Change status"))
        self.toggleMessageTimestamps.setText(_translate("self", "Toggle Message Timestamps"))
        self.removeFriend.setText(_translate("self", "Remove friend"))
        self.blockFriend.setText(_translate("self", "Block user"))
        self.viewFriends.setText(_translate("self", "View friends"))
        self.editFontSize.setText(_translate("self", "Edit font size"))
        self.leave.setText(_translate("self", "Leave"))
        self.FAQ.setText(_translate("self", "FAQ"))
        self.reportABug.setText(_translate("self", "Report a bug"))
        self.toggleExplicitLanguageFilter.setText(_translate("self", "Toggle Explicit Language Filter"))
        self.aboutChatroom.setText(_translate("self", "About Chatroom"))

    def setup_ui(self):
        self.setObjectName("self")
        self.resize(578, 363)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        # Main window CSS
        self.setStyleSheet("#self {\n"
        "    background-color:#A054ED;\n"
        "}\n"
        "\n"
        "QWidget {\n"
        "    outline: none;\n"
        "}\n"
        "\n"
        "QMenuBar {\n"
        "    background-color: rgb(56, 40, 80);\n"
        "    border-bottom: 1px solid white;\n"
        "    color: white;\n"
        "    font-family: \"Microsoft New Tai Lue\";\n"
        "}\n"
        "\n"
        "QMenu {\n"
        "    border: 1px solid white;\n"
        "    background-color: rgb(51, 35, 75);\n"
        "    color: white;\n"
        "    font-family: \"Microsoft New Tai Lue\";\n"
        "    selection-background-color: #000;\n"
        "    selection-color: #abe25f;\n"
        "}\n"
        "\n"
        "QScrollBar {\n"
        "    background: rgba(0, 0, 0, 0);\n"
        "    padding: 1px;\n"
        "    width: 9px;\n"
        "}\n"
        "\n"
        "QScrollBar::handle {\n"
        "    background: white;\n"
        "    border: 1px solid white;\n"
        "    border-radius: 3px;\n"
        "}\n"
        "\n"
        "QScrollBar::add-page, QScrollBar::sub-page {\n"
        "    background: rgba(0, 0, 0, 0);\n"
        "}\n"
        "\n"
        "QScrollBar::sub-line, QScrollBar::add-line {\n"
        "    height: 0;\n"
        "}")

        self.centralwidget = QtWidgets.QWidget(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setSizeIncrement(QtCore.QSize(1, 1))
        self.centralwidget.setMouseTracking(False)

        # Buttons, containers CSS
        self.centralwidget.setStyleSheet("QPushButton, QPlainTextEdit {\n"
"    background-color: rgb(56, 40, 80);\n"
"    color: white;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"QGroupBox {\n"
"    color: white;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"QLineEdit {\n"
"    border: 1px solid white;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QWidget {\n"
"    font-family: \"Microsoft New Tai Lue\";\n"
"}")

        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.usersGroupBox = QtWidgets.QGroupBox(self.centralwidget)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.usersGroupBox.sizePolicy().hasHeightForWidth())

        self.usersGroupBox.setSizePolicy(sizePolicy)
        self.usersGroupBox.setStyleSheet("")
        self.usersGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.usersGroupBox.setCheckable(False)
        self.usersGroupBox.setObjectName("usersGroupBox")

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.usersGroupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.usersGridLayout = QtWidgets.QGridLayout()
        self.usersGridLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.usersGridLayout.setObjectName("usersGridLayout")
        self.muteButton = QtWidgets.QPushButton(self.usersGroupBox)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.muteButton.sizePolicy().hasHeightForWidth())

        self.muteButton.setSizePolicy(sizePolicy)
        self.muteButton.setCheckable(True)
        self.muteButton.setObjectName("muteButton")
        self.usersGridLayout.addWidget(self.muteButton, 1, 1, 1, 1)
        self.friendButton = QtWidgets.QPushButton(self.usersGroupBox)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.friendButton.sizePolicy().hasHeightForWidth())

        self.friendButton.setSizePolicy(sizePolicy)
        self.friendButton.setCheckable(False)
        self.friendButton.setDefault(False)
        self.friendButton.setFlat(False)
        self.friendButton.setObjectName("friendButton")
        self.usersGridLayout.addWidget(self.friendButton, 1, 0, 1, 1)
        self.userList = QtWidgets.QListWidget(self.usersGroupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.userList.sizePolicy().hasHeightForWidth())
        self.userList.setSizePolicy(sizePolicy)
        self.userList.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        # List and item CSS
        self.userList.setStyleSheet("QListView {\n"
"    background-color: rgb(56, 40, 80);\n"
"    color: white;\n"
"    selection-color: white;\n"
"}\n"
"\n"
"#userList::item:hover {\n"
"    border: 1px solid rgb(56, 40, 80);\n"
"    border-radius: 5px;\n"
"    background-color: #A054ED;\n"
"}\n"
"\n"
"#userList::item:selected {\n"
"    border: 1px solid rgb(56, 40, 80);\n"
"    border-radius:5px;\n"
"    background-color: #000;\n"
"}\n"
"\n"
"")

        self.userList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.userList.setTabKeyNavigation(False)
        self.userList.setObjectName("userList")
        item = QtWidgets.QListWidgetItem()
        self.userList.addItem(item)
        item = QtWidgets.QListWidgetItem()
        self.userList.addItem(item)
        self.usersGridLayout.addWidget(self.userList, 0, 0, 1, 2)
        self.horizontalLayout.addLayout(self.usersGridLayout)
        self.gridLayout.addWidget(self.usersGroupBox, 0, 1, 1, 1)
        self.chatroomGroupBox = QtWidgets.QGroupBox(self.centralwidget)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.chatroomGroupBox.sizePolicy().hasHeightForWidth())

        self.chatroomGroupBox.setSizePolicy(sizePolicy)
        self.chatroomGroupBox.setSizeIncrement(QtCore.QSize(1, 1))
        self.chatroomGroupBox.setStyleSheet("")
        self.chatroomGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.chatroomGroupBox.setObjectName("chatroomGroupBox")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.chatroomGroupBox)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.chatroomComboBox = QtWidgets.QComboBox(self.chatroomGroupBox)
        self.chatroomComboBox.setAutoFillBackground(False)

        # Room selection CSS
        self.chatroomComboBox.setStyleSheet("QComboBox {\n"
"    background-color: rgb(56, 40, 80);\n"
"    selection-background-color: rgb(56, 40, 80);\n"
"    color: white;\n"
"}\n"
"\n"
"QListView {\n"
"    background-color: rgb(56, 40, 80);\n"
"    color: white;\n"
"    selection-background-color: #000;\n"
"    selection-color: #abe25f;\n"
"    outline: none;\n"
"}")

        self.chatroomComboBox.setEditable(False)
        self.chatroomComboBox.setFrame(True)
        self.chatroomComboBox.setProperty("dropdownBackground", True)
        self.chatroomComboBox.setObjectName("chatroomComboBox")

        # Placeholder rooms
        self.chatroomComboBox.addItem("")
        self.chatroomComboBox.addItem("")
        self.chatroomComboBox.addItem("")
        self.chatroomComboBox.addItem("")
        self.chatroomComboBox.addItem("")

        self.gridLayout_4.addWidget(self.chatroomComboBox, 0, 0, 1, 1)
        self.pushButton = QtWidgets.QPushButton(self.chatroomGroupBox)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout_4.addWidget(self.pushButton, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.chatroomGroupBox, 1, 1, 1, 1)
        self.msgListGroupBox = QtWidgets.QGroupBox(self.centralwidget)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.msgListGroupBox.sizePolicy().hasHeightForWidth())
        self.msgListGroupBox.setSizePolicy(sizePolicy)
        self.msgListGroupBox.setStyleSheet("QWidget {\n"
"    outline: none;\n"
"}")
        self.msgListGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.msgListGroupBox.setObjectName("msgListGroupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.msgListGroupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.msgList = QtWidgets.QListWidget(self.msgListGroupBox)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.msgList.sizePolicy().hasHeightForWidth())

        self.msgList.setSizePolicy(sizePolicy)
        self.msgList.setAutoFillBackground(False)

        # Message container scrollbar CSS
        self.msgList.setStyleSheet("QListView {\n"
"    background-color: rgb(56, 40, 80);\n"
"    color: white;\n"
"    alternate-background-color: white;\n"
"}\n"
"\n"
"QFrame {\n"
"    border: 1px solid white;\n"
"    border-radius: 6px;\n"
"    outline: None;\n"
"}\n"
"\n"
"QScrollBar {\n"
"    background-color: black;\n"
"}")

        self.msgList.setLineWidth(0)
        self.msgList.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.msgList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.msgList.setAlternatingRowColors(False)
        self.msgList.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.msgList.setMovement(QtWidgets.QListView.Static)
        self.msgList.setProperty("isWrapping", True)
        self.msgList.setResizeMode(QtWidgets.QListView.Adjust)
        self.msgList.setViewMode(QtWidgets.QListView.ListMode)
        self.msgList.setUniformItemSizes(False)
        self.msgList.setWordWrap(True)
        self.msgList.setObjectName("msgList")

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

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sendMsgBox.sizePolicy().hasHeightForWidth())

        self.sendMsgBox.setSizePolicy(sizePolicy)
        self.sendMsgBox.setMaximumSize(QtCore.QSize(16777215, 50))

        # Message send CSS
        self.sendMsgBox.setStyleSheet("QFrame {\n"
                                      "    border: 1px solid white;\n"
                                      "    border-radius: 6px;\n"
                                      "}")

        self.sendMsgBox.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.sendMsgBox.setFrameShadow(QtWidgets.QFrame.Plain)
        self.sendMsgBox.setLineWidth(0)
        self.sendMsgBox.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
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
        self.menubar.setStyleSheet("QMenuBar::item:selected {\n"
"    background-color: #000;\n"
"    color: #abe25f;\n"
"}")
        self.menubar.setDefaultUp(False)
        self.menubar.setNativeMenuBar(True)
        self.menubar.setObjectName("menubar")
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setAutoFillBackground(False)
        self.menuView.setStyleSheet("")
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
        self.theme1 = QtWidgets.QAction(self)
        self.theme1.setObjectName("theme1")
        self.theme2 = QtWidgets.QAction(self)

        font = QtGui.QFont()
        font.setFamily("Microsoft New Tai Lue")

        self.theme2.setFont(font)
        self.theme2.setObjectName("theme2")
        self.theme3 = QtWidgets.QAction(self)
        self.theme3.setObjectName("theme3")
        self.toggleUserList = QtWidgets.QAction(self)
        self.toggleUserList.setCheckable(True)
        self.toggleUserList.setObjectName("toggleUserList")
        self.toggleUserActionButtons = QtWidgets.QAction(self)
        self.toggleUserActionButtons.setCheckable(True)
        self.toggleUserActionButtons.setObjectName("toggleUserActionButtons")
        self.toggleCoolMode = QtWidgets.QAction(self)
        self.toggleCoolMode.setCheckable(True)

        font = QtGui.QFont()
        font.setFamily("Comic Sans MS")

        self.toggleCoolMode.setFont(font)
        self.toggleCoolMode.setObjectName("toggleCoolMode")
        self.createTheme = QtWidgets.QAction(self)
        self.createTheme.setObjectName("createTheme")
        self.addFriend = QtWidgets.QAction(self)
        self.addFriend.setObjectName("addFriend")
        self.editName = QtWidgets.QAction(self)
        self.editName.setObjectName("editName")
        self.editStatus = QtWidgets.QAction(self)
        self.editStatus.setObjectName("editStatus")
        self.toggleMessageTimestamps = QtWidgets.QAction(self)
        self.toggleMessageTimestamps.setObjectName("toggleMessageTimestamps")
        self.removeFriend = QtWidgets.QAction(self)
        self.removeFriend.setObjectName("removeFriend")
        self.blockFriend = QtWidgets.QAction(self)
        self.blockFriend.setObjectName("blockFriend")
        self.viewFriends = QtWidgets.QAction(self)
        self.viewFriends.setObjectName("viewFriends")
        self.editFontSize = QtWidgets.QAction(self)
        self.editFontSize.setObjectName("editFontSize")
        self.leave = QtWidgets.QAction(self)
        self.leave.setObjectName("leave")
        self.FAQ = QtWidgets.QAction(self)
        self.FAQ.setObjectName("FAQ")
        self.reportABug = QtWidgets.QAction(self)
        self.reportABug.setObjectName("reportABug")
        self.toggleExplicitLanguageFilter = QtWidgets.QAction(self)
        self.toggleExplicitLanguageFilter.setObjectName("toggleExplicitLanguageFilter")
        self.aboutChatroom = QtWidgets.QAction(self)
        self.aboutChatroom.setObjectName("aboutChatroom")

        self.menuThemes.addAction(self.theme1)
        self.menuThemes.addAction(self.theme2)
        self.menuThemes.addAction(self.theme3)
        self.menuThemes.addSeparator()
        self.menuThemes.addAction(self.createTheme)

        self.menuView.addAction(self.toggleExplicitLanguageFilter)
        self.menuView.addAction(self.toggleMessageTimestamps)
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

    def send_message(self, content):
        tosend = fmt.content(content=content, system_message=False, user=self.user)
        print(tosend)
        self.socket.sendall(pickle.dumps(tosend))

    def show(self):
        self.stop_event = threading.Event()
        self.conn_thread = threading.Thread(target=self.connect)
        self.conn_thread.start()

        super().show()


class MessageBox(QtWidgets.QPlainTextEdit):
    """
    Subclassing the QPlainTextEdit widget as it independently
    detects keyPressEvent and will not emit the keyPressEvent
    in the client's QMainWindow; it'll be swallowed.

    Passing the caller's class instance in order to access the
    window's other widgets, useful for displaying messages.
    """

    sendmsg = QtCore.pyqtSignal(int)

    def __init__(self, window: Client, *args):
        super().__init__(*args)
        self.mainWindow = window
        self.sendmsg.connect(self.mainWindow.on_key)

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        self.sendmsg.emit(e.key())
        super().keyPressEvent(e)


class KickedDialog(QtWidgets.QDialog):

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def retranslateUi(self):
        self.setWindowTitle(QtCore.QCoreApplication.translate("Kicked", "Kicked", None))
        self.label.setText(QtCore.QCoreApplication.translate("Kicked", "You were kicked from the room.", None))
        self.pushButton.setText(QtCore.QCoreApplication.translate("Kicked", "OK", None))

    def setup_ui(self):
        if not self.objectName():
            self.setObjectName("Kicked")
        self.resize(304, 181)
        self.setMinimumSize(QtCore.QSize(304, 181))
        self.setMaximumSize(QtCore.QSize(304, 181))
        self.setStyleSheet("QPushButton, QPlainTextEdit {\n"
                           "	background-color: rgb(56, 40, 80);\n"
                           "	color: white;\n"
                           "	font-weight: bold;\n"
                           "}\n"
                           "QLabel {\n"
                           "    color: white;\n"
                           "}"
                           "#Kicked {\n"
                           "	background-color:#A054ED;\n"
                           "}\n"
                           "")
        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QtCore.QRect(70, 60, 161, 16))
        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QtCore.QRect(110, 120, 75, 23))
        self.pushButton.clicked.connect(self.close)

        self.retranslateUi()

        QtCore.QMetaObject.connectSlotsByName(self)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)

    window = Client(
        HOST,
        PORT
    )
    try:
        window.show()

        sys.exit(app.exec_())
    finally:
        print("Goodbye")
        kickWindow = KickedDialog()
        kickWindow.show()
        sys.exit(app.exec_())
