import sqlite3
from abc import ABC, abstractmethod
from typing import Union
from uuid import UUID


TABLE_COLUMNS_MSG = (
    "content",
    "message_uuid",
    "room",
    "created_at",
    "user",
    "system_message"
)
TABLE_COLUMNS_ROOM = (
    "uuid",
    "name",
    "invitedusers",
    "password"
)
TABLE_COLUMNS_USR = (
    "uuid",
    "name",
    "pwhash",
    "friends",
    "email",
    "blockedusers",
    "nickname",
    "status",
    "friendrequests",
    "rooms"
)


class BaseObj(ABC):

    TABLE_COLUMNS: tuple

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def data_format_from_tuple(cls, t: tuple, *, return_instance=False) -> Union[None, dict, "BaseObj"]:
        """
        Will return None if the zip failed, usually from attempting
        to instantiate a class with a non-iterable passed as 't'.
        This tends to happen if data wasn't found from the DB.

        :param t:
        :param return_instance:
        :return:
        """
        try:
            data_format = {k: v for k, v in zip(cls.TABLE_COLUMNS, t) if v is not None}
        except TypeError:
            return None
        if return_instance:
            return cls(**data_format)
        return data_format

    @property
    @abstractmethod
    def uuid(self) -> UUID: ...


# TODO: Implement logging
class BaseQuery:

    def __init__(self, _cache: "Cache", _conn: sqlite3.Connection, _cursor: sqlite3.Cursor):
        self.__cache = _cache
        self.__conn = _conn
        self.__cursor = _cursor

    @staticmethod
    def __data_to_table_params(*data) -> str:
        """
        Converts a tuple of arguments to sqlite-friendly parameters
        for creating a table.

        Example:
            Usage: __data_to_table_params("my_int", "INTEGER", "my_string", "TEXT")

            Returns: 'my_int INTEGER, my_string TEXT'

        :param data: A tuple of values to be unpacked and iterated over.
        :return: A string representation of parameters and datatypes for creating a table.
        """
        return ", ".join(f"{data[i]} {data[i+1]}" for i in range(0, len(data), 2))

    def clear_cache_for(self, func: callable, *args, **kwargs):
        del self.cache[str(func(*args, **kwargs).uuid)]
        return self.cache.get(func(*args, **kwargs))

    @property
    def cache(self) -> "Cache":
        return self.__cache

    @cache.setter
    def cache(self, value: "Cache"):
        self.__cache = value

    @property
    def conn(self) -> sqlite3.Connection:
        return self.__conn

    @conn.setter
    def conn(self, value):
        self.__conn = value

    @property
    def cursor(self) -> sqlite3.Cursor:
        return self.__cursor

    @cursor.setter
    def cursor(self, value):
        self.__cursor = value

    def create_table_if_not_exists(self, table_name: str, *data):
        if not data:

            if table_name.lower() == "messages":
                self.cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                message_uuid CHAR(36),
                room CHAR(36),
                user CHAR(36),
                system_message INT
                )""")

            elif table_name.lower() == "rooms":
                self.cursor.execute("""CREATE TABLE IF NOT EXISTS rooms (
                uuid CHAR(36),
                name TEXT,
                invitedusers TEXT DEFAULT "",
                password TEXT DEFAULT NULL
                )""")

            elif table_name.lower() == "users":
                self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATE DEFAULT CURRENT_TIMESTAMP,
                uuid CHAR(36),
                name CHAR(24),
                pwhash TEXT DEFAULT NULL,
                friends TEXT DEFAULT "",
                email TEXT DEFAULT NULL,
                blockedusers TEXT "",
                nickname TEXT DEFAULT NULL,
                status INT DEFAULT 1,
                friendrequests TEXT DEFAULT "",
                rooms TEXT DEFAULT ""
                )""")

            else:
                return
        else:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS ? 
            (?)""", (table_name, self.__data_to_table_params(*data)))

        self.conn.commit()

    def drop_table(self, table_name: str):
        self.cursor.execute("""DROP TABLE ?""", table_name)
        self.conn.commit()
