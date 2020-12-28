from secrets import token_bytes
from uuid import UUID

from clientside.user import User


class Message:

    def __init__(self, **kwargs):
        self.id: UUID = UUID(bytes=token_bytes(16))

        self.content: str = kwargs["content"]
        self.sender: User = kwargs["user"]

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    @property
    def sender(self):
        return self._sender

    @sender.setter
    def sender(self, value):
        if isinstance(value, User):
            self._sender = value
        else:
            raise TypeError(f"{value} is not type {User.__name__!r}")
