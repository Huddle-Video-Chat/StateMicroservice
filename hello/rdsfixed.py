import os
import redis
import pickle

if os.environ.get("REDIS_URL"):
    rc = redis.from_url(os.environ.get("REDIS_URL"))
else: 
    rc = redis.Redis(host='localhost', port=6379)

def get_list(key):
    return rc.lrange(key, 0, -1)

def delete_all_in_list(key):
    for _id in self.get_list(key):
        rc.delete(id)

def reset():
    rc.flushdb()

class Room():
    def get_key(id: int) -> str:
        return 'ROOM_' + str(id)

    def get_map_key(id):
        return 'MAP_' + str(id) 
    
    def get_bots_key(id):
        return 'BOTS_' + str(id)

    def get_messages_list_key(id: int) -> str:
        return 'LISTROOMMESSAGES_' + str(id)

    def get_room_list_key() -> str:
        return 'LISTROOMS'

    def exists(id: int) -> str:
        return rc.exists(Room.get_key(id))

    def create(id: int, data) -> int:
        key: str = Room.get_key(id)
        rc.lpush(Room.get_room_list_key(), id) # adds room id to rooms list
        rc.hmset(key, data) # creates room dict

        rc.hmset(key, {"HUDDLECOUNTER": 0})
        rc.hmset(key, {"STATECOUNTER": 0})

        return id

    def updateStateCounter(id):
        val = int(rc.hget(Room.get_key(id), "STATECOUNTER")) + 1
        rc.hmset(Room.get_key(id), {"STATECOUNTER": val})
        return val  

    def getStateCounter(id):
        return int(rc.hget(Room.get_key(id), "STATECOUNTER"))

    def add_user_to_huddle(id, user_id, huddle_id):
        if Room.exists(id):
            rc.hmset(Room.get_map_key(id), {user_id: huddle_id})

    def add_user_to_new_huddle(id, user_id):
        if Room.exists(id):
            rc.hmset(Room.get_map_key(id), {user_id: Room.get_next_huddle_id(id)})

    def delete_user(id, user_id):
        if Room.exists(id):
            rc.hdel(Room.get_map_key(id), user_id)

    def set_bot(id, huddle_id, url):
        if Room.exists(id):
            rc.hmset(Room.get_bots_key(id), {huddle_id: url})

    def get_bot(id, huddle_id):
        if Room.exists(id):
            return rc.hget(Room.get_bots_key(id), huddle_id)
        
    def delete_bot(id, huddle_id):
        if Room.exists(id):
            rc.hdel(Room.get_bots_key(id), huddle_id)

    def delete(id):
        if Room.exists(id):
            rc.lrem(Room.get_room_list_key(), 1, id) # deletes room from list 

            key = Room.get_key(id)
            all_keys = list(rc.hgetall(key).keys()) 
            rc.hdel(key, *all_keys) # deletes dict

            map_key = Room.get_map_key(id)
            all_keys = list(rc.hgetall(map_key).keys()) 
            rc.hdel(map_key, *all_keys) # deletes dict

            bots_key = Room.get_bots_key(id)
            all_keys = list(rc.hgetall(bots_key).keys()) 
            rc.hdel(bots_key, *all_keys) # deletes dict

    def list():
        return get_list(Room.get_room_list_key())

    def add_message(id, username, body):
        if Room.exists(id):
            rc.lpush(Room.get_messages_list_key(id), pickle.dumps({"username": username, "body": body})) # add message to room's messages list

    def list_messages(id):
        return [pickle.loads(msg) for msg in get_list(Room.get_messages_list_key(id))]

    def get_next_huddle_id(id):
        val = int(rc.hget(Room.get_key(id), "HUDDLECOUNTER")) + 1
        rc.hmset(Room.get_key(id), {"HUDDLECOUNTER": val})
        return val  

    def num():
        return rc.llen(Room.get_room_list_key())

    def get_zeroth_huddle(id):
        _map = Room.get_map(id)
        if len(_map.keys()) > 0:
            key = list(_map.keys())[0]
            return int(_map[key])
        else:
            return Room.get_next_huddle_id(id)

    def get(id):
        return rc.hgetall(Room.get_key(id))

    def get_map(id):
        return rc.hgetall(Room.get_map_key(id))