import sqlite3
from typing import Tuple, Union

from clientside.user import User
from utils.fmt import hash_pw

CONN = sqlite3.connect("users.db", check_same_thread=False)
CUR = CONN.cursor()


def add_user(user: User, password):
    uuid = str(user.get_uuid())
    name = user.name
    email = user.get_email()
    print(email)
    pwhash = hash_pw(password, uuid)
    CUR.execute("""INSERT INTO accounts (uuid, name, pwhash, email)
    VALUES (?, ?, ?, ?)""", (uuid, name, pwhash, email, ))
    CONN.commit()


def does_user_email_exist(email: str,
                          return_pw_hash: bool = False,
                          return_uuid: bool = False) -> Union[bool, str, None]:
    """
    Searches for the email in the database, returning
    whether a match was found or not.
    In cases where the requested email is incorrect,
    None is returned instead.

    :param return_pw_hash: Returns hashed pw if supplied email was found.
    :param return_uuid: Returns UUID belonging to email if found.
    :param email: The target email to search for.
    :return: A boolean indicating the result of the search.
    """
    if return_pw_hash:
        return get_pw_hash_by("email", email)
    if return_uuid:
        return fetch_user_data_by("email", email)[1]
    if not return_uuid and not return_pw_hash:
        for i in CUR.execute("SELECT email FROM accounts WHERE email = ?", (email,)):
            return True
        return False
    return get_pw_hash_by("email", email) if return_pw_hash else fetch_user_data_by(email)


def create_table_if_not_exists(table_name):
    if table_name == "accounts":
        CUR.execute("""CREATE TABLE IF NOT EXISTS accounts
        (uuid varchar(36), name varchar(24), pwhash text, friends text,
        email text, blockedusers text, nickname text, status int,
        friendrequests text, rooms text)""")
        CONN.commit()


def drop_table(table_name):
    print(table_name)


def fetch_user_data_by(datatype: str, data: ...) -> Tuple[int, Tuple[Union[str, None], ...]]:
    for user_data in CUR.execute(f"""SELECT status, uuid, name, friends, blockedusers, nickname, friendrequests, email
     FROM accounts WHERE {datatype} = ?""", (data,)):
        return user_data


def get_pw_hash_by(datatype: str, data: str) -> str:
    for i in CUR.execute(f"SELECT pwhash FROM accounts WHERE {datatype} = ?", (data,)):
        CONN.commit()
        return i
