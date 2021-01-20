from PyQt5 import QtWidgets, QtCore, QtGui

from clientside import config
from utils.fmt import is_valid_section_name

CFG_NAMES = {
    "text_colour": "Text",
    "line_colour": "Line colours",
    "tb_bg_colour": "Toolbar colour",
    "btn_bg_colour": "Button colour",
    "main_bg_colour": "Background",
    "menu_bg_colour": "Menu colour",
    "btn_text_colour": "Button text",
    "msg_box_bg_colour": "Message-edit background",
    "scroll_bar_colour": "Scrollbar",
    "msg_list_bg_colour": "Message list",
    "user_list_bg_colour": "Userlist",
    "menu_slctd_bg_colour": "Menu hover",
    "scroll_bar_bg_colour": "Scrollbar background",
    "menu_slctd_text_colour": "Menu text hover",
    "user_list_slctd_bg_colour": "Userlist hover"
}


class ColourTable(QtWidgets.QTableWidget):
    """
    The UI for selecting and setting colours when
    creating a new theme. You have the ability to
    name the new theme, but cannot overwrite any
    existing themes.

    In the future I might add an overwrite option
    if a theme already exists.
    """

    def __init__(self, parent):
        super().__init__(parent)

        CFG = config.get_current_theme()

        self._parent = parent

        self.setObjectName("self")

        self.setRowCount(len(CFG_NAMES))
        self.setColumnCount(1)

        self.setVerticalHeaderLabels(CFG_NAMES.values())

        # Prevent user from resizing columns and rows
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        for i, k in enumerate(CFG_NAMES.keys()):
            try:
                cur_colour = CFG[k]

                cell = QtWidgets.QTableWidgetItem()
                cell.setBackground(QtGui.QColor(cur_colour))
                cell.setFlags(QtCore.Qt.ItemIsEnabled)
                cell.setToolTip("Double-click me to set my colour!")

                self.setItem(i, 0, cell)
            except Exception as e:
                print(e)

        self.setStyleSheet("""
            QTableWidget {
                border: 2px solid black;
            }
        """)

    def mouseDoubleClickEvent(self, e) -> None:
        new_colour = QtWidgets.QColorDialog.getColor()

        changed_colour = sum((new_colour.hue(), new_colour.saturation(),
                              new_colour.red(), new_colour.green(),
                              new_colour.blue(), new_colour.value())) != 0

        if changed_colour:
            self.currentItem().setBackground(new_colour)

        super().mouseDoubleClickEvent(e)


class ThemeCreator(QtWidgets.QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.setup_ui()

        ThemeUpdater().to_current_theme(self)

    def set_color(self):
        try:
            from .menu import ThemeAction

            is_valid_section_name(self.inputName.text())

            items = (self.tableWidget.item(i, 0) for i in range(self.tableWidget.rowCount()))
            elements = {k: i.background().color().name() for k, i in zip(CFG_NAMES.keys(), items)}
            print(f"{elements}".replace("'", '"').replace(",", ",\n"))
            config.add_theme(name=self.inputName.text(), **elements)

            action_btn_theme = ThemeAction(self._parent)
            action_btn_theme.setText(self.inputName.text())
            action_btn_theme.setup_trigger()
            self._parent.menuThemes.insertAction(self._parent.menuThemes.actions()[-2], action_btn_theme)

            self.close()
        except (NameError, LookupError) as err:
            from .info import CustomDialog

            errdialog = CustomDialog(window_title=f"{type(err).__name__}",
                                     message=f"{err}",
                                     font=self._parent.current_font)
            errdialog.exec_()

    def setup_ui(self):
        if not self.objectName():
            self.setObjectName("self")

        self.setFixedSize(400, 500)

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")

        self.tableWidget = ColourTable(self)

        __qtablewidgetitem = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)

        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)

        self.gridLayout.addWidget(self.tableWidget, 1, 0, 4, 1)

        self.inputName = QtWidgets.QLineEdit(self)
        self.inputName.setPlaceholderText("Enter theme name...")
        self.inputName.setMaxLength(15)

        self.gridLayout.addWidget(self.inputName, 3, 1, 1, 1)

        self.btnConfirm = QtWidgets.QPushButton(self)
        self.btnConfirm.setObjectName("pushButton")
        self.btnConfirm.clicked.connect(self.set_color)

        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.Fixed)

        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.btnConfirm.sizePolicy().hasHeightForWidth())
        self.btnConfirm.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.btnConfirm, 2, 1, 1, 1)

        self.retranslate_ui()

        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslate_ui(self):
        self.setWindowTitle(
            QtCore.QCoreApplication.translate("self", "Theme Creator", None))

        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(
            QtCore.QCoreApplication.translate("self", "Colour", None))

        print(self.btnConfirm)
        self.btnConfirm.setText(
            QtCore.QCoreApplication.translate("self", "Create theme", None))


