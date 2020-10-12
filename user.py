import enum

from utils.debug import debug


class Activity(enum.Enum):
    ONLINE = "online"


print(Activity.ONLINE)


class User:

    def __init__(self, nickname: str = None):
        self.blocked_users = []
        self.friends = []
        self.nickname = nickname
        self.online_friends = []
        self.username = None

        self._status = Activity.ONLINE
        self._UUID = self._generate_new_uuid()

    def __str__(self):
        return self.username if not self.nickname else self.nickname

    def __int__(self):
        return len(self.friends)

    @staticmethod
    def _generate_new_uuid() -> int:
        return 5

    def get_mutual_friends(self, user) -> list:
        pass

    def get_status(self):
        return self._status

    def is_blocked(self, user) -> None:
        return

    def is_friends_with(self, user) -> None:
        return

    def remove_friend(self, user):
        pass

    def send_friend_request(self, user):
        pass

    def set_nickname(self, new_nickname: str = None):
        return

    @debug(verbose=False)
    def set_status(self, state: str):
        pass

    def unblock(self, user):
        pass
