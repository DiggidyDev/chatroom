from PyQt5 import QtWidgets, QtCore

from .themes import ThemeUpdater

style = ThemeUpdater()


class CustomDialog(QtWidgets.QDialog):

    def __init__(self, *, window_title, message, font):
        super().__init__()
        self.window_title = window_title
        self.message = message
        self._font = font
        self.setup_ui()
        style.to_current_theme(self)

    def retranslate_ui(self):
        self.setWindowTitle(QtCore.QCoreApplication.translate(self.window_title, self.window_title, None))
        self.label.setText(QtCore.QCoreApplication.translate(self.window_title, self.message, None))
        self.pushButton.setText(QtCore.QCoreApplication.translate(self.window_title, "OK", None))
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

    def setup_ui(self):
        if not self.objectName():
            self.setObjectName(self.window_title)

        self.resize(304, 181)
        self.setMinimumSize(QtCore.QSize(304, 181))
        self.setMaximumSize(QtCore.QSize(304, 181))
        self.setStyleSheet("QPushButton, QPlainTextEdit {\n"
                           "	background-color: rgb(56, 40, 80);\n"
                           "	color: white;\n"
                           "	font-weight: bold;\n"
                           "}\n"
                           "QLabel {\n"
                           "    color: white;\n"
                           "}"
                           "#WINDOWTITLE {\n"
                           "	background-color:#A054ED;\n"
                           "}\n"
                           "".replace("WINDOWTITLE", self.window_title.replace(" ", "\\ ")))

        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName(u"label")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setTextFormat(QtCore.Qt.MarkdownText)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)
        self.label.setFont(self._font)

        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setFont(self._font)
        self.pushButton.clicked.connect(self.close)

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")

        self.leftSpacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                                QtWidgets.QSizePolicy.Minimum)
        self.leftMidSpacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                                QtWidgets.QSizePolicy.Minimum)
        self.rightMidSpacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                                QtWidgets.QSizePolicy.Minimum)
        self.rightSpacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                                QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(self.leftSpacer, 1, 0, 1, 1)
        self.gridLayout.addItem(self.leftMidSpacer, 1, 1, 1, 1)
        self.gridLayout.addWidget(self.pushButton, 1, 2, 1, 1)
        self.gridLayout.addWidget(self.label, 0, 1, 1, 3)
        self.gridLayout.addItem(self.rightMidSpacer, 1, 3, 1, 1)
        self.gridLayout.addItem(self.rightSpacer, 1, 4, 1, 1)

        self.retranslate_ui()

        QtCore.QMetaObject.connectSlotsByName(self)
