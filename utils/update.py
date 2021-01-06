from PyQt5 import QtWidgets, QtCore

# TODO: Auto-update ZIP
CHUNK_SIZE = 2 ** 20

# Set the current application's download type
# based on the modules available to be imported
try:
    from utils.versionbin import get_version, set_version

    DL_TYPE = "exe"
except ImportError:
    from utils.versionzip import get_version, set_version

    DL_TYPE = "zip"


def is_update_available(show_window: bool = False) -> bool:
    """
    Will return True if any updates are found.

    Using the queried version from the website, this checks
    whether the current client's version is up-to-date. If
    it isn't, it will [PERFORM UPDATE].
    :return:
    """

    if show_window:
        check = ProgressWindow()
        check.show()
        check.check_for_updates()

    if get_live_version() != get_version():
        return True

    return False


def get_live_version() -> str:
    """
    Fetches the current version of the client being hosted
    on the website. This will be used to check for new versions
    and auto-updating the application.

    :return:
    """
    import json  # For converting the requested string into JSON
    import urllib.request, urllib.error  # Querying for the current live version

    # TODO: Try/except catch any status errors
    try:
        live_version = json.loads(urllib.request.urlopen("https://diggydev.co.uk/chatroom/version.json").read())["live_bin"]
    except urllib.error.URLError as e:
        print("BEEP BOOP SOMETHING GONE WRONG")

    return live_version


def start_download():
    import threading

    dl_window = ProgressWindow()
    dl_thread = threading.Thread(target=dl_window.download_new_client)
    dl_thread.setDaemon(True)
    dl_thread.start()
    dl_window.exec_()


class ProgressWindow(QtWidgets.QDialog):

    def __init__(self):
        super(ProgressWindow, self).__init__()
        self.setup_ui()

    def check_for_updates(self):
        self.labelCurrentTask.setText("Checking for updates...")

        wait = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(2000, wait.quit)
        wait.exec_()
        self.close()

    def download_new_client(self):
        if DL_TYPE == "exe":
            try:
                import os
                import requests

                if not os.path.isfile("updater.exe"):
                    self.labelCurrentTask.setText("Fetching updater.exe")

                    updater = requests.get(f"https://diggydev.co.uk/chatroom/updater.exe", stream=True)
                    updater_size = int(updater.headers["Content-Length"])
                    cur_size = 0

                    self.labelCurrentTask.setText("Downloading updater.exe")

                    with open("updater.exe", "wb") as up_exe:
                        for chnk in updater.iter_content(chunk_size=CHUNK_SIZE):
                            up_exe.write(chnk)
                            cur_size += len(chnk)
                            self.progressBar.setValue(int((cur_size/updater_size) * 100))

                    self.labelCurrentTask.setText("Done!")
                    updater.close()
                self.progressBar.setValue(0)
                self.labelCurrentTask.setText("Fetching client.exe")

                new_client = requests.get(f"https://diggydev.co.uk/chatroom/client.{DL_TYPE}", stream=True)
                new_client_size = int(new_client.headers["Content-Length"])
                cur_size = 0

                print(new_client)

                self.labelCurrentTask.setText("Downloading client.exe")
                with open("client-new.exe", "wb") as exe:
                    for chnk in new_client.iter_content(chunk_size=CHUNK_SIZE):  # 1 MiB
                        exe.write(chnk)
                        cur_size += len(chnk)
                        self.progressBar.setValue(int((cur_size / new_client_size) * 100))

                new_client.close()
            except Exception as e:
                print(e)
            finally:
                import os
                import sys

                set_version(get_live_version())

                os.execl("updater.exe", *([sys.executable] + sys.argv))
        if DL_TYPE == "zip":
            from zipfile import ZipFile

            with ZipFile("client.zip", "r") as _zip:
                _zip.extractall()

    def setup_ui(self):
        if not self.objectName():
            self.setObjectName("self")

        self.resize(289, 225)
        self.setMinimumSize(QtCore.QSize(289, 225))
        self.setMaximumSize(QtCore.QSize(289, 225))

        self.setStyleSheet(u"#self {\n"
"	background-color:#A054ED;\n"
"}\n"
"\n"
"QWidget {\n"
"	outline: none;\n"
"}\n"
"\n"
"QMenuBar {\n"
"	background-color: rgb(56, 40, 80);\n"
"	border-bottom: 1px solid white;\n"
"	color: white;\n"
"	font-family: \"Microsoft New Tai Lue\";\n"
"}\n"
"\n"
"QMenu {\n"
"	border: 1px solid white;\n"
"	background-color: rgb(51, 35, 75);\n"
"	color: white;\n"
"	font-family: \"Microsoft New Tai Lue\";\n"
"	selection-background-color: #000;\n"
"	selection-color: #abe25f;\n"
"}\n"
"\n"
"QScrollBar {\n"
"	background: rgba(0, 0, 0, 0);\n"
"	padding: 1px;\n"
"	width: 9px;\n"
"}\n"
"\n"
"QScrollBar::handle {\n"
"	background: white;\n"
"	border: 1px solid white;\n"
"	border-radius: 3px;\n"
"}\n"
"\n"
"QScrollBar::add-page, QScrollBar::sub-page {\n"
"	background: rgba(0, 0, 0, 0);\n"
"}\n"
"\n"
"QScrollBar::sub-line, QScrollBar::add-line {\n"
"	height: 0;\n"
"}")
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName(u"gridLayout")
        self.spacerBottom = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerBottom, 7, 0, 1, 1)

        self.spacerDownTop = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerDownTop, 1, 0, 1, 1)

        self.spacerMid = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerMid, 3, 0, 1, 1)

        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setObjectName(u"progressBar")

        self.gridLayout.addWidget(self.progressBar, 4, 0, 1, 1)

        self.spacerTop = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerTop, 0, 0, 1, 1)

        self.labelCurrentTask = QtWidgets.QLabel(self)
        self.labelCurrentTask.setObjectName(u"labelCurrentTask")
        self.labelCurrentTask.setAlignment(QtCore.Qt.AlignCenter)

        self.gridLayout.addWidget(self.labelCurrentTask, 2, 0, 1, 1)

        self.spacerUpBot = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerUpBot, 6, 0, 1, 1)

        self.spacerMidBot = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerMidBot, 5, 0, 1, 1)


        self.retranslateUi(self)

        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Updater):
        Updater.setWindowTitle(QtCore.QCoreApplication.translate("self", u"Chatroom Auto-updater", None))
        self.labelCurrentTask.setText(QtCore.QCoreApplication.translate("self", u"Downloading...", None))
