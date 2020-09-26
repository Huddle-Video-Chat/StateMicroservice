import os
import redis
import pickle
from typing import Dict, List


if os.environ.get("REDIS_URL"):
    rc: redis.Redis = redis.from_url(os.environ.get("REDIS_URL"))
else: 
    rc: redis.Redis = redis.Redis(host='localhost', port=6379)

def get_list(key: str) -> List:
    """
    Helper function to retrieve a list stored in redis.
    :param key: str key of the redis list
    :return: list stored at key
    """
    return rc.lrange(key, 0, -1)

def delete_all_in_list(key: str) -> None:
    """
    Helper function to deplete a redis list.
    :param key: str key of the redis list
    """
    for _id in rc.get_list(key):
        rc.delete(_id)

def reset() -> None:
    """
    Helper function to clear the redis database.
    """
    rc.flushdb()

class Room():
    """
    Grouping functions related to database interactions for a Room.

    """
    def get_key(id: str) -> str:
        """
        Gets the key used in redis for a room.
        This hashmap stores a variety of room-specific values.
        :param id: id of the desired room
        :return: str key
        """
        return 'ROOM_' + str(id)


    def get_map_key(id):
        """
        Gets the key used in redis for a room's map of users to huddle
        :param id: id of the desired room
        :return: str key
        """
        return 'MAP_' + str(id) 
    
    def get_bots_key(id):
        return 'BOTS_' + str(id)

    def get_messages_list_key(id: str) -> str:
        """
        Gets the key used in redis for a room's messages.
        Stores a pickle
        :param id: id of the desired room
        :return: str key
        """
        return 'LISTROOMMESSAGES_' + str(id)

    def get_room_list_key() -> str:
        """
        Gets the key used for list of all rooms.
        :return: str key
        """
        return 'LISTROOMS'

    def get_named_huddles_key(id: str) -> str:
        """
        Gets the key used for map of named huddles in a room
        :param id: id of the desired room
        :return: str key
        """
        return 'NAMEDHUDDLES_' + str(id)

    def get_named_huddles_map(id: str) -> Dict:
        """
        Gets the map of named huddles in a room
        :param id: id of the desired room
        :return: map of the named huddles
        """
        return rc.hgetall('NAMEDHUDDLES_' + str(id))

    def add_named_huddle(id: str, huddle_id: int, name: str) -> None:
        """
        Marks an existing huddle in the room as named. The huddle may or may not contain people.
        :param id: id of the room
        :param huddle_id: id of the huddle
        :param name: name given to the huddle
        """
        rc.hmset(Room.get_named_huddles_key(id), {huddle_id: name})

    def removed_huddle_name(id: str, huddle_id: int) -> None:
        """
        Marks a named huddle as unnamed.
        :param id: id of the room
        :param huddle_id: id of the huddle
        """
        if rc.hget(Room.get_named_huddles_key(id), huddle_id):
            rc.hdel(Room.get_named_huddles_key(id), huddle_id)
        else:
            raise Exception("Huddle: " + str(huddle_id) + " is not named")

    def exists(id: str) -> int:
        """
        Checks whether a room exists in the database.
        :param id: id of the desired room
        :return: 1 if room exists, 0 if it does not
        """
        return rc.exists(Room.get_key(id))

    def create(id: str, data: Dict) -> str:
        """
        Creates a new room in the database containing pre-set metadata.
        ------------------
        name: name of the room
        huddle counter: number of huddles created in the room
        state counter: number of times room state has been changed
        ------------------
        :param id: id of the desired room
        :param data: dict containing metadata for the room.
        :return: str id of the room
        """
        key: str = Room.get_key(id)
        rc.lpush(Room.get_room_list_key(), id) # adds room id to rooms list
        rc.hmset(key, data) # creates room dict
        rc.hmset(key, {"HUDDLECOUNTER": 0})
        rc.hmset(key, {"STATECOUNTER": 0})
        #FIXME maybe return room state for consistency?
        return id

    def updateStateCounter(id: str) -> int:
        #TODO this should be called within database manipulation functions, not on the API layer
        """
        Increments state counter in a room when
        changes have been made.

        :param id: id of the desired room
        :return: int updated state count of the room
        """
        Room.verify_room(id)
        val: int = int(rc.hget(Room.get_key(id), "STATECOUNTER")) + 1
        rc.hmset(Room.get_key(id), {"STATECOUNTER": val})
        return val  

    def getStateCounter(id: str) -> int:
        """
        Returns the state counter of a room.

        :param id: id of the desired room
        :return: int updated state count of the room
        """
        Room.verify_room(id)
        count: int = int(rc.hget(Room.get_key(id), "STATECOUNTER"))
        return count

    def add_user_to_huddle(id: str, user_id: str, huddle_id: str) -> None:
        """
        Adds a user to a huddle. If the huddle does not already exist,
        it is created.
        :param id: str id of the room
        :param user_id: str id of user in the room
        :param huddle_id: str id of huddle in the room
        """
        Room.verify_room(id)
        rc.hmset(Room.get_map_key(id), {user_id: huddle_id})

    def add_user_to_new_huddle(id, user_id) -> None:
        """
        Adds a user to a new huddle. Creates one in the process.
        :param id: str id of the room
        :param user_id: str id of user in the room
        """
        Room.verify_room(id)
        rc.hmset(Room.get_map_key(id), {user_id: Room.get_next_huddle_id(id)})

    def delete_user(id: str, user_id) -> None:
        """
        Deletes a user from a room. Removes it as a key in the hashmap.
        :param id: str id of the room
        :param user_id: str id of user in the room
        """
        Room.verify_room(id)
        rc.hdel(Room.get_map_key(id), user_id)

    def has_user(id: str) -> bool:
        """
        returns if a room has users in it
        :param id: str id of the room
        """
        Room.verify_room(id)
        return rc.exists(Room.get_map_key(id))

    def delete(id: str) -> None:
        """
        Deletes a room from the database.
        Remove it from the room list and any dictionaries associated with it.
        :param id: str id of the room
        """
        Room.verify_room(id)
        rc.lrem(Room.get_room_list_key(), 1, id) # deletes room from list
        key: str = Room.get_key(id)
        rc.delete(key)

        map_key: str = Room.get_map_key(id)
        rc.delete(map_key)

        bots_key: str = Room.get_bots_key(id)
        rc.delete(bots_key)

    def list() -> List:
        """
        Get the room list, containing the keys to every room.
        :return: list of all room ids
        """
        return get_list(Room.get_room_list_key())

    def set_bot(id, huddle_id, url):
        if Room.exists(id):
            rc.hmset(Room.get_bots_key(id), {huddle_id: url})


    def get_bot(id, huddle_id):
        if Room.exists(id):
            return rc.hget(Room.get_bots_key(id), huddle_id)


    def delete_bot(id, huddle_id):
        if Room.exists(id):
            rc.hdel(Room.get_bots_key(id), huddle_id)

    def add_message(id: str, username: str, body: str) -> None:
        """
        Append a new message to the list of messages in the room.
        :param id: str id of the room
        :param username: name of user sending message
        :param body: body of the message
        """
        Room.verify_room(id)
        rc.lpush(Room.get_messages_list_key(id), pickle.dumps({"username": username, "body": body}))

    def list_messages(id: str) -> List:
        """
        Get the message list in the room.
        :param id: str id of the room
        :return: list of all messages in order of when it's sent
        """
        Room.verify_room(id)
        return [pickle.loads(msg) for msg in get_list(Room.get_messages_list_key(id))]

    def get_next_huddle_id(id: str) -> int:
        """
        Increments the huddle counter and return the latest value.
        :param id: str id of the room
        :return: latest huddle count
        """
        Room.verify_room(id)

        val: int = int(rc.hget(Room.get_key(id), "HUDDLECOUNTER")) + 1
        rc.hmset(Room.get_key(id), {"HUDDLECOUNTER": val})
        return val  

    def num() -> int:
        """
        Get the number of rooms in total
        :return: total number of rooms in the database
        """
        return rc.llen(Room.get_room_list_key())

    def get_zeroth_huddle(id: str) -> int:
        """
        Get the id of the original huddle in a room.
        :param id: str id of the room
        :return: id of the huddle
        """
        Room.verify_room(id)
        _map = Room.get_map(id)
        if len(_map.keys()) > 0:
            key = list(_map.keys())[0]
            return int(_map[key])
        else:
            return Room.get_next_huddle_id(id)

    def get(id: str):
        return rc.hgetall(Room.get_key(id))

    def get_map(id: str):
        return rc.hgetall(Room.get_map_key(id))

    def verify_room(id: str) -> None:
        #TODO make this into a decorator function
        """
        Helper function that throws an exception if the room id does not
        exist.
        :return: None
        """
        if not Room.exists(id):
            raise Exception("Room: " + str(id) + " does not exist")