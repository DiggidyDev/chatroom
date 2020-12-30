import timeit
from typing import List, Dict, Union
from uuid import UUID, uuid4

from bases import _BaseObj


class _CacheDict(Dict[str, _BaseObj], dict):
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

    def __str__(self):
        return ", ".join(self.__cache_list)

    def __len__(self):
        return len(self.__cache_list)

    def __uncache_from_index(self, index: int) -> _BaseObj:
        removed = self.__cache_list.pop(-(index+1 & 1))
        return self.__cache_dict.pop(removed)

    @property
    def __top(self) -> int:
        return self.__len__()

    def cache_to(self, side: str, obj: _BaseObj):
        """
        Bottom of cache has an index of 0

        :param side:
        :param obj:
        :return:
        """
        index = 0

        if side not in {"top", "bottom"}:
            raise AttributeError("You can only cache to the 'top' or 'bottom'")
        elif side == "top":
            index -= 1

        if self.is_full():
            self.__uncache_from_index(index)

        uuid = str(obj.uuid)
        self.__cache_list.insert(index, uuid)

        self.__cache_dict[uuid] = obj

    def get(self, obj: ...) -> Union[None, _BaseObj]:
        """"""
        try:
            if isinstance(obj, _BaseObj):
                return self.__cache_dict[str(obj.uuid)]
            elif isinstance(obj, str):
                return self.__cache_dict[obj]
            elif isinstance(obj, UUID):
                return self.__cache_dict[str(obj)]
        except KeyError:
            raise

    def is_full(self):
        return self.__top == self.__cache_dict.max_size
