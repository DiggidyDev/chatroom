from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

import clientside.client
from ui.info import CustomDialog
from ui.themes import ThemeCreator
from utils.update import get_version


class HelpSlots:

    @staticmethod
    def about_chatroom(widget: clientside.client.Client) -> None:
        chatroom_version = get_version()

        info_window = CustomDialog(window_title="About Chatroom",
                                   message=f"**Current Version:** {chatroom_version}\n\n"
                                           "**Developer:** Valentine Wilson\n\n"
                                           "*[Source code](https://github.com/DiggidyDev/chatroom)*",
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


class FriendsSlots:

    @staticmethod
    def add_friend():
        pass

    @staticmethod
    def block_friend():
        pass

    @staticmethod
    def remove_friend():
        pass

    @staticmethod
    def view_friends(widget: clientside.client.Client):
        friends_list_dialog = CustomDialog(window_title="Friends",
                                           message=widget.user.friends,
                                           font=widget.current_font)
        friends_list_dialog.exec_()


class ViewSlots:

    @staticmethod
    def change_fonts(widget: clientside.client.Client):
        try:
            widget.toggle_comic_sans()
        except Exception as e:
            print(e)

    @staticmethod
    def create_theme(widget: clientside.client.Client):
        a = ThemeCreator(widget)
        a.exec_()

    @staticmethod
    def toggle_alternate_row_colours(widget: clientside.client.Client):
        try:
            widget.toggle_alternate_row_colours()
        except Exception as e:
            print(e)

    @staticmethod
    def toggle_user_action_buttons(widget: clientside.client.Client):
        try:
            widget.toggle_user_buttons()
        except Exception as e:
            print(e)

    @staticmethod
    def toggle_user_list(widget: clientside.client.Client):
        try:
            widget.toggle_user_list()
        except Exception as e:
            print(e)
