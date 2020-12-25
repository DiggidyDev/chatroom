from abc import ABC, abstractmethod


class Room(ABC):
    """
    Creating the Room as an abstract base class will
    mean that if it wishes to be inherited from, all
    of its abstract methods must be overridden.
    """

    def __init__(self):
        pass

    #@abstractmethod
    def abc_method(self) -> None:
        return None

    @property
    def invites(self):
        return

    @property
    #@abstractmethod
    def name(self):
        return self._name

    def update(self):
        self._name = None


class Chatroom(Room):

    def __init__(self):
        super().__init__()

    def abc_method(self) -> None:
        super().abc_method()


class Gameroom(Room):

    def __init__(self):
        super().__init__()

    def abc_method(self) -> None:
        return


a = Gameroom()
