import sqlite3
from typing import Iterable, Tuple, Union, Optional

from bases import BaseQuery
from message import Message
from room import Room
from user import User
from utils.fmt import hash_pw
from utils.cache import Cache


class MessageQuery(BaseQuery):

    room_query: "RoomQuery"
    user_query: "UserQuery"

    def __init__(self, *, cache: Cache):
        self.__cache = cache
        self.__conn = sqlite3.connect("messages.db", check_same_thread=False)
        self.__cursor = self.__conn.cursor()

        super().__init__(self.__cache, self.__conn, self.__cursor)
        self.create_table_if_not_exists("messages")

    def add_message(self, message: Message):
        if isinstance(message, dict):
            message = Message(**message)

        message.room = self.room_query.main_room if not message.room else message.room

        self.cursor.execute(f"""INSERT INTO messages ({", ".join(Message.TABLE_COLUMNS)})
        VALUES (?, ?, ?, ?, ?, ?)""", (message.content, str(message.uuid), str(message.room.uuid),
                                       message.timestamp, str(message.user.uuid),
                                       message.system_message))
        self.conn.commit()

    def fetch_message_by_uuid(self, uuid: str) -> Message:
        try:
            message = self.cache.get(uuid)
            print("GOT FROM CACHE")
        except (KeyError, TypeError) as e:
            self.cursor.execute(f"""SELECT {", ".join(Message.TABLE_COLUMNS)} FROM messages WHERE message_uuid = ?""", (uuid,))
            record = self.cursor.fetchone()
            obj_record = [*record]  # Unpacking tuple into list

            del record

            obj_record[2] = self.room_query.fetch_room_by("uuid", obj_record[2])
            obj_record[4] = self.user_query.fetch_user_by("uuid", obj_record[4])

            obj_record = (*obj_record,)
            print(obj_record, "AHWAH")
            message = Message.data_format_from_tuple(obj_record, return_instance=True)

            if isinstance(message, Message):
                self.cache.cache_to("bottom", message)

        return message


class RoomQuery(BaseQuery):

    msg_query: MessageQuery
    user_query: "UserQuery"

    def __init__(self, *, cache: Cache):
        self.__cache = cache
        self.__conn = sqlite3.connect("rooms.db", check_same_thread=False)
        self.__cursor = self.__conn.cursor()

        super().__init__(self.__cache, self.__conn, self.__cursor)
        self.create_table_if_not_exists("rooms")

        self.main_room: Room = self.__create_main_room_if_not_exists(Room("main"))

    def __create_main_room_if_not_exists(self, room: Room) -> Room:
        main_room = self.fetch_room_by("name", "main")
        if main_room is None:
            self.cursor.execute("""INSERT INTO rooms (name, uuid)
            SELECT ?, ? WHERE NOT EXISTS (SELECT 1 FROM rooms WHERE name = "main")""",
                                (room.name, str(room.uuid)))
            self.conn.commit()
            main_room = room

        return main_room

    def fetch_room_by(self, column: str, data: ...) -> Union[None, Room]:
        """
        Attempts to find a room in the cache and return it.
        If no room is found, a SELECT query is executed and
        caches the result if a record matches the search.

        :param column: The column name to search by in the SQLite query if necessary.
        :param data: Criteria that must be matched in the given column.
        :return: A Room object matching the given data, or None if not found.
        """
        try:
            room = self.cache.get(data)
        except (KeyError, TypeError) as e:
            print(e)
            self.cursor.execute(f"""SELECT * FROM rooms WHERE {column} = ?""",
                                (data,))
            record = self.cursor.fetchone()
            room = Room.data_format_from_tuple(record, return_instance=True)

            if isinstance(room, Room):
                self.cache.cache_to("bottom", room)

        return room


