import pickle
import socket

from user import User
from utils.debug import debug


PORT = 65501
HOST = "127.0.0.1"

u = User("Nickname")


@debug(verbose=True)
def connect():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        initialcontent = {"content": "Initial connection.", "user": u}
        s.sendall(pickle.dumps(initialcontent))
        while True:
            data = pickle.loads(s.recv(1024))
            print(f"Received: {pickle.loads(data)}")

            # Wait for user to enter their message
            message = input("CMD> ")
            tosend = format_content(content=message, user=u)
            if tosend:
                s.sendall(pickle.dumps(tosend))

#@debug(verbose=False)
def format_content(**kwargs):
    """
    Correctly format content for outgoing
    :param kwargs:
    :return:
    """
    struct = {
        "content": kwargs["content"],
        "user": kwargs["user"]
    }

    return struct



if __name__ == "__main__":
    connect()
