import datetime
import pickle
import socket
import threading

from PyQt5 import QtCore, QtWidgets, QtGui

from clientside.user import User
from utils import fmt

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65501


class Client(QtWidgets.QMainWindow):

    sendmsg = QtCore.pyqtSignal(int)

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

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Instantiating the superclass' event, and adding our own
        event handler for when the user presses a key.
        :param event:
        :return:
        """
        super().keyPressEvent(event)
        self.sendmsg.emit(event.key())

    def on_key(self, key: QtCore.Qt.Key):

        # Ensuring they press enter while the QLineEdit Widget
        # is in focus, and it's not empty
        if key == QtCore.Qt.Key_Return and \
                self.msginput.hasFocus() and \
                self.msginput.text().strip() != "":

            self.send_message(self.msginput.text())
            self.msginput.setText("")

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MyWindow", f"Client: {self.user.nickname}"))
        self.msginput.setPlaceholderText(_translate("MyWindow", "Send a message..."))
        __sortingEnabled = self.msgList.isSortingEnabled()
        self.msgList.setSortingEnabled(False)

        currentTime = datetime.datetime.now()
        item = self.msgList.item(0)
        item.setText(_translate("MyWindow", f"{currentTime.strftime('[%Y/%m/%d  -  %H:%M %p]')}"))

        self.msgList.setSortingEnabled(__sortingEnabled)

    def setup_ui(self):
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

        self.msgList = QtWidgets.QListWidget(self.centralwidget)
        self.msgList.setGeometry(QtCore.QRect(10, 10, 311, 121))
        self.msgList.setObjectName("msglist")

        item = QtWidgets.QListWidgetItem()
        self.msgList.addItem(item)

        self.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 332, 20))
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)

        self.retranslate_ui()
        QtCore.QMetaObject.connectSlotsByName(self)

    def send_message(self, content):
        tosend = fmt.content(content=content, system_message=False, user=self.user)
        print(tosend)
        self.socket.sendall(pickle.dumps(tosend))

    def show(self):
        self.stop_event = threading.Event()
        self.conn_thread = threading.Thread(target=self.connect)
        self.conn_thread.start()
        super().show()


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
        # window.socket.sendall(pickle.dumps(fmt.content(content="Leaving", system_message=True, user=window.user)))
