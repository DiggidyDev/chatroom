from PyQt5 import QtWidgets, QtCore

from ui.themes import ThemeUpdater

style = ThemeUpdater()

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
    Using the queried version from the website, this checks
    whether the current client's version is up-to-date. If
    it isn't, it will download an updater if none is
    found, then execute it.

    :return: A boolean indicating whether an update has been found.
    """

    if show_window:
        check = ProgressWindow()
        style.to_current_theme(check)
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
    from urllib import request, error  # Querying for the current live version

    # TODO: Try/except catch any status errors
    try:
        live_version = json.loads(request.urlopen("https://diggydev.co.uk/chatroom/version.json").read())["live_bin"]
    except error.URLError as e:
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
        super().__init__()
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

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.spacerBottom = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerBottom, 7, 0, 1, 1)

        self.spacerDownTop = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerDownTop, 1, 0, 1, 1)

        self.spacerMid = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerMid, 3, 0, 1, 1)

        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setObjectName("progressBar")

        self.gridLayout.addWidget(self.progressBar, 4, 0, 1, 1)

        self.spacerTop = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerTop, 0, 0, 1, 1)

        self.labelCurrentTask = QtWidgets.QLabel(self)
        self.labelCurrentTask.setObjectName("labelCurrentTask")
        self.labelCurrentTask.setAlignment(QtCore.Qt.AlignCenter)

        self.gridLayout.addWidget(self.labelCurrentTask, 2, 0, 1, 1)

        self.spacerUpBot = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerUpBot, 6, 0, 1, 1)

        self.spacerMidBot = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.gridLayout.addItem(self.spacerMidBot, 5, 0, 1, 1)


        self.retranslateUi(self)

        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, updater):
        updater.setWindowTitle(QtCore.QCoreApplication.translate("self", u"Chatroom Auto-updater", None))
        self.labelCurrentTask.setText(QtCore.QCoreApplication.translate("self", u"Downloading...", None))
