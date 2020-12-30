import sqlite3
from abc import ABC, abstractmethod
from uuid import UUID


class _BaseObj(ABC):

    @property
    @abstractmethod
    def uuid(self) -> UUID: ...


# TODO: Implement logging
class _BaseQuery:

    def __init__(self, _conn, _cursor):
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
            if table_name.lower() == "accounts":
                self.cursor.execute("""CREATE TABLE IF NOT EXISTS accounts
                (uuid varchar(36), name varchar(24), pwhash text, friends text,
                email text, blockedusers text, nickname text, status int,
                friendrequests text, rooms text)""")

            elif table_name.lower() == "messages":
                self.cursor.execute("""CREATE TABLE IF NOT EXISTS messages
                (content text, message_uuid varchar(36), room varchar(36), sender varchar(36),
                system_message integer)""")

            else:
                return
        else:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS ? 
            (?)""", (table_name, self.__data_to_table_params(*data)))

        self.conn.commit()

    @staticmethod
    def drop_table(self, table_name: str):
        print(table_name)
