import types
from secrets import token_bytes
from typing import Iterable, List, Tuple, Union
from uuid import UUID

from bases import BaseObj, TABLE_COLUMNS_USR
from room import Room

Activity = types.SimpleNamespace(ONLINE=1, OFFLINE=0)


class User(BaseObj):

    TABLE_COLUMNS = TABLE_COLUMNS_USR

    _email: Union[str, None]
    _rooms: None

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

            super().__init__()
        else:
            self.__set_up_existing_user(existing_data)

    def __set_up_existing_user(self, data):
        self.anonymous = data[7] is None
        self.online_friends = []

        self.blocked_users = data[4]
        self.friend_requests = data[6]
        self.friends = data[3]
        self.nickname = data[5]
        self.username = data[2]
        self._rooms = data[8]
        self.status = data[0]
        self._email = data[7]
        self.uuid = data[1]

        return self

    def __str__(self):
        return self.username if not self.nickname else self.nickname

    def __int__(self):
        return len(self.friends) if not self.is_anonymous() else None

    @property
    def email(self):
        return self._email if not self.is_anonymous() else None

    @email.setter
    def email(self, value):
        self._email = value if not self.is_anonymous() else None

    @property
    def name(self) -> str:
        return self.__str__()

    @property
    def status(self) -> Activity:
        return self._status

    @status.setter
    def status(self, value):
        if value is None:
            value = 1
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

    @property
    def rooms(self) -> List[Room]:
        return self._rooms

    @rooms.setter
    def rooms(self, value: Iterable[Room]):
        self._rooms = value

    def send_friend_request(self, user):
        pass

    def set_nickname(self, new_nickname: str = None):
        return

    def unblock(self, user):
        pass
