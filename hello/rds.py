import os
import redis

# class RedisClient(redis.Redis):
#     def __init__(self):
#         super(self.__class__, self).__init__(
#             host='redis://h:pf1c13f2a465ee1822060f5118972cea576ebb4eb5f7f7e4f310446f7dc366232@ec2-23-21-1-196.compute-1.amazonaws.com',
#             port=18429
#         )

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
    def get_key(id):
        return 'ROOM_' + str(id)
    
    def get_user_list_key(id):
        return 'LISTROOMUSERS_' + str(id)

    def get_huddle_list_key(id):
        return 'LISTROOMHUDDLES_' + str(id)

    def get_room_list_key():
        return 'LISTROOMS'

    def get_messages_list_key(id):
        return 'LISTROOMMESSAGES_' + str(id)

    def exists(id):
        return rc.exists(Room.get_key(id))

    def create(id, data):
        # id = Room.get_next_id(Room.get_room_counter_key())

        key = Room.get_key(id)
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

    def add_user(id, user_id, user_data):
        if Room.exists(id):
            # user_id = Room.get_next_id(Room.get_key(id), key="USERCOUNTER")
            User.create(id, user_id, user_data) # creates user dict
            rc.lpush(Room.get_user_list_key(id), user_id) # add user id to room's users list
            return user_id
            

    def delete_user(id, user_id, huddle_id):
        if Room.exists(id):
            rc.lrem(Room.get_user_list_key(id), 1, user_id) # delete user from users list
            User.delete(id, user_id) # delete user dict
            Huddle.delete_user(id, huddle_id, user_id)


    def add_huddle(id, huddle_data):
        if Room.exists(id):
            huddle_id = Room.get_next_huddle_id(id)
            Huddle.create(id, huddle_id, huddle_data) # creates huddle dict
            rc.lpush(Room.get_huddle_list_key(id), huddle_id) # add huddle id to room's huddles list


            return huddle_id

    def delete_huddle(id, huddle_id):
        rc.lrem(Room.get_huddle_list_key(id), 1, huddle_id) # delete huddle from huddles list
        Huddle.delete(id, huddle_id) # delete huddle dict

    def add_message(id, username, body):
        if Room.exists(id):
            rc.lpush(Room.get_messages_list_key(id), str({"username": username, "body": body})) # add message to room's messages list

    def delete(id):
        if Room.exists(id):
            key = Room.get_key(id)

            rc.lrem(Room.get_room_list_key(), 1, id) # deletes room from list 

            all_keys = list(rc.hgetall(key).keys()) 
            rc.hdel(key, *all_keys) # deletes dict

            for huddle_id in Room.list_huddles(id):
                Room.delete_huddle(id, huddle_id)

            for user_id in Room.list_users(id):
                Room.delete_user(id, user_id)

    def list():
        return get_list(Room.get_room_list_key())

    def list_huddles(id):
        return get_list(Room.get_huddle_list_key(id))

    def list_users(id):
        return get_list(Room.get_user_list_key(id))

    def list_messages(id):
        return get_list(Room.get_messages_list_key(id))

    def get_next_huddle_id(id):
        val = int(rc.hget(Room.get_key(id), "HUDDLECOUNTER")) + 1
        rc.hmset(Room.get_key(id), {"HUDDLECOUNTER": val})
        return val  

    def num():
        return rc.llen(Room.get_room_list_key())

    def num_users(id):
        return rc.llen(Room.get_user_list_key(id))

    def num_huddles(id):
        return rc.llen(Room.get_huddle_list_key(id))

    def get_zeroth_huddle(id):
        return int(get_list(Room.get_huddle_list_key(id))[0])

class Huddle():
    def get_key(room_id, id):
        return 'HUDDLE_' + str(room_id) + "_" + str(id)

    def get_user_list_key(room_id, id):
        return 'LISTHUDDLEUSERS_' + str(room_id) + "_" + str(id)

    def exists(room_id, id):
        return rc.exists(Huddle.get_key(room_id, id))

    def create(room_id, id, data):
        rc.hmset(Huddle.get_key(room_id, id), data)

    def add_user(room_id, id, user_id):
        if Huddle.exists(room_id, id):
            rc.lpush(Huddle.get_user_list_key(room_id, id), user_id) # add user id to huddle's users list
            User.set_huddle(room_id, user_id, id)

    def delete_user(room_id, id, user_id):
        rc.lrem(Huddle.get_user_list_key(room_id, id), 1, user_id) # delete user from users list

    def get(room_id, id):
        return rc.hgetall(Huddle.get_key(room_id, id))

    def delete(room_id, id):
        if Huddle.exists(room_id, id):
            key = Huddle.get_key(room_id, id)
            all_keys = list(rc.hgetall(key).keys()) 
            rc.hdel(key, *all_keys) # deletes dict

            for user_id in Huddle.list_users(room_id, id):
                Huddle.delete_user(room_id, id, user_id)

    def list_users(room_id, id):
        return get_list(Huddle.get_user_list_key(room_id, id))

    def num_users(room_id, id):
        return rc.llen(Huddle.get_user_list_key(room_id, id))

    
class User():
    def get_key(room_id, id):
        return 'USER_' + str(room_id) + "_" + str(id)

    def exists(room_id, id):
        return rc.exists(User.get_key(room_id, id))

    def get_huddle(room_id, id):
        return int(rc.hget(User.get_key(room_id, id), 'HUDDLE'))

    def set_huddle(room_id, id, huddle_id):
        rc.hmset(User.get_key(room_id, id), {'HUDDLE': huddle_id})

    def create(room_id, id, data):
        rc.hmset(User.get_key(room_id, id), data)

    def get(room_id, id):
        return rc.hgetall(User.get_key(room_id, id))

    def delete(room_id, id):
        if User.exists(room_id, id):
            key = User.get_key(room_id, id)
            all_keys = list(rc.hgetall(key).keys()) 
            rc.hdel(key, *all_keys) # deletes dict