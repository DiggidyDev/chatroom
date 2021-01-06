import timeit
from typing import List, Dict, Union, Iterable
from uuid import UUID

from bases import BaseObj
from room import Room
from user import User


class _CacheDict(Dict[str, BaseObj], dict):
    """
    My own implementation of a dict, used for fetching
    objects when populated, given a specific key.
    """

    def __init__(self, max_size=128, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__max_size = max_size

    @property
    def max_size(self):
        return self.__max_size


class Cache:

    def __init__(self, max_size=128):
        self.__cache_dict: _CacheDict = _CacheDict(max_size)
        self.__cache_list: List[str] = []
        self.__bottom = 0

    def __delitem__(self, key):
        print("deleting")
        self.__cache_list.remove(key)
        del self.__cache_dict[key]

    def __str__(self):
        return ", ".join(self.__cache_list)

    def __len__(self):
        return len(self.__cache_list)

    def __do_cache(self, obj: BaseObj, index: int):
        try:
            self.get(obj)
        except KeyError:
            if self.is_full():
                self.__uncache_from_index(index)

            uuid = str(obj.uuid)
            self.__cache_list.insert(index, uuid)

            self.__cache_dict[uuid] = obj
        else:
            print("Value already exists.")

    def __uncache_from_index(self, index: int) -> BaseObj:
        removed = self.__cache_list.pop(-(index+1 & 1))
        return self.__cache_dict.pop(removed)

    @property
    def __top(self) -> int:
        return self.__len__()

    def cache_to(self, side: str, obj: Union[BaseObj, Iterable[BaseObj]]):
        """
        Bottom of cache has an index of 0.

        This only really matters when coming to large
        amounts of messages being cached clientside
        when scrolling up or down; "top" and "bottom"
        respectively.

        :param side:
        :param obj:
        :return:
        """
        index = 0

        if side not in {"top", "bottom"}:
            raise AttributeError("You can only cache to the 'top' or 'bottom'")
        elif side == "top":
            index -= 1

        if isinstance(obj, BaseObj):
            self.__do_cache(obj, index)
        elif isinstance(obj, Iterable):
            for iter_obj in obj:
                self.__do_cache(iter_obj, index)

    # TODO: Add get by certain attr?
    def get(self, obj: ...) -> Union[None, BaseObj, Room, User]:
        """
        Returns

        :param obj:
        :return:
        """
        if obj is None:
            raise TypeError("No obj given")
        try:
            if isinstance(obj, BaseObj):
                return self.__cache_dict[str(obj.uuid)]
            elif isinstance(obj, str):
                return self.__cache_dict[obj]
            elif isinstance(obj, UUID):
                return self.__cache_dict[str(obj)]
        except KeyError:
            raise KeyError(f"{obj!r} not found in cache")

    def is_full(self):
        return self.__top == self.__cache_dict.max_size

    def update(self, obj: BaseObj):
        if not isinstance(obj, BaseObj):
            raise TypeError(f"{obj!r} invalid type for cache")
        try:
            cached_obj = self.get(obj)
            self.__cache_dict[str(cached_obj.uuid)] = obj
        except KeyError:
            raise


def main():

    from uuid import uuid1

    class TestObj(BaseObj):

        @property
        def uuid(self) -> UUID:
            return uuid1()

    times = {}

    for i in range(10):
        mycache = Cache(max_size=2**15)
        start = timeit.default_timer()
        for _ in range(2**16):
            t = TestObj()
            mycache.cache_to("bottom", t)

        times[i] = timeit.default_timer()-start

    FORMATTED = f""" AVERAGE : {sum(times.values())/len(times)}"""

    print(FORMATTED)
