from PyQt5 import QtWidgets


class MessageWidgetItem(QtWidgets.QListWidgetItem):

    def __init__(self, uuid=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.uuid = uuid
