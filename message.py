import pickle
from secrets import token_bytes
from typing import Optional, Union
from uuid import UUID

from bases import _BaseObj
from user import User


class Message(_BaseObj):
    TABLE_COLUMNS = (
        "content", "message_uuid", "room_uuid", "sender_uuid", "system_message"
    )

    def __init__(self,
                 content: str,
                 system_message: bool,
                 create: str = None,
                 data: ... = None,
                 datatype: str = None,
                 get: str = None,
                 message_uuid: Optional[str] = None,
                 room: str = None,
                 sender: Union[User, str] = None):
        self._content = content
        self._system_message = system_message

        self.create = create
        self.data = data
        self.datatype = datatype
        self.get = get
        self._room = room
        self._sender = sender
        self._uuid: UUID = UUID(bytes=token_bytes(16)) if message_uuid is None else UUID(message_uuid)

    def __bytes__(self):
        return pickle.dumps(dict(self))

    def __iter__(self):
        given_args = {k: v for k, v in vars(Message).items()}
        given_args.update(vars(self))
        for k, v in sorted(
                [(k, v) for k, v in given_args.items() if k in self.__class_args() and v is not None],
                key=lambda x: x[0]
        ):
            if k.startswith("_"):
                k = k[1:]
            yield k, v

    def __str__(self):
        return self.content

    @staticmethod
    def data_format_from_tuple(t: tuple) -> dict:
        return {k: v for k, v in zip(Message.TABLE_COLUMNS, t)}

    @classmethod
    def from_uuid(cls, **data):
        return cls(**data)

    @classmethod
    def __class_args(cls):
        return cls.__init__.__code__.co_names

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, value):
        self._room = value

    @property
    def sender(self) -> User:
        return self._sender

    @sender.setter
    def sender(self, value):
        if isinstance(value, User):
            self._sender = value.uuid
        else:
            try:
                self._sender = UUID(value)
            except ValueError:
                raise

    @property
    def system_message(self) -> bool:
        return self._system_message

    @system_message.setter
    def system_message(self, value):
        self._system_message = value

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        self._uuid = value


my_dict = {
    "content": "hello",
    "system_message": False,
    "data": "hi"
}

a = Message(**my_dict)
print(dict(a))
