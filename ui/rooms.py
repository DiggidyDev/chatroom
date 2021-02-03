from typing import List

from PyQt5 import QtCore, QtGui, QtWidgets

from room import Room
from .themes import ThemeUpdater


style = ThemeUpdater()


class RoomDropdown(QtWidgets.QComboBox):

    rooms: List[Room]

    def __init__(self, parent, *, anonymous: bool = None):
        """
        :param parent:
        :param anonymous: Restrict the user from joining or creating
            rooms if they're anonymous.
        """
        super().__init__(parent)

        self._parent = parent
        self.previous_room = None

        self.anonymous = anonymous
        self.rooms = []

        style.to_current_theme(self)

        if not anonymous:
            self.currentIndexChanged.connect(self.room_handler)
            self.insertSeparator(0)
            self.addItem("Create room...")
            self.addItem("Join room...")

    def __len__(self):
        return len(self.rooms)

    # TODO: Add limit for future (100 rooms? 50?)
    def add_rooms(self, *rooms: Room):
        if self.anonymous:
            if len(self) > 0:
                raise PermissionError("Anonymous users cannot join new rooms.")

            self.addItem(rooms[0].name)
            self.setCurrentIndex(0)

        else:
            # Set the flag for selecting the default room
            # at startup
            initial_creation = len(self) == 0

            for room in rooms:
                self.rooms.append(room)
                self.insertItem(len(self) - 3, room.name)

            if initial_creation:
                # Prevent the current selected
                # dropdown item from being blank
                self.setCurrentIndex(0)

    def room_handler(self):
        if self.currentText() == "Create room...":
            room_dialog = CreateRoomDialog(self._parent, self)
            room_dialog.exec_()
        elif self.currentText() == "Join room...":
            print("JOINING ROOM")
        elif 0 <= self.currentIndex() < len(self):
            print(self.rooms[self.currentIndex()].name)
            self.previous_room = self.currentIndex()

    @property
    def rooms(self) -> List[Room]:
        return self._rooms

    @rooms.setter
    def rooms(self, value):
        self._rooms = value


# TODO: THIS SHIT
class CreateRoomDialog(QtWidgets.QDialog):
    """
    The popup dialog to appear when a user attempts to
    create a new room.
    """

    def __init__(self, parent, room_dropdown: RoomDropdown):
        super().__init__(parent)

        self.room_dropdown = room_dropdown
        self.setup_ui()

        style.to_current_theme(self)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        # CHECK IF NEW ROOM CREATION WAS SUCCESSFUL (THEN SWITCH TO THAT ROOM INSTEAD OF PREVIOUS)
        self.room_dropdown.setCurrentIndex(self.room_dropdown.previous_room)

    def display_username_input(self):
        self.inputUsername.setVisible(not self.inputUsername.isVisible())

    def setup_ui(self):
        self.setObjectName("self")

        self.resize(461, 238)
        self.setMinimumSize(QtCore.QSize(461, 238))
        self.setMaximumSize(QtCore.QSize(461, 238))

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonAnon = QtWidgets.QPushButton(self)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonAnon.sizePolicy().hasHeightForWidth())

        self.buttonAnon.setSizePolicy(sizePolicy)
        self.buttonAnon.setObjectName("buttonAnon")
        self.gridLayout.addWidget(self.buttonAnon, 6, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 19,
                                           QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Preferred)
        self.gridLayout.addItem(spacerItem, 5, 0, 1, 1)

        self.inputNickname = QtWidgets.QLineEdit(self)
        self.inputNickname.setEnabled(True)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.inputNickname.sizePolicy().hasHeightForWidth())

        self.inputNickname.setSizePolicy(sizePolicy)
        self.inputNickname.setText("")
        self.inputNickname.setObjectName("inputNickname")
        self.inputNickname.setMaxLength(10)

        self.gridLayout.addWidget(self.inputNickname, 6, 0, 1, 1)
        self.labelContAnon = QtWidgets.QLabel(self)
        self.labelContAnon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelContAnon.setObjectName("labelContAnon")
        self.gridLayout.addWidget(self.labelContAnon, 2, 0, 1, 2)
        self.buttonLoginRegister = QtWidgets.QPushButton(self)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonLoginRegister.sizePolicy().hasHeightForWidth())

        self.buttonLoginRegister.setSizePolicy(sizePolicy)
        self.buttonLoginRegister.setObjectName("buttonLoginRegister")
        self.gridLayout.addWidget(self.buttonLoginRegister, 7, 5, 1, 1)

        self.inputEmail = QtWidgets.QLineEdit()
        self.inputEmail.setObjectName("inputEmail")
        self.inputEmail.setPlaceholderText("Email")
        self.gridLayout.addWidget(self.inputEmail, 6, 4, 1, 2)

        self.inputUsername = QtWidgets.QLineEdit(self)
        self.inputUsername.setObjectName("inputUsername")
        self.inputUsername.setMaxLength(24)
        self.gridLayout.addWidget(self.inputUsername, 5, 4, 1, 2)
        self.inputPassword = QtWidgets.QLineEdit(self)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.inputPassword.sizePolicy().hasHeightForWidth())

        self.inputPassword.setSizePolicy(sizePolicy)
        self.inputPassword.setFrame(True)
        self.inputPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.inputPassword.setObjectName("inputPassword")

        self.gridLayout.addWidget(self.inputPassword, 7, 4, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40,
                                            QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 8, 0, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40,
                                            QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Preferred)
        self.gridLayout.addItem(spacerItem2, 0, 1, 1, 1)
        self.verticalDivider = QtWidgets.QFrame(self)
        self.verticalDivider.setFrameShape(QtWidgets.QFrame.VLine)
        self.verticalDivider.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalDivider.setObjectName("verticalDivider")
        self.gridLayout.addWidget(self.verticalDivider, 0, 2, 9, 1)
        self.toggleExistingAcc = QtWidgets.QCheckBox(self)
        self.toggleExistingAcc.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.toggleExistingAcc.setObjectName("toggleExistingAcc")
        self.gridLayout.addWidget(self.toggleExistingAcc, 2, 4, 1, 2)

        self.retranslate_ui()

        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslate_ui(self):
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("self", "Create Room"))
        self.buttonAnon.setText(_translate("self", "Go!"))
        self.inputNickname.setPlaceholderText(_translate("self", "Nickname"))
        self.labelContAnon.setText(_translate("self", "Continue anonymously"))
        self.buttonLoginRegister.setText(_translate("self", "Register"))
        self.inputUsername.setPlaceholderText(_translate("self", "Username"))
        self.inputPassword.setPlaceholderText(_translate("self", "Password"))
        self.toggleExistingAcc.setText(
            _translate("self", "Already got an account?            "))

        self.inputNickname.setTabOrder(self.inputNickname, self.buttonAnon)
        self.buttonAnon.setTabOrder(self.buttonAnon, self.toggleExistingAcc)
        self.toggleExistingAcc.setTabOrder(self.toggleExistingAcc, self.inputUsername)
        self.inputUsername.setTabOrder(self.inputUsername, self.inputEmail)
        self.inputEmail.setTabOrder(self.inputEmail, self.inputPassword)
        self.inputPassword.setTabOrder(self.inputPassword, self.buttonLoginRegister)