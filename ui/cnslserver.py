from PyQt5 import QtWidgets


class ConsoleWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.setupUI()

    def setupUI(self):
        pass


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ConsoleWindow()
    sys.exit(app.exec_())
