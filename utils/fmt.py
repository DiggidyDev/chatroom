import hashlib
import pickle
import re
from datetime import datetime
from typing import Iterable, Type, Union

from PyQt5 import QtWidgets

from message import Message
from user import User
from .cache import Cache
from ui.items import MessageWidgetItem


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


def do_friendly_conversion_to(cls: Union[Type[Message], Type[User]], data):
    valid_keys = {k.strip("_") for k in {*cls.class_args()}}.intersection(data.keys())
    valid_data = {k: v for k, v in data.items() if k in valid_keys}

    return Message(**valid_data)


def encode_str(obj_to_encode: Union[str, dict, tuple, User, Message]) -> bytes:
    return pickle.dumps(obj_to_encode)


def filter_content(msg: str) -> str:
    pattern = EXPLICIT_WORDS.replace("\r\n", "|")
    indices = [i.span() for i in re.finditer(" |".join(sorted(pattern.split("|"), key=lambda x: len(x))), f" {msg.lower()} ")]
    filtered_msg = list(msg)

    for start, end in indices:
        for i in range(start, end-1):
            try:
                filtered_msg[i-1] = "*"
            except IndexError:
                pass

    filtered_msg = "".join(filtered_msg)

    return filtered_msg


def hash_pw(password: str, uuid: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), uuid.encode("utf-8"), 200000).hex()


# noinspection PyTypeHints,PyTypeChecker
def update_msg_list(widget: QtWidgets.QMainWindow, received: Union[dict, Iterable[Message]], *, cache: Cache = None,
                    pos=None):
    if isinstance(received, dict):
        print(received)
        try:
            item = MessageWidgetItem(uuid=received["message_uuid"])
        except KeyError as e:
            item = QtWidgets.QListWidgetItem()

        if hasattr(widget, "current_font"):
            item.setFont(widget.current_font)

        if isinstance(received, bytes):
            received = decode_bytes(received)

        sender = str(received["user"])
        message_content = received["content"]

        # Display `You` for messages you, the user, have sent
        # as to distinguish messages in an easier fashion
        if hasattr(widget, "user"):
            if widget.user.uuid == received["user"].uuid:
                sender = "You"
            if str(received["user"]) == "$DELETED_USER":
                sender = "Deleted user"

        if received['system_message']:
            print(received['content'])
            if message_content == "Initial connection.":
                item.setText(f"{sender} joined.")
            elif message_content == "User left.":
                item.setText(f"{sender} left.")
            else:
                item.setText(received["content"])
        elif not received['system_message']:
            if hasattr(widget, "toggleExplicitLanguageFilter") and widget.toggleExplicitLanguageFilter.isChecked():
                message_content = filter_content(message_content)
            item.setText(f"{sender}: {message_content}")

        time = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
        if "created_at" in received.keys():
            time = received["created_at"]

            if isinstance(time, datetime):
                time = time.strftime("%Y/%m/%d - %H:%M:%S")

        item.setToolTip(time)

        try:
            if pos is None:
                widget.msgList.takeItem(0)
                widget.msgList.addItem(item)
            else:
                widget.msgList.takeItem(widget.msgList.count()-1)
                widget.msgList.insertItem(0, item)
        except RuntimeError as e:
            print(e)

    elif isinstance(received, Iterable):
        print(received)
        for i, message in enumerate(received, start=1):
            item = MessageWidgetItem(uuid=message.uuid)
            item.setToolTip(message.timestamp)

            sender = message.user

            if hasattr(widget, "current_font"):
                item.setFont(widget.current_font)

            if hasattr(widget, "user"):
                if widget.user.uuid == message.user.uuid:
                    sender = "You"
                if str(message.user) == "$DELETED_USER":
                    sender = "Deleted user"

            if message.system_message:
                if message.content == "Initial connection.":
                    item.setText(f"{sender} joined.")
                elif message.content == "User left.":
                    item.setText(f"{sender} left")
                else:
                    item.setText(message.content)
            elif not message.system_message:
                content = message.content
                if hasattr(widget, "toggleExplicitLanguageFilter") and widget.toggleExplicitLanguageFilter.isChecked():
                    content = filter_content(message.content)
                item.setText(f"{sender}: {content}")

            cache.cache_to("top", message)
            if widget.msgList.count() < 100:
                widget.msgList.insertItem(0, item)
        print(cache)


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

            if hasattr(widget, "current_font"):
                user_item.setFont(widget.current_font)

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


def is_valid_section_name(section):
    sect_pattern = r"^[a-zA-Z]{3,20}$"
    if not re.search(sect_pattern, section):
        raise NameError("Please ensure your theme name is 3-20 chars long, only containing A-z")


def is_valid_anon_username(name):
    pattern = r"^[a-zA-Z|.|_|\-|\d|]{3,10}$"
    if not re.search(pattern, name):
        raise NameError("Please enter a valid name.\nIt must be between 3 and 10 characters.\n\n"
                        "It may contain the following characters:\n\na-Z 0-9 . - _")


def is_valid_username(name):
    pattern = r"^[a-zA-Z|.|_|\-|\d|]{3,24}$"
    if not re.search(pattern, name):
        raise NameError("Please enter a valid name.\nIt must be between 3 and 24 characters.\n\n"
                        "It may contain the following characters:\n\na-Z 0-9 . - _")
