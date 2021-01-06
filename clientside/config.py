import configparser
import clientside

from utils.fmt import is_valid_section_name

parser = configparser.ConfigParser()
parser.read(clientside.__file__[:-11] + "config.ini")


def add_theme(*, name: str, **elements):
    is_valid_section_name(name)
    section = "THEME." + name

    if parser.has_section(section):
        raise LookupError(f"Section {section!r} already exists")

    parser[section] = {**elements}
    write_to_file()


def edit_theme(*, name: str, **elements):
    is_valid_section_name(name)
    section = "THEME." + name

    if not parser.has_section(section):
        raise LookupError(f"Section {section!r} wasn't found")

    parser[section] = {**elements}
    write_to_file()


def get_theme(name):
    section = "THEME." + name

    if parser.has_section(section=section):
        return dict(parser[section])


def get_theme_names():
    for i in parser.sections():
        if i.startswith("THEME."):
            yield i


def write_to_file():
    with open("config.ini", "w") as f:
        parser.write(f)


for i in get_theme_names():
    print(i)

