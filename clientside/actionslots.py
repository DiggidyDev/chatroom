from ui.info import CustomDialog
from utils.update import get_version

from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl


class ViewSlots:

    def change_fonts():
        pass


class HelpSlots:

    @staticmethod
    def about_chatroom() -> None:
        chatroom_version = get_version()

        info_window = CustomDialog(window_title="About Chatroom",
                                   message=f"**Current Version:** {chatroom_version}\n\n"
                                           f"**Developer:** Valentine Wilson\n\n"
                                           f"*[Source code](https://github.com/DiggidyDev/chatroom)*")
        info_window.exec_()

    @staticmethod
    def faq() -> None:
        faq_window = CustomDialog(window_title="FAQ",
                                  message="Q: something\n\n"
                                          "A: another thing")
        faq_window.exec_()

    @staticmethod
    def report_a_bug() -> None:
        github_issues_url = QUrl("https://github.com/DiggidyDev/chatroom/issues")
        QDesktopServices.openUrl(github_issues_url)
