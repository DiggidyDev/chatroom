# Set the current application's download type
# based on the modules available to be imported
try:
    from utils.versionbin import get_version, set_version
    DL_TYPE = "exe"
except ImportError:
    from utils.versionzip import get_version, set_version
    DL_TYPE = "zip"


def check_for_updates() -> bool:
    """
    Will return True if any updates are found.

    Using the queried version from the website, this checks
    whether the current client's version is up-to-date. If
    it isn't, it will [PERFORM UPDATE].
    :return:
    """

    from utils.versionbin import get_version

    if get_live_version() != get_version():
        return True
    return False


def get_live_version() -> str:
    """
    Fetches the current version of the client being hosted
    on the website. This will be used to check for new versions
    and auto-updating the application.

    :return:
    """
    import json  # For converting the requested string into JSON
    import urllib.request  # Querying for the current live version

    live_version = json.loads(urllib.request.urlopen("https://diggydev.co.uk/chatroom/version.json").read())["live_bin"]

    return live_version


def start_download() -> bool:
    if DL_TYPE == "exe":
        try:
            import os
            import requests

            CHNK_SIZE = 2**20

            if not os.path.isfile("updater.exe"):
                updater = requests.get(f"https://diggydev.co.uk/chatroom/updater.exe", stream=True)

                with open("updater.exe", "wb") as up_exe:
                    for chnk in updater.iter_content(chunk_size=CHNK_SIZE):
                        up_exe.write(chnk)

                updater.close()

            new_client = requests.get(f"https://diggydev.co.uk/chatroom/client.{DL_TYPE}", stream=True)
            print(new_client)
            with open("client-new.exe", "wb") as exe:
                for chnk in new_client.iter_content(chunk_size=CHNK_SIZE):  # 1 MiB
                    exe.write(chnk)

            new_client.close()
        except Exception as e:
            print(e)
        finally:
            import os
            import sys

            set_version(get_live_version())

            os.execl("updater.exe", *([sys.executable] + sys.argv))
    if DL_TYPE == "zip":
        from zipfile import ZipFile

        with ZipFile("client.zip", "r") as _zip:
            _zip.extractall()

    return True
