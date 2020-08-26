from django.shortcuts import render
# from django.http import Response

from rest_framework.decorators import api_view
from rest_framework.response import Response
from . import rdsfixed as rds
from .helpers import check_params
from . import helpers

from datetime import datetime

@api_view(['GET']) 
def ping(request):
    return Response("Hello World!")

# @api_view(['POST']) 
# @check_params(['name'])
# def createRoom(request):
#     id = rds.Room.create(helpers.getQueryDict(request))
#     return Response({"id": id})

@api_view(['GET']) 
@check_params(['id'])
def roomExists(request):
    r = rds.Room.exists(helpers.getQueryValue(request, 'id'))
    return Response(r)

@api_view(['POST']) 
@check_params(['id', 'user_id'])
def joinRoom(request):
    id = helpers.getQueryValue(request, 'id')
    user_id = helpers.getQueryValue(request, 'user_id')

    # if not rds.User.exists(id, user_id):
    if not rds.Room.exists(id):
        rds.Room.create(id, {'name': 'default'})

    rds.Room.add_user_to_huddle(id, user_id, rds.Room.get_zeroth_huddle(id))

    # if rds.Room.num_huddles(id) == 0:
    #     rds.Room.add_huddle(id, {'id': id})

    # huddle_id = rds.Room.get_zeroth_huddle(id)
    # rds.Huddle.add_user(id, huddle_id, user_id)

    rds.Room.updateStateCounter(id)

    return Response(getStateJson(id, user_id))

@api_view(['DELETE']) 
@check_params(['id', 'user_id'])
def leaveRoom(request):
    id = helpers.getQueryValue(request, 'id')
    user_id = helpers.getQueryValue(request, 'user_id')

    rds.Room.delete_user(
        id, 
        user_id,
    )

    # if rds.Huddle.num_users(id, huddle_id) == 0:
    #     rds.Room.delete_huddle(id, huddle_id)

    if rds.Room.num_users(id) == 0:
        rds.Room.delete(id)

    rds.Room.updateStateCounter(id)

    return Response(True)


@api_view(['POST']) 
@check_params(['id', 'user_id', 'new_huddle_id'])
def joinHuddle(request):
    id = helpers.getQueryValue(request, 'id')
    new_huddle_id = helpers.getQueryValue(request, 'new_huddle_id')
    user_id = helpers.getQueryValue(request, 'user_id')
    # old_huddle_id = rds.User.get_huddle(id, user_id)

    # rds.Huddle.delete_user(id, old_huddle_id, user_id)
    # rds.Huddle.add_user(id, new_huddle_id, user_id)

    rds.Room.add_user_to_huddle(id, user_id, new_huddle_id)

    # if rds.Huddle.num_users(id, old_huddle_id) == 0:
    #     rds.Room.delete_huddle(id, old_huddle_id)

    rds.Room.updateStateCounter(id)

    return Response(getStateJson(id, user_id))

@api_view(['POST']) 
@check_params(['id', 'user_id'])
def createHuddle(request):
    id = helpers.getQueryValue(request, 'id')
    user_id = helpers.getQueryValue(request, 'user_id')

    rds.Room.add_user_to_new_huddle(id, user_id)

    # old_huddle_id = rds.User.get_huddle(id, user_id)

    # rds.Huddle.delete_user(id, old_huddle_id, user_id)
    # new_huddle_id = rds.Room.add_huddle(id, {'id': id})
    # rds.Huddle.add_user(id, new_huddle_id, user_id)

    # if rds.Huddle.num_users(id, old_huddle_id) == 0:
    #     rds.Room.delete_huddle(id, old_huddle_id)

    rds.Room.updateStateCounter(id)

    return Response(getStateJson(id, user_id))

@api_view(['GET']) 
@check_params(['id', 'user_id'])
def state(request):
    id = helpers.getQueryValue(request, 'id')
    user_id = helpers.getQueryValue(request, 'user_id')
    return Response(getStateJson(id, user_id))

def getStateJson(id, user_id):
    response = {
        "state_counter": rds.Room.getStateCounter(id),
        "id": id,
        "user_id": user_id,
        # "huddle_id": int(rds.User.get_huddle(id, user_id)),
        "users": {}, # [u for u in rds.Room.list_users(id)],
        # "rooms": []
    }

    _map = rds.Room.get_map(id)

    for k in _map.keys():
        response['users'][k.decode("utf-8")] = int(_map[k])

    huddle_id = response['users'][user_id]
    response['huddle_id'] = huddle_id
    response['bot_url'] = rds.Room.get_bot(id, huddle_id)

    # for huddle_id in rds.Room.list_huddles(id):
    #     huddle_id = int(huddle_id)
    #     users = [u for u in rds.Huddle.list_users(id, huddle_id)]

    #     for u in rds.Huddle.list_users(id, huddle_id):
    #         response['users'][u.decode("utf-8") ] = huddle_id

    #     response['rooms'] += [{"id" : huddle_id, "users": users}]

    return response

    # return str(rds.Room.get_map(id))

@api_view(['POST']) 
@check_params(['id', 'username', 'body'])
def sendMessage(request):
    id = helpers.getQueryValue(request, 'id')
    username = helpers.getQueryValue(request, 'username')
    body = helpers.getQueryValue(request, 'body')

    rds.Room.add_message(id, username, body)
    messages = rds.Room.list_messages(id)
    
    return Response(messages)

@api_view(['GET']) 
@check_params(['id'])
def getMessages(request):
    id = helpers.getQueryValue(request, 'id')
    messages = rds.Room.list_messages(id)
    return Response(messages)

@api_view(['DELETE'])
def clear(request):
    rds.reset()
    return Response("Cleared database")


@api_view(['POST']) 
@check_params(['id', 'huddle_id', 'user_id'])
def addCodenames(request):
    id = helpers.getQueryValue(request, 'id')
    user_id = helpers.getQueryValue(request, 'user_id')
    huddle_id = helpers.getQueryValue(request, 'huddle_id')

    url = "https://www.horsepaste.com/" + str(hash(datetime.now()))
    rds.Room.set_bot(id, huddle_id, url)
    return Response(getStateJson(id, user_id))

@api_view(['DELETE']) 
@check_params(['id', 'huddle_id', 'user_id'])
def deleteBot(request):
    id = helpers.getQueryValue(request, 'id')
    user_id = helpers.getQueryValue(request, 'user_id')
    huddle_id = helpers.getQueryValue(request, 'huddle_id')

    rds.Room.delete_bot(id, huddle_id)
    return Response(getStateJson(id, user_id))