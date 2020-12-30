from abc import ABC
from bases import _BaseObj
from secrets import token_bytes
from uuid import UUID


class Room(_BaseObj):
    """
    Creating the Room as an abstract base class will
    mean that if it wishes to be inherited from, all
    of its abstract methods must be overridden.
    """

    def __init__(self):
        self._name = None
        self._uuid = UUID(bytes=token_bytes(16))

    def __str__(self):
        return str(self.uuid)

    @property
    def invites(self):
        return

    @property
    def name(self):
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

    def update(self):
        self._name = None


class Chatroom(Room):

    def __init__(self):
        super().__init__()

    def abc_method(self) -> None:
        super()


class Gameroom(Room):

    def __init__(self):
        super().__init__()


a = Gameroom()
