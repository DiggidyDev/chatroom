import os
import sys

if os.path.isfile("client.exe"):
    os.remove("client.exe")

if os.path.isfile("client-new.exe"):
    os.rename("client-new.exe", "client.exe")

os.execl("client.exe", *([sys.executable]+sys.argv))
