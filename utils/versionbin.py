def get_version() -> str:
    import pkgutil

    v_bin = pkgutil.get_data("clientside", "version.txt")

    return v_bin.decode("utf-8")


def set_version(version: str):
    import clientside

    f = open(clientside.__file__[:-12] + "version.txt", "w")
    f.write(version)
    f.close()
