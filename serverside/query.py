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

    def fetch_recent_messages(self, *, amount=200, room: Room = None, position=None, msg: Message = None):
        if room is None:
            room = self.room_query.main_room

        if hasattr(room, "uuid"):
            room_uuid = str(room.uuid)
        else:
            room_uuid = room

        if msg is None:
            self.cursor.execute(f"""SELECT message_uuid FROM messages WHERE room = ? ORDER BY _id DESC LIMIT {amount}""",
                                (room_uuid,))
            r = self.cursor.fetchall()
            msgs = [self.fetch_message_by_uuid(u[0]) for u in r]

        else:
            if hasattr(msg, "uuid"):
                msg_uuid = str(msg.uuid)
            else:
                msg_uuid = msg

            if position == "above":
                self.cursor.execute(
                    f"""SELECT message_uuid FROM messages WHERE _id < (SELECT _id FROM messages WHERE\
                    message_uuid = ? and room = ?) ORDER BY _id DESC LIMIT {amount}""",
                    (msg_uuid, room_uuid)
                )
            elif position == "below":
                self.cursor.execute(
                    f"""SELECT message_uuid FROM messages WHERE _id > (SELECT _id FROM messages WHERE\
                     message_uuid = ? and room = ?) ORDER BY _id ASC LIMIT {amount}""",
                    (msg_uuid, room_uuid)
                )
            else:
                raise TypeError("Please only use \"above\" or \"below\"")

            r = self.cursor.fetchall()
            msgs = [self.fetch_message_by_uuid(u[0]) for u in r]

        return msgs

    def fetch_message_by_uuid(self, uuid: str) -> Message:
        try:
            message = self.cache.get(uuid)
        except (KeyError, TypeError) as e:
            self.cursor.execute(f"""SELECT {", ".join(Message.TABLE_COLUMNS)} FROM messages WHERE message_uuid = ?""", (uuid,))
            record = self.cursor.fetchone()
            obj_record = [*record]  # Unpacking tuple into list

            del record

            obj_record[2] = self.room_query.fetch_room_by("uuid", obj_record[2])
            obj_record[4] = self.user_query.fetch_user_by("uuid", obj_record[4])

            obj_record = (*obj_record,)
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

        self.main_room: Room = self.create_room_if_not_exists(Room("main"))

    def create_room_if_not_exists(self, room_to_find: Room) -> Room:
        room = self.fetch_room_by("name", room_to_find.name)
        if room is None:
            self.cursor.execute("""INSERT INTO rooms (name, uuid)
            SELECT ?, ? WHERE NOT EXISTS (SELECT 1 FROM rooms WHERE name = "main")""",
                                (room_to_find.name, str(room_to_find.uuid)))
            self.conn.commit()
            room = room_to_find

        return room

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
            email = user.email
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

    def fetch_all_rooms_for(self, user: User) -> Iterable[Room]:
        if user.is_anonymous():
            return [self.room_query.main_room]

        try:
            cached_user = self.cache.get(user)

            return cached_user.rooms
        except (KeyError, AttributeError) as e:
            print(e)
            self.cursor.execute("""SELECT rooms FROM users WHERE uuid = ?""", (str(user.uuid),))
            record = self.cursor.fetchone()[0]
            room_uuids = record.split(" ")  # Agreed-upon room sep. char

            rooms = [self.room_query.fetch_room_by("uuid", uuid) for uuid in room_uuids]
            user.rooms = rooms

            if isinstance(e, KeyError):
                self.cache.update(user)
            else:
                self.cache.cache_to("bottom", user)

            return rooms

    def fetch_user_by(self, column: str, data: ...):
        user = None
        try:
            user = self.cache.get(data if column == "uuid" else None)

        except (KeyError, TypeError) as e:
            self.cursor.execute(f"""SELECT status, uuid, name, friends, blockedusers, nickname, friendrequests, email, rooms
                                FROM users WHERE {column} = ?""", (data,))

            user_data = self.cursor.fetchone()
            if user_data is not None:
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

