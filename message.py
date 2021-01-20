import pickle
from secrets import token_bytes
from datetime import datetime
from typing import Union
from uuid import UUID

from bases import BaseObj, TABLE_COLUMNS_MSG
from room import Room
from user import User


class Message(BaseObj):

    TABLE_COLUMNS = TABLE_COLUMNS_MSG

    def __init__(self,
                 content: str,
                 system_message: bool,
                 create: str = None,
                 data: ... = None,
                 datatype: str = None,
                 get: str = None,
                 message_uuid: str = None,
                 room: Room = None,
                 created_at: datetime = None,
                 user: User = None):
        self._content = content
        self._system_message = system_message

        self.create = create
        self.created_at = created_at if created_at is not None else datetime.now()
        self.data = data
        self.datatype = datatype
        self.get = get

        self._message_uuid = message_uuid if message_uuid is not None else UUID(bytes=token_bytes(16))
        self._room = room
        self._user = user

        super().__init__()

    def __repr__(self):
        return f"<type={self.__class__.__name__} system_message={not not self.system_message} " \
               f"content={self.content!r} room={self.room!r} user={self.user!r} " \
               f"timestamp={self.timestamp!r} uuid={self.uuid}>"

    def __bytes__(self):
        return pickle.dumps(dict(self))

    def __getitem__(self, item):
        return dict(self)[item]

    def __iter__(self):
        given_args = {k: v for k, v in vars(Message).items()}
        given_args.update(vars(self))
        for k, v in sorted(
                [(k, v) for k, v in given_args.items() if k in self.class_args()
                                                          and v is not None and k[-1] != "_"],
                key=lambda x: x[0].strip("_")
        ):
            if k.startswith("_"):
                k = k[1:]
            yield k, v

    def __str__(self):
        return self.content

    @classmethod
    def class_args(cls):
        return cls.__init__.__code__.co_names

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    @property
    def room(self) -> Room:
        return self._room

    @room.setter
    def room(self, value):
        self._room = value

    @property
    def user(self) -> User:
        return self._user

    @user.setter
    def user(self, value):
        if isinstance(value, User):
            self._user = value
        else:
            raise TypeError(f"{value!r} is not valid type {User!r}")

    @property
    def system_message(self) -> bool:
        return self._system_message

    @system_message.setter
    def system_message(self, value):
        self._system_message = value

    @property
    def timestamp(self) -> str:
        return self.created_at if not hasattr(self.created_at, "strftime") else self.created_at.strftime("%Y/%m/%d - %H:%M:%S")

    @timestamp.setter
    def timestamp(self, value: Union[datetime, str]):
        self.created_at = value

    @property
    def uuid(self):
        return self._message_uuid

    @uuid.setter
    def uuid(self, value):
        self._message_uuid = value
