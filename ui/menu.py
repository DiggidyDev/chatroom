from PyQt5 import QtWidgets

from .themes import ThemeUpdater

style = ThemeUpdater()


class ThemeAction(QtWidgets.QAction):

    def __init__(self, parent: QtWidgets.QMainWindow):
        super().__init__(parent)

        self.parent = parent

    def setup_trigger(self):
        self.triggered.connect(lambda x: style.update_theme(self.parent, self.text()))
