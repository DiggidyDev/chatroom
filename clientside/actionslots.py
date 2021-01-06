from ui.info import CustomDialog
from utils.update import get_version

from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
import clientside.client


class ViewSlots:

    @staticmethod
    def change_fonts(widget: clientside.client.Client):
        try:
            widget.toggle_comic_sans()
        except Exception as e:
            print(e)


class HelpSlots:

    @staticmethod
    def about_chatroom(widget: clientside.client.Client) -> None:
        chatroom_version = get_version()

        info_window = CustomDialog(window_title="About Chatroom",
                                   message=f"**Current Version:** {chatroom_version}\n\n"
                                           f"**Developer:** Valentine Wilson\n\n"
                                           f"*[Source code](https://github.com/DiggidyDev/chatroom)*",
                                   font=widget.current_font)
        info_window.exec_()

    @staticmethod
    def faq(widget: clientside.client.Client) -> None:
        faq_window = CustomDialog(window_title="FAQ",
                                  message="Q: something\n\n"
                                          "A: another thing",
                                  font=widget.current_font)
        faq_window.exec_()

    @staticmethod
    def report_a_bug() -> None:
        github_issues_url = QUrl("https://github.com/DiggidyDev/chatroom/issues")
        QDesktopServices.openUrl(github_issues_url)
