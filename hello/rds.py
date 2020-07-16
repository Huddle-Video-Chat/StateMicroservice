import redis

class RedisClient(redis.Redis):
    def __init__(self):
        super(self.__class__, self).__init__(
            host='redis://h:pf1c13f2a465ee1822060f5118972cea576ebb4eb5f7f7e4f310446f7dc366232@ec2-23-21-1-196.compute-1.amazonaws.com',
            port=18429
        )

    def get_list(self, key):
        return super(self.__class__, self).lrange(key, 0, -1)

    def delete_all_in_list(self, key):
        for _id in self.get_list(key):
            super(self.__class__, self).delete(id)

    def reset(self):
        super(self.__class__, self).flushdb()
        super(self.__class__, self).set(Room.get_room_counter_key(), 0)

rc = RedisClient()

class Room():
    def get_key(id):
        return 'ROOM' + str(id)
    
    def get_user_list_key(id):
        return 'LISTROOMUSERS' + str(id)

    def get_huddle_list_key(id):
        return 'LISTROOMHUDDLES' + str(id)

    def get_room_list_key():
        return 'LISTROOMS'

    def get_room_counter_key():
        return 'ROOMCOUNTER'

    def exists(id):
        return rc.exists(Room.get_key(id))

    def create(data):
        id = Room.get_next_id(Room.get_room_counter_key())

        key = Room.get_key(id)
        rc.lpush(Room.get_room_list_key(), id) # adds room id to rooms list
        rc.hmset(key, data) # creates room dict

        rc.hmset(key, {"USERCOUNTER": 0, "HUDDLECOUNTER": 0})

        return id

    def add_user(id, user_data):
        if Room.exists(id):
            user_id = Room.get_next_id(Room.get_key(id), key="USERCOUNTER")
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
            huddle_id = Room.get_next_id(Room.get_key(id), key="HUDDLECOUNTER")
            Huddle.create(id, huddle_id, huddle_data) # creates huddle dict
            rc.lpush(Room.get_huddle_list_key(id), huddle_id) # add huddle id to room's huddles list
            return huddle_id

    def delete_huddle(id, huddle_id):
        rc.lrem(Room.get_huddle_list_key(id), 1, huddle_id) # delete huddle from huddles list
        Huddle.delete(id, huddle_id) # delete huddle dict

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
        return rc.get_list(Room.get_room_list_key())

    def list_huddles(id):
        return rc.get_list(Room.get_huddle_list_key(id))

    def list_users(id):
        return rc.get_list(Room.get_user_list_key(id))

    def get_next_id(id, key=None):
        if not key:
            val = int(rc.get(id)) + 1
            rc.set(id, val)
            return val
        else:
            print(id, key)
            val = int(rc.hget(id, key)) + 1
            rc.hmset(id, {key: val})
            return val  

    def num():
        return rc.llen(Room.get_room_list_key())

    def num_users(id):
        return rc.llen(Room.get_user_list_key(id))

    def num_huddles(id):
        return rc.llen(Room.get_huddle_list_key(id))

    def get_zeroth_huddle(id):
        return int(rc.get_list(Room.get_huddle_list_key(id))[0])

class Huddle():
    def get_key(room_id, id):
        return 'HUDDLE' + str(room_id) + "_" + str(id)

    def get_user_list_key(room_id, id):
        return 'LISTHUDDLEUSERS' + str(room_id) + "_" + str(id)

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
        return rc.get_list(Huddle.get_user_list_key(room_id, id))

    def num_users(room_id, id):
        return rc.llen(Huddle.get_user_list_key(room_id, id))

    
class User():
    def get_key(room_id, id):
        return 'USER' + str(room_id) + "_" + str(id)

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