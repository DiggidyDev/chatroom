import configparser
import clientside

from utils.fmt import is_valid_section_name

parser = configparser.ConfigParser()


# TODO: ADD MAX THEME LIMIT
def add_theme(*, name: str, **elements):
    update_parser()
    is_valid_section_name(name)
    section = "THEME." + name

    if parser.has_section(section):
        raise LookupError(f"Theme {name!r} already exists")

    parser[section] = {**elements}
    write_to_file()


def check_for_default_themes():
    update_parser()
    if not parser.has_section("THEME.Default"):
        parser["THEME.Default"] = {
            "text_colour": "white",
            "line_colour": "white",
            "tb_bg_colour": "rgb(56, 40, 80)",
            "btn_bg_colour": "rgb(56, 40, 80)",
            "main_bg_colour": "#A054ED",
            "menu_bg_colour": "rgb(51, 35, 75)",
            "btn_text_colour": "white",
            "msg_box_bg_colour": "rgb(56, 40, 80)",
            "scroll_bar_colour": "white",
            "msg_list_bg_colour": "rgb(56, 40, 80)",
            "user_list_bg_colour": "rgb(56, 40, 80)",
            "menu_slctd_bg_colour": "black",
            "scroll_bar_bg_colour": "rgb(56, 40, 80)",
            "menu_slctd_text_colour": "#ABE25F",
            "user_list_slctd_bg_colour": "black"
        }
        write_to_file()
    if not parser.has_section("THEME.Dark"):
        parser["THEME.Dark"] = {
            "text_colour": "white",
            "line_colour": "#1d1d1d",
            "tb_bg_colour": "#8f5d92",
            "btn_bg_colour": "#5d525d",
            "main_bg_colour": "#1d1d1d",
            "menu_bg_colour": "#373737",
            "btn_text_colour": "white",
            "msg_box_bg_colour": "#5d525d",
            "scroll_bar_colour": "#504e50",
            "msg_list_bg_colour": "#352735",
            "user_list_bg_colour": "#352735",
            "menu_slctd_bg_colour": "#2a282a",
            "scroll_bar_bg_colour": "#352735",
            "menu_slctd_text_colour": "#ae98ae",
            "user_list_slctd_bg_colour": "white"
        }
        write_to_file()
    if not parser.has_section("THEME.Clown"):
        parser["THEME.Clown"] = {
            "text_colour": "#000000",
            "line_colour": "#00ff00",
            "tb_bg_colour": "#00aaff",
            "btn_bg_colour": "#55aa00",
            "main_bg_colour": "#ff55ff",
            "menu_bg_colour": "#ffff00",
            "btn_text_colour": "#ffffff",
            "msg_box_bg_colour": "#ffaa7f",
            "scroll_bar_colour": "#ff007f",
            "msg_list_bg_colour": "#00aa7f",
            "user_list_bg_colour": "#ffaa00",
            "menu_slctd_bg_colour": "#aaaaff",
            "scroll_bar_bg_colour": "#555500",
            "menu_slctd_text_colour": "#aaff00",
            "user_list_slctd_bg_colour": "#ffffff"
        }
        write_to_file()
    if not parser.has_section("THEME.Light"):
        parser["THEME.Light"] = {
            "text_colour": "#000000",
            "line_colour": "#000000",
            "tb_bg_colour": "#ffffff",
            "btn_bg_colour": "#f7beff",
            "main_bg_colour": "#e3d5e7",
            "menu_bg_colour": "#ffc6c7",
            "btn_text_colour": "#370039",
            "msg_box_bg_colour": "#ffc0c1",
            "scroll_bar_colour": "#3b002d",
            "msg_list_bg_colour": "#ffcfd0",
            "user_list_bg_colour": "#ffd3d4",
            "menu_slctd_bg_colour": "#780002",
            "scroll_bar_bg_colour": "#ffffff",
            "menu_slctd_text_colour": "#ffffff",
            "user_list_slctd_bg_colour": "#ffffff"
        }


def edit_theme(*, name: str, **elements):
    update_parser()
    is_valid_section_name(name)
    section = "THEME." + name

    if not parser.has_section(section):
        raise LookupError(f"Section {section!r} wasn't found")

    parser[section] = {**elements}
    write_to_file()


def get_current_theme() -> dict:
    update_parser()
    if not parser.has_section("PROFILE"):
        parser["PROFILE"] = {"current_theme": "Default"}
        write_to_file()

    if parser.has_section("THEME." + parser["PROFILE"]["current_theme"]):
        return get_theme(parser["PROFILE"]["current_theme"])
    check_for_default_themes()
    return get_theme(parser["PROFILE"]["current_theme"])


def get_theme(name):
    update_parser()
    section = "THEME." + name

    if parser.has_section(section=section):
        return dict(parser[section])


def get_theme_names():
    update_parser()
    for section_name in parser.sections():
        if section_name.startswith("THEME."):
            yield section_name


def set_current_theme(name):
    update_parser()
    section_name = "THEME." + name

    if parser.has_section(section_name):
        parser["PROFILE"]["current_theme"] = name
        write_to_file()


def update_parser():
    parser.read(clientside.__file__[:-11] + "config.ini")


def write_to_file():
    with open("config.ini", "w") as f:
        parser.write(f)


check_for_default_themes()
