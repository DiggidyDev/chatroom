from PyQt5 import QtWidgets


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.setupUI()

    def setupUI(self):
        self.setFixedSize(500, 500)
        self.move(300, 300)

        self.label = QtWidgets.QLabel(self)
        self.label.move(50, 50)
        self.label.setText("Hello!")

        self.show()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())

