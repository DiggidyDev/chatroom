import pickle
import socket
import threading
import datetime

from PyQt5 import QtCore, QtWidgets, QtGui

from user import User
from utils.debug import debug

HOST = "127.0.0.1"
PORT = 65501


class Ui_MyWindow(QtWidgets.QMainWindow):
    sendmsg = QtCore.pyqtSignal(int)

    def __init__(self, host, port):
        super().__init__()

        self.PORT = port
        self.HOST = host

        self.socket = None
        self.u = User(input("Enter your username: "))

        self.setupUi()

    def on_key(self, key: QtCore.Qt.Key):

        # Ensuring they press enter while the QLineEdit Widget
        # is in focus, and it's not empty
        if key == QtCore.Qt.Key_Return and \
                self.msginput.hasFocus() and \
                self.msginput.text() != "":

            self.send_message(self.msginput.text())
            self.msginput.setText("")

        print(key)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Instantiating the superclass's event, and adding our own
        event handler for when the user presses a key.
        :param event:
        :return:
        """
        super().keyPressEvent(event)
        self.sendmsg.emit(event.key())

    @debug(verbose=True)
    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.HOST, self.PORT))
            self.socket = s

            initialcontent = {
                "content": "Initial connection.",
                "system-message": True,
                "user": self.u
            }

            s.sendall(pickle.dumps(initialcontent))

            while True:
                data = pickle.loads(s.recv(4096))
                if data:
                    print(f"RECV: {pickle.loads(data)}")
                    self.update_msg_list(pickle.loads(data))

    @staticmethod
    def format_content(**kwargs):
        """
        Correctly format content for outgoing
        :param kwargs:
        :return:
        """
        struct = {
            "content": kwargs["content"],
            "system-message": kwargs["system_message"],
            "user": kwargs["user"]
        }

        return struct

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MyWindow", f"Client: {self.u.nickname}"))
        self.msginput.setPlaceholderText(_translate("MyWindow", "Send a message..."))
        __sortingEnabled = self.msglist.isSortingEnabled()
        self.msglist.setSortingEnabled(False)
        item = self.msglist.item(0)
        item.setText(_translate("MyWindow", "Something from a user"))
        self.msglist.setSortingEnabled(__sortingEnabled)

    def setupUi(self):
        self.setObjectName("MyWindow")
        self.setEnabled(True)
        self.resize(332, 200)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())

        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(332, 200))
        self.setMaximumSize(QtCore.QSize(332, 200))

        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setAnimated(True)
        self.setDocumentMode(False)
        self.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.setUnifiedTitleAndToolBarOnMac(False)

        self.centralwidget = QtWidgets.QWidget()
        self.centralwidget.setAutoFillBackground(False)
        self.centralwidget.setStyleSheet("")
        self.centralwidget.setInputMethodHints(QtCore.Qt.ImhNone)
        self.centralwidget.setObjectName("centralwidget")

        self.msginput = QtWidgets.QLineEdit(self.centralwidget)
        self.msginput.setGeometry(QtCore.QRect(10, 150, 311, 20))
        self.msginput.setStyleSheet("")
        self.msginput.setInputMethodHints(QtCore.Qt.ImhNone)
        self.msginput.setCursorMoveStyle(QtCore.Qt.LogicalMoveStyle)
        self.msginput.setClearButtonEnabled(True)
        self.msginput.setObjectName("msginput")
        self.sendmsg.connect(self.on_key)

        self.msglist = QtWidgets.QListWidget(self.centralwidget)
        self.msglist.setGeometry(QtCore.QRect(10, 10, 311, 121))
        self.msglist.setObjectName("msglist")

        item = QtWidgets.QListWidgetItem()
        self.msglist.addItem(item)

        self.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 332, 20))
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def send_message(self, content):
        tosend = self.format_content(content=content, system_message=False, user=self.u)
        print(tosend)
        self.socket.sendall(pickle.dumps(tosend))

    def show(self):
        conn_thread = threading.Thread(target=self.connect)
        conn_thread.setDaemon(True)
        conn_thread.start()

        super().show()

    def update_msg_list(self, received):
        item = QtWidgets.QListWidgetItem()
        sender = str(received['user'])

        # Display `You` for messages you, the user, have sent
        # as to distinguish messages in an easier fashion
        if received['user'].get_uuid() == self.u.get_uuid():
            sender = "You"

        currentTime = datetime.datetime.now()

        if received['system-message']:
            if received['content'] == "Initial connection.":
                item.setText(f"{sender} joined.")
        elif not received['system-message']:
            item.setText(f"{sender}: {received['content']}")

        item.setToolTip(f"""Timestamp: {currentTime.strftime("%Y/%m/%d - %H:%M:%S")}
UUID: {received['user'].get_uuid()}""")
        self.msglist.addItem(item)
        self.msglist.scrollToBottom()


def run():
    import sys
    app = QtWidgets.QApplication(sys.argv)

    window = Ui_MyWindow(
        HOST,
        PORT
    )

    window.show()

    sys.exit(app.exec_())

run()
