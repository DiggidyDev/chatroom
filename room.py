from secrets import token_bytes
from uuid import UUID

from bases import BaseObj, TABLE_COLUMNS_ROOM


class Room(BaseObj):

    TABLE_COLUMNS = TABLE_COLUMNS_ROOM

    def __init__(self,
                 name,
                 *,
                 invitedusers=None,
                 password=None,
                 uuid=None,
                 last_message=None):

        if invitedusers is None:
            invitedusers = []

        self._invites = invitedusers
        self._last_message = last_message
        self._name = name
        self._password = password
        self._uuid = uuid if uuid else UUID(bytes=token_bytes(16))

        super().__init__()

    def __repr__(self):
        return f"<type={self.__class__.__qualname__} invites={self.invites!r} name={self.name!r} has_password={self._password is not None}>"

    def __str__(self):
        return str(self.uuid)

    @property
    def invites(self):
        return self._invites

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def most_recent_message(self):
        return self._last_message

    @most_recent_message.setter
    def most_recent_message(self, value):
        self._last_message = value

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        self._uuid = value