class ThemeUpdater:

    @staticmethod
    def setup_themes(cls, **cfg):
        text_colour = cfg["text_colour"]
        line_colour = cfg["line_colour"]
        tb_bg_colour = cfg["tb_bg_colour"]
        btn_bg_colour = cfg["btn_bg_colour"]
        main_bg_colour = cfg["main_bg_colour"]
        menu_bg_colour = cfg["menu_bg_colour"]
        btn_text_colour = cfg["btn_text_colour"]
        msg_box_bg_colour = cfg["msg_box_bg_colour"]
        scroll_bar_colour = cfg["scroll_bar_colour"]
        msg_list_bg_colour = cfg["msg_list_bg_colour"]
        user_list_bg_colour = cfg["user_list_bg_colour"]
        menu_slctd_bg_colour = cfg["menu_slctd_bg_colour"]
        scroll_bar_bg_colour = cfg["scroll_bar_bg_colour"]
        menu_slctd_text_colour = cfg["menu_slctd_text_colour"]
        user_list_slctd_bg_colour = cfg["user_list_slctd_bg_colour"]

        # INFO: Main client CSS
        cls.setStyleSheet("QMainWindow, QDialog {\n"
                          f"    background-color: {main_bg_colour};\n"
                          "}\n"
                          "QLabel, QCheckBox {\n"
                          f"    color: {text_colour}"
                          "}\n"
                          "QWidget {\n"
                          "    outline: none;\n"
                          "}\n"
                          "\n"
                          "QMenuBar {\n"
                          f"    background-color: {tb_bg_colour};\n"
                          f"    border-bottom: 1px solid {line_colour};\n"
                          f"    color: {text_colour};\n"
                          "    font-family: \"Microsoft New Tai Lue\";\n"
                          "}\n"
                          "\n"
                          "QLineEdit {\n"
                          f"    background-color: {msg_box_bg_colour};\n"
                          f"    color: {text_colour};\n"
                          f"    border: none;\n"
                          "}\n"
                          "QLineEdit::disabled {\n"
                          f"    background-color: {menu_bg_colour};"
                          "}\n"
                          "QPlainTextEdit {\n"
                          f"    background-color: {msg_box_bg_colour};\n"
                          f"    color: {text_colour};\n"
                          "    font-weight: bold;\n"
                          "}\n"
                          "QPushButton {\n"
                          f"    background-color: {btn_bg_colour};\n"
                          f"    color: {btn_text_colour};\n"
                          "    font-weight: bold;\n"
                          "}\n"
                          "QMenu {\n"
                          f"    border: 1px solid {line_colour};\n"
                          f"    background-color: {menu_bg_colour};\n"
                          f"    color: {text_colour};\n"
                          "    font-family: \"Microsoft New Tai Lue\";\n"
                          f"    selection-background-color: {menu_slctd_bg_colour};\n"
                          f"    selection-color: {menu_slctd_text_colour};\n"
                          "}\n"
                          "\n"
                          "QScrollBar {\n"
                          "    background: rgba(0, 0, 0, 0);\n"
                          "    padding: 1px;\n"
                          "    width: 9px;\n"
                          "}\n"
                          "\n"
                          "QScrollBar::handle {\n"
                          f"    background: {scroll_bar_colour};\n"
                          f"    border: 1px solid {scroll_bar_colour};\n"
                          "    border-radius: 3px;\n"
                          "}\n"
                          "\n"
                          "QScrollBar::add-page, QScrollBar::sub-page {\n"
                          "    background: rgba(0, 0, 0, 0);\n"
                          "}\n"
                          "\n"
                          "QScrollBar::sub-line, QScrollBar::add-line {\n"
                          "    height: 0;\n"
                          "}")

        if hasattr(cls, "msgList"):
            # INFO: Menubar CSS
            cls.menubar.setStyleSheet("QMenuBar::item:selected {\n"
                                      f"    background-color: {menu_slctd_bg_colour};\n"
                                      f"    color: {menu_slctd_text_colour};\n"
                                      "}\n")

            # INFO: Buttons, containers CSS
            cls.centralwidget.setStyleSheet("\n"
                                            "QGroupBox {\n"
                                            f"    color: {text_colour};\n"
                                            f"    border: 1px solid {line_colour};\n"
                                            "    border-radius: 5px;\n"
                                            "    margin-top: 2ex;\n"
                                            "    font-weight: bold;\n"
                                            "}\n"
                                            "QGroupBox::title {\n"
                                            "    subcontrol-origin: margin;\n"
                                            "    subcontrol-position: top center;\n"
                                            "    padding: 0 3px;\n"
                                            "}\n"
                                            "QLineEdit {\n"
                                            f"    border: 1px solid {line_colour};\n"
                                            "    border-radius: 4px;\n"
                                            "}\n"
                                            "QWidget {\n"
                                            "    font-family: \"Microsoft New Tai Lue\";\n"
                                            "}")

            # INFO: Message send CSS
            cls.sendMsgBox.setStyleSheet("QFrame {\n"
                                         f"    border: 1px solid {line_colour};\n"
                                         "    border-radius: 6px;\n"
                                         "}")

            # INFO: Message container scrollbar CSS
            cls.msgList.setStyleSheet("QListView {\n"
                                      f"    alternate-background-color: {menu_slctd_bg_colour};\n"
                                      f"    background-color: {msg_list_bg_colour};\n"
                                      f"    color: {text_colour};\n"
                                      "}\n"
                                      "QListView::item {\n"
                                      "    border: none;\n"
                                      "}\n"
                                      "QFrame {\n"
                                      f"    border: 1px solid {line_colour};\n"
                                      "    border-radius: 6px;\n"
                                      "    outline: none;\n"
                                      "}\n"
                                      "\n"
                                      "QScrollBar {\n"
                                      f"    background-color: {scroll_bar_bg_colour};\n"
                                      "}")

            # INFO: Dotted-border removal CSS
            cls.msgListGroupBox.setStyleSheet("QWidget {\n"
                                              "    outline: none;\n"
                                              "}")

            # INFO: Room selection CSS
            cls.chatroomComboBox.setStyleSheet("QComboBox {\n"
                                               f"    background-color: {menu_bg_colour};\n"
                                               f"    color: {text_colour};\n"
                                               f"    font-family: \"Microsoft New Tai Lue\";"
                                               f"    selection-background-color: {menu_slctd_bg_colour};\n"
                                               f"    selection-color: {menu_slctd_text_colour}\n"
                                               "}\n"
                                               "\n"
                                               "QListView {\n"
                                               f"    background-color: {menu_bg_colour};\n"
                                               f"    color: {text_colour};\n"
                                               "    outline: none;\n"
                                               f"    selection-background-color: {menu_slctd_bg_colour};\n"
                                               f"    selection-color: {menu_slctd_text_colour};\n"
                                               "}")

            # INFO: User list and item CSS
            cls.userList.setStyleSheet("QListView {\n"
                                       f"    alternate-background-color: {menu_slctd_bg_colour};\n"
                                       f"    background-color: {user_list_bg_colour};\n"
                                       f"    color: {text_colour};\n"
                                       f"    selection-color: {menu_slctd_text_colour};\n"
                                       "}\n"
                                       "QListView::item {\n"
                                       "    border: none;\n"
                                       "}\n"
                                       "QFrame {\n"
                                       f"    border: 1px solid {line_colour};\n"
                                       "    border-radius: 6px;\n"
                                       "    outline: none;\n"
                                       "}\n"
                                       "#userList::item:hover {\n"
                                       f"    border: 1px solid {user_list_bg_colour};\n"
                                       "    border-radius: 5px;\n"
                                       f"    color: {user_list_bg_colour};\n"
                                       f"    background-color: {user_list_slctd_bg_colour};\n"
                                       "}\n"
                                       "#userList::item:selected {\n"
                                       f"    border: 1px solid {user_list_bg_colour};\n"
                                       "    border-radius:5px;\n"
                                       f"    background-color: {main_bg_colour};\n"
                                       "}\n"
                                       "QScrollBar {\n"
                                       f"    background-color: {scroll_bar_bg_colour};\n"
                                       "}")

    def to_current_theme(self, window):
        cfg = config.get_current_theme()
        self.setup_themes(window, **cfg)

    def update_theme(self, cls, name):
        try:
            config.set_current_theme(name)
            cfg = config.get_current_theme()
            self.setup_themes(cls, **cfg)
        except Exception as e:
            print(e)
