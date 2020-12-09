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


def update_msg_list(widget: QtWidgets.QMainWindow, received: dict):
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
            item.setText(f"{sender}: {received['content'].replace('fuck', '****')}")

        item.setToolTip(fr"""Timestamp: {currentTime.strftime("%Y/%m/%d - %H:%M:%S")}
    UUID: {received['user'].get_uuid() if received['user'] != 'Server' else None}""".strip())
        try:
            widget.msgList.addItem(item)
        except RuntimeError:
            return

        widget.msgList.scrollToBottom()


def is_valid_email(email: str) -> re.Match:
    email_pattern = r"^(\w+[\+\.\w-]*@)([\w-]+\.)*\w+[\w-]*\.([a-z]{2,4}|d+)$"
    return re.search(email_pattern, email)
