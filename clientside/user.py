import types
from uuid import UUID
from secrets import token_bytes
from typing import Union

from utils.debug import debug

Activity = types.SimpleNamespace(ONLINE=1, OFFLINE=0)


class User:

    _email: Union[str, None]

    def __init__(self, nickname: str = None,
                 existing_data: Union[tuple, bool] = False,
                 registered_user: bool = False):
        if not existing_data:
            self.anonymous = not registered_user

            self.blocked_users = []
            self.nickname = nickname
            self.username = nickname if registered_user else None

            self._status = Activity.ONLINE
            self._UUID = UUID(bytes=token_bytes(16))
        else:
            self.__set_up_existing_user(existing_data)

    def __set_up_existing_user(self, userdata):
        self.anonymous = False
        self.friends = []
        self.online_friends = []

        self._UUID = userdata[1]
        self.blocked_users = userdata[4]
        self.friend_requests = userdata[6]
        self.friends = userdata[3]
        self.nickname = userdata[5]
        self.set_status(userdata[0])
        self.username = userdata[2]
        self.set_email(userdata[7])

    def __str__(self):
        return self.username if not self.nickname else self.nickname

    def __int__(self):
        return len(self.friends) if not self.is_anonymous() else None

    @property
    def name(self) -> str:
        return self.__str__()

    def get_email(self) -> str:
        return self._email if not self.is_anonymous() else None

    def get_mutual_friends(self, user) -> list:
        pass

    def get_status(self) -> Activity:
        return self._status

    def get_uuid(self) -> UUID:
        """
        :return: Universally unique Identifier
        """
        return self._UUID

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

    @debug(verbose=False)
    def set_status(self, state: str):
        pass

    def unblock(self, user):
        pass
