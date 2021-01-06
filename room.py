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
                 uuid=UUID(bytes=token_bytes(16))):

        self._invites = invitedusers
        self._name = name
        self._password = password
        self._uuid = uuid if uuid else UUID(bytes=token_bytes(16))

        super().__init__()

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
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        self._uuid = value
