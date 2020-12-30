import sqlite3
from typing import Tuple, Union, Optional

from bases import _BaseQuery
from message import Message
from user import User
from utils.fmt import hash_pw


class MessageQuery(_BaseQuery):

    def __init__(self):
        self.__conn = sqlite3.connect("messages.db", check_same_thread=False)
        self.__cursor = self.__conn.cursor()

        super().__init__(self.__conn, self.__cursor)
        self.create_table_if_not_exists("messages")

    def add_message(self, message: Message):
        self.cursor.execute(f"""INSERT INTO messages (?, ?, ?, ?, ?)
        VALUES (?, ?, ?, ?, ?)""", (*Message.TABLE_COLUMNS,
                                    message.content, message.uuid, message.room.uuid,
                                    message.user.uuid, message.system_message))

    def fetch_message_by_uuid(self, uuid: str) -> Message:
        self.cursor.execute(f"""SELECT * FROM messages WHERE message_uuid = ?""", (uuid,))
        record = self.cursor.fetchone()

        data = Message.data_format_from_tuple(record)
        message = Message.from_uuid(**data)
        return message


class UserQuery(_BaseQuery):

    def __init__(self):
        self.__conn = sqlite3.connect("users.db", check_same_thread=False)
        self.__cursor = self.__conn.cursor()

        super().__init__(self.__conn, self.__cursor)
        self.create_table_if_not_exists("accounts")

    def add_user(self, user: User, password: str):
        uuid = str(user.uuid)
        name = user.name
        email = user.get_email()
        pw_hash = hash_pw(password, uuid)
        self.cursor.execute("""INSERT INTO accounts (uuid, name, pw_hash, email)
                            VALUES (?, ?, ?, ?)""", (uuid, name, pw_hash, email))
        self.conn.commit()

    def is_username_available(self, username: str) -> bool:
        self.cursor.execute("""SELECT name FROM accounts WHERE name = ?""", (username,))

        record = self.cursor.fetchone()
        return False if record else True

    def does_user_email_exist(self, email: str, return_pw_hash: bool = False, return_uuid: bool = False)\
            -> Union[str, Tuple[Optional[str], ...], bool, Tuple[int, Tuple[Optional[str], ...]]]:
        """
        Searches for the email in the user database,
        returning whether a match was found or not.
        In cases where the requested email is incorrect,
        None is returned instead.

        :param return_pw_hash: Returns hashed pw if supplied email was found.
        :param return_uuid: Returns UUID belonging to email if found.
        :param email: The target email to search for.
        :return: A boolean indicating the result of the search.
        """

        if return_pw_hash:
            return self.fetch_pw_hash_by("email", email)
        if return_uuid:
            return self.fetch_user_data_by("email", email)[1]

        if not return_uuid and not return_pw_hash:
            self.cursor.execute("SELECT email FROM accounts WHERE email = ?", (email,))
            record = self.cursor.fetchone()

            return True if record else False

        return self.fetch_pw_hash_by("email", email) if return_pw_hash else self.fetch_user_data_by("email", email)

    def fetch_user_data_by(self, datatype: str, data: ...) -> Tuple[int, Tuple[Union[str, None], ...]]:
        self.cursor.execute(f"""SELECT status, uuid, name, friends, blockedusers, nickname, friendrequests, email
                            FROM accounts WHERE {datatype} = ?""", (data,))

        user_data = self.cursor.fetchone()
        return user_data

    def fetch_pw_hash_by(self, datatype: str, data: ...) -> str:
        self.cursor.execute(f"SELECT pwhash FROM accounts WHERE {datatype} = ?", (data,))

        pw_hash = self.cursor.fetchone()
        return pw_hash