class UserQuery(BaseQuery):

    msg_query: MessageQuery
    room_query: RoomQuery

    def __init__(self, *, cache: Cache):
        self.__cache = cache
        self.__conn = sqlite3.connect("users.db", check_same_thread=False)
        self.__cursor = self.__conn.cursor()

        super().__init__(self.__cache, self.__conn, self.__cursor)
        self.create_table_if_not_exists("users")

    def add_user(self, user: User, *, password: str = None):
        main_room = self.room_query.fetch_room_by("name", "main")
        name = user.name
        uuid = str(user.uuid)

        self.cache.cache_to("bottom", user)

        if not user.is_anonymous():
            email = user.get_email()
            pw_hash = hash_pw(password, uuid)
            self.cursor.execute("""INSERT INTO users (uuid, name, pwhash, email, rooms)
                                VALUES (?, ?, ?, ?, ?)""", (uuid, name, pw_hash, email,
                                                            str(main_room.uuid)))
        else:
            self.cursor.execute("""INSERT INTO users (uuid, name, rooms)
                                VALUES (?, ?, ?)""", (uuid, name, str(main_room.uuid)))

        self.conn.commit()

    def delete_user(self, user: User):
        self.cursor.execute("""UPDATE users SET name = "$DELETED_USER" WHERE uuid = ?""", (str(user.uuid),))
        self.cursor.execute("""UPDATE users SET status = ? WHERE uuid = ?""", (user.status, str(user.uuid)))

        self.conn.commit()
        if not user.is_anonymous():
            for col in {"pwhash", "email", "nickname"}:
                self.cursor.execute(f"""UPDATE users SET {col} = NULL WHERE uuid = ?""", (str(user.uuid),))
            self.conn.commit()

        try:
            # Cached data is instantly updated, as to comply
            # with whatever GDPR regulations I need to
            # comply with
            self.cache.update(user)
        except (KeyError, TypeError) as e:
            print("GOLLY, USER WASN'T IN CACHE - NO WORRIES")

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
            self.cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
            record = self.cursor.fetchone()

            return True if record else False

        return self.fetch_pw_hash_by("email", email) if return_pw_hash else self.fetch_user_data_by("email", email)

    def fetch_all_rooms_for(self, user: User) -> Iterable[Room]:
        if user.is_anonymous():
            return [self.room_query.main_room]

        try:
            cached_user = self.cache.get(user)
            print(user)
            print(f"{user!r}")
            print(vars(cached_user))

            return cached_user.rooms
        except KeyError as e:
            print(e)
            self.cursor.execute("""SELECT rooms FROM users WHERE uuid = ?""", (str(user.uuid),))
            record = self.cursor.fetchone()[0]
            room_uuids = record.split(" ")  # Agreed-upon room sep. char

            rooms = [self.room_query.fetch_room_by("uuid", uuid) for uuid in room_uuids]
            user.rooms = rooms

            self.cache.cache_to("bottom", user)

            return rooms

    def fetch_user_data_by(self, column: str, data: ...) -> Tuple[int, Tuple[Union[str, None], ...]]:
        self.cursor.execute(f"""SELECT status, uuid, name, friends, blockedusers, nickname, friendrequests, email
                            FROM users WHERE {column} = ?""", (data,))

        user_data = self.cursor.fetchone()

        return user_data

    def fetch_user_by(self, column: str, data: ...):
        try:
            user = self.cache.get(data if column == "uuid" else None)
        except (KeyError, TypeError) as e:
            user_data = self.fetch_user_data_by(column, data)
            user = User.from_existing_data(data=user_data)
            user.rooms = self.fetch_all_rooms_for(user)

            if isinstance(user, User):
                self.cache.cache_to("bottom", user)

        return user

    def fetch_pw_hash_by(self, column: str, data: ...) -> str:
        self.cursor.execute(f"SELECT pwhash FROM users WHERE {column} = ?", (data,))

        pw_hash = self.cursor.fetchone()
        return pw_hash

    def is_username_available(self, username: str) -> bool:
        self.cursor.execute("""SELECT name FROM users WHERE name = ?""", (username,))

        record = self.cursor.fetchone()

        return False if record else True

    def update_user_status(self, user: User):
        self.cache.update(user)
        self.cursor.execute("""UPDATE users SET status = ? WHERE uuid = ?""", (user.status, str(user.uuid)))

        self.conn.commit()


if __name__ == "__main__":
    rm = Cache()
    ms = Cache()
    ms_q = MessageQuery(cache=ms)
    rm_q = RoomQuery(cache=rm)
    us_q = UserQuery(cache=Cache(max_size=2**10))
    ms_q.room_query, ms_q.user_query = rm_q, us_q
    rm_q.msg_query, rm_q.user_query = ms_q, us_q
    us_q.msg_query, us_q.msg_query = ms_q, rm_q

    msg = Message(content="HELLO WORLD", system_message=True, room=rm_q.fetch_room_by("name", "main"))
    ms_q.add_message(msg)

    print("FIRST FETCH")
    m = ms_q.fetch_message_by_uuid("1d7548ec-50b0-f8be-5097-5d22f16f84ca")

    print("FETCHING AGAIN")
    m = ms_q.fetch_message_by_uuid("1d7548ec-50b0-f8be-5097-5d22f16f84ca")

    print("CLEAN CACHE FETCH:")
    m = ms_q.clear_cache_for(ms_q.fetch_message_by_uuid, "1d7548ec-50b0-f8be-5097-5d22f16f84ca")

