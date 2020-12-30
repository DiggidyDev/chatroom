import types
from secrets import token_bytes
from typing import Tuple, Union
from uuid import UUID

from bases import _BaseObj

Activity = types.SimpleNamespace(ONLINE=1, OFFLINE=0)


class User(_BaseObj):

    _email: Union[str, None]

    def __init__(self, nickname: str = None,
                 existing_data: Union[tuple, bool] = False,
                 registered_user: bool = False):
        if not existing_data:
            self.anonymous = not registered_user

            self.blocked_users = []
            self.nickname = nickname
            self.username = nickname if registered_user else None

            self.status = Activity.ONLINE
            self.uuid = UUID(bytes=token_bytes(16))
        else:
            self.__set_up_existing_user(existing_data)

    def __set_up_existing_user(self, data):
        self.anonymous = False
        self.friends = []
        self.online_friends = []

        self.blocked_users = data[4]
        self.friend_requests = data[6]
        self.friends = data[3]
        self.nickname = data[5]
        self.username = data[2]
        self.status = data[0]
        self.email = data[7]
        self.uuid = data[1]

        return self

    def __str__(self):
        return self.username if not self.nickname else self.nickname

    def __int__(self):
        return len(self.friends) if not self.is_anonymous() else None

    @property
    def name(self) -> str:
        return self.__str__()

    @property
    def status(self) -> Activity:
        return self._status

    @status.setter
    def status(self, value):
        if isinstance(value, int):
            self._status = value
        else:
            raise TypeError(f"{value!r} is not a valid type {int.__name__!r} for status")

    @property
    def uuid(self) -> UUID:
        return self._UUID

    @uuid.setter
    def uuid(self, value):
        self._UUID = value

    @classmethod
    def from_existing_data(cls, data: Tuple) -> "User":
        return cls().__set_up_existing_user(data)

    def get_email(self) -> str:
        return self._email if not self.is_anonymous() else None

    def get_mutual_friends(self, user) -> list:
        pass

    def get_status(self) -> Activity:
        return self._status

    def is_anonymous(self) -> bool:
        return self.anonymous

    def is_blocked(self, user) -> None:
        return

    def is_friends_with(self, user) -> None:
        return

    def remove_friend(self, user):
        pass

    def send_friend_request(self, user):
        pass

    def set_email(self, email: str):
        self._email = email if not self.is_anonymous() else None

    def set_nickname(self, new_nickname: str = None):
        return

    def unblock(self, user):
        pass
