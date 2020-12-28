import sqlite3
from typing import Tuple, Union, Optional

from clientside.user import User
from serverside.message import Message
from utils.fmt import hash_pw


class MessageQuery:

    def __init__(self):
        self.CONN = sqlite3.connect("messages.db", check_same_thread=False)
        self.CURSOR = self.CONN.cursor()

    def add_message(self,
                    message: Message):
        pass


class UserQuery:

    def __init__(self):
        self.CONN = sqlite3.connect("users.db", check_same_thread=False)
        self.CURSOR = self.CONN.cursor()

    def add_user(self,
                 user: User,
                 password):
        uuid = str(user.uuid)
        name = user.name
        email = user.get_email()
        pw_hash = hash_pw(password, uuid)
        self.CONN.execute("""INSERT INTO accounts (uuid, name, pw_hash, email)
        VALUES (?, ?, ?, ?)""", (uuid, name, pw_hash, email, ))
        self.CONN.commit()

    def is_username_available(self,
                              username: str) -> bool:
        self.CURSOR.execute("""SELECT name FROM accounts WHERE name = ?""", (username,))
        record = self.CURSOR.fetchone()

        return False if record else True

    def does_user_email_exist(self,
                              email: str,
                              return_pw_hash: bool = False,
                              return_uuid: bool = False) -> Union[
        str, Tuple[Optional[str], ...], bool, Tuple[
            int, Tuple[Optional[str], ...]]]:
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
            return self.get_pw_hash_by("email", email)
        if return_uuid:
            return self.fetch_user_data_by("email", email)[1]

        if not return_uuid and not return_pw_hash:
            self.CURSOR.execute("SELECT email FROM accounts WHERE email = ?", (email,))
            record = self.CURSOR.fetchone()

            return True if record else False

        return self.get_pw_hash_by("email", email) if return_pw_hash else self.fetch_user_data_by(email)

    def create_table_if_not_exists(self,
                                   table_name: str):
        if table_name.lower() == "accounts":
            self.CURSOR.execute("""CREATE TABLE IF NOT EXISTS accounts
            (uuid varchar(36), name varchar(24), pwhash text, friends text,
            email text, blockedusers text, nickname text, status int,
            friendrequests text, rooms text)""")

            self.CONN.commit()

    @staticmethod
    def drop_table(self,
                   table_name: str):
        print(table_name)

    def fetch_user_data_by(self,
                           datatype: str,
                           data: ...) -> Tuple[int, Tuple[Union[str, None], ...]]:
        for user_data in self.CURSOR.execute(f"""SELECT status, uuid, name, friends, blockedusers, nickname, friendrequests, email
         FROM accounts WHERE {datatype} = ?""", (data,)):
            return user_data

    def get_pw_hash_by(self,
                       datatype: str,
                       data: str) -> str:
        for i in self.CURSOR.execute(f"SELECT pwhash FROM accounts WHERE {datatype} = ?", (data,)):
            self.CONN.commit()
            return i
