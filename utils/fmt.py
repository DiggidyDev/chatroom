import hashlib
import pickle
import re
from datetime import datetime
from typing import Union

from PyQt5 import QtWidgets

from user import User
from message import Message


def _get_explicit_words() -> str:
    import pkgutil

    return pkgutil.get_data("clientside", "explicit_words_list.txt").decode("utf-8")


EXPLICIT_WORDS = _get_explicit_words()


def content(*, message_content: str, system_message: bool, user: User) -> dict:
    """
    Creates a message-friendly format for sending
    messages between the client and server.
    
    :param message_content: The contents to be displayed as a message.
    :param system_message: An indication as to whether it's been sent
                           from the server or not (i.e. an important message).
    :param user: The user sending the message.
    :return: A dict suitable for sending messages in any chatroom.
    """
    struct = {
        "content": message_content,
        "system_message": system_message,
        "user": user
    }

    return struct


def decode_bytes(bytes_to_decode: bytes) -> Union[str, dict, tuple, User, Message]:
    return pickle.loads(bytes_to_decode)


def encode_str(obj_to_encode: Union[str, dict, tuple, User, Message]) -> bytes:
    return pickle.dumps(obj_to_encode)


def filter_content(msg: str) -> str:
    pattern = EXPLICIT_WORDS.replace("\r\n", "|")
    indices = [i.span() for i in re.finditer("|".join(sorted(pattern.split("|"), key=lambda x: len(x))), msg.lower())]
    filtered_msg = list(msg)

    for start, end in indices:
        for i in range(start, end):
            filtered_msg[i] = "*"

    filtered_msg = "".join(filtered_msg)

    return filtered_msg


def hash_pw(password: str, uuid: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), uuid.encode("utf-8"), 200000).hex()


# noinspection PyTypeHints
def update_msg_list(widget: QtWidgets.QMainWindow, received: dict):
    if "user" in received.keys():
        item = QtWidgets.QListWidgetItem()

        if isinstance(received, bytes):
            received = decode_bytes(received)

        sender = str(received["user"])
        message_content = received["content"]

        # Display `You` for messages you, the user, have sent
        # as to distinguish messages in an easier fashion
        if hasattr(widget, "user"):
            if received["user"].uuid == widget.user.uuid:
                sender = "You"

        current_time = datetime.now()

        if received['system_message']:
            if received['content'] == "Initial connection.":
                item.setText(f"{sender} joined.")
            elif received['content'] == "Leaving":
                item.setText(f"{sender} left.")
            else:
                item.setText(received["content"])
        elif not received['system_message']:
            if hasattr(widget, "toggleExplicitLanguageFilter") and widget.toggleExplicitLanguageFilter.isChecked():
                message_content = filter_content(message_content)
            item.setText(f"{sender}: {message_content}")

        item.setToolTip(fr"""Timestamp: {current_time.strftime("%Y/%m/%d - %H:%M:%S")}""")

        try:
            widget.msgList.addItem(item)
        except RuntimeError:
            return


def update_user_list(widget: QtWidgets.QMainWindow, recv_content: dict):
    endings = {" was kicked.", " left."}

    if recv_content["content"] == "Initial connection.":
        new_user = recv_content["user"]
        server_user_list: list = recv_content["userlist"]

        if new_user.name == widget.user.name:
            for user in server_user_list:
                user_item = QtWidgets.QListWidgetItem()
                user_item.setText(user)
                widget.userList.addItem(user_item)
        else:
            user_item = QtWidgets.QListWidgetItem()
            user_item.setText(new_user.name)
            widget.userList.addItem(user_item)

    for ending in endings:
        if recv_content["content"].endswith(ending):

            user_to_remove = recv_content["content"][:-len(ending)]

            if hasattr(widget, "userList"):
                widget.userList.takeItem([
                    widget.userList.item(i).text() for i in range(widget.userList.count())
                ].index(user_to_remove))


def is_valid_email(email: str) -> re.Match:
    email_pattern = r"^(\w+[\+\.\w-]*@)([\w-]+\.)*\w+[\w-]*\.([a-z]{2,4}|d+)$"
    return re.search(email_pattern, email)
