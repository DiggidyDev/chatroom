from ui.info import CustomDialog


class HelpSlots:

    @staticmethod
    def about_chatroom():
        version_file = open("version.txt", "r")
        chatroom_version = version_file.read()
        version_file.close()

        info_window = CustomDialog(window_title="About Chatroom",
                                   message=f"**Current Version:** {chatroom_version}  \n\n"
                                           f"**Developer:** Valentine Wilson  \n\n"
                                           f"*[Source code](https://github.com/DiggidyDev/chatroom)*")
        info_window.exec_()
