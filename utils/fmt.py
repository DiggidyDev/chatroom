import hashlib
import pickle
import re
from datetime import datetime

from PyQt5 import QtWidgets


def content(**kwargs):
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


def hash_pw(password: str, uuid: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), uuid.encode("utf-8"), 200000).hex()


def update_msg_list(widget: QtWidgets.QMainWindow,
                    received: dict):
    if "user" in received.keys():
        item = QtWidgets.QListWidgetItem()
        if isinstance(received, bytes):
            received = pickle.loads(received)
        sender = str(received["user"])

        # Display `You` for messages you, the user, have sent
        # as to distinguish messages in an easier fashion
        if hasattr(widget, "user"):
            if received["user"].get_uuid() == widget.user.get_uuid():
                sender = "You"

        currentTime = datetime.now()

        if received['system-message']:
            if received['content'] == "Initial connection.":
                item.setText(f"{sender} joined.")
            elif received['content'] == "Leaving":
                item.setText(f"{sender} left.")
            else:
                item.setText(received["content"])
        elif not received['system-message']:
            # EXPLICIT FILTER
            item.setText(f"{sender}: {received['content'].lower().replace('fuck', '****')}")

        item.setToolTip(fr"""Timestamp: {currentTime.strftime("%Y/%m/%d - %H:%M:%S")}
    UUID: {received['user'].get_uuid() if received['user'] != 'Server' else None}""".strip())
        try:
            widget.msgList.addItem(item)
        except RuntimeError:
            return

        widget.msgList.scrollToBottom()


def update_user_list(widget: QtWidgets.QMainWindow,
                     recv_content: dict):
    if recv_content["content"] == "Initial connection.":
        new_user = recv_content["user"]
        server_user_list: list = recv_content["userlist"]
        if new_user.name == widget.user.name:
            for user in server_user_list:
                uitem = QtWidgets.QListWidgetItem()
                uitem.setText(user)
                widget.userList.addItem(uitem)
        else:
            uitem = QtWidgets.QListWidgetItem()
            uitem.setText(new_user.name)
            widget.userList.addItem(uitem)
    elif recv_content["content"].endswith(" was kicked."):
        kicked_user = recv_content["content"][:-12]
        if hasattr(widget, "userList"):
            widget.userList.takeItem([
                widget.userList.item(i).text() for i in range(widget.userList.count())
            ].index(kicked_user))
    elif recv_content["content"].endswith(" left."):
        left_user = recv_content["content"][:-6]
        if hasattr(widget, "userList"):
            widget.userList.takeItem([
                                         widget.userList.item(i).text() for i in range(widget.userList.count())
                                     ].index(left_user))


def is_valid_email(email: str) -> re.Match:
    email_pattern = r"^(\w+[\+\.\w-]*@)([\w-]+\.)*\w+[\w-]*\.([a-z]{2,4}|d+)$"
    return re.search(email_pattern, email)
