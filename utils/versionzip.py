def get_version() -> str:
    f = open("version.txt", "r+")
    return f.read()


def set_version(version: str):
    f = open("version.txt", "w+")
    f.write(version)
