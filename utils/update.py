from datetime import datetime
import pickle

from PyQt5 import QtWidgets


def update_msg_list(widget: QtWidgets.QMainWindow, received: dict):
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
        item.setText(f"{sender}: {received['content']}")

    item.setToolTip(fr"""Timestamp: {currentTime.strftime("%Y/%m/%d - %H:%M:%S")}
UUID: {received['user'].get_uuid() if received['user'] != 'Server' else None}""".strip())
    try:
        widget.msgList.addItem(item)
    except RuntimeError:
        return
    widget.msgList.scrollToBottom()

