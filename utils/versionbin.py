def get_version() -> str:
    f = open("version.txt", "r+")
    contents = f.read()
    f.close()
    return contents


def set_version(version: str):
    f = open("version.txt", "w+")
    f.write(version)
    f.close()
