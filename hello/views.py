from django.shortcuts import render
# from django.http import Response

from rest_framework.decorators import api_view
from rest_framework.response import Response
from . import rds
from .helpers import check_params
from . import helpers

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
@check_params(['id', 'user_id', 'username', 'first', 'last'])
def joinRoom(request):
    id = helpers.getQueryValue(request, 'id')
    user_data = helpers.getQueryDict(request, keys=['username', 'first', 'last'])
    user_id = helpers.getQueryValue(request, 'user_id')

    if not rds.Room.exists(id):
        rds.Room.create(id, {'name': 'default'})

    rds.Room.add_user(id, user_id, user_data)

    if rds.Room.num_huddles(id) == 0:
        rds.Room.add_huddle(id, {'id': id})

    huddle_id = rds.Room.get_zeroth_huddle(id)
    rds.Huddle.add_user(id, huddle_id, user_id)

    return Response(getStateJson(id, user_id))

@api_view(['DELETE']) 
@check_params(['id', 'user_id'])
def leaveRoom(request):
    id = helpers.getQueryValue(request, 'id')
    user_id = helpers.getQueryValue(request, 'user_id')
    huddle_id = rds.User.get_huddle(id, user_id)

    rds.Room.delete_user(
        id, 
        user_id,
        huddle_id
    )

    if rds.Huddle.num_users(id, huddle_id) == 0:
        rds.Room.delete_huddle(id, huddle_id)

    if rds.Room.num_users(id) == 0:
        rds.Room.delete(id)

    return Response(True)


@api_view(['POST']) 
@check_params(['id', 'user_id', 'new_huddle_id'])
def joinHuddle(request):
    id = helpers.getQueryValue(request, 'id')
    new_huddle_id = helpers.getQueryValue(request, 'new_huddle_id')
    user_id = helpers.getQueryValue(request, 'user_id')
    old_huddle_id = rds.User.get_huddle(id, user_id)

    rds.Huddle.delete_user(id, old_huddle_id, user_id)
    rds.Huddle.add_user(id, new_huddle_id, user_id)

    if rds.Huddle.num_users(id, old_huddle_id) == 0:
        rds.Room.delete_huddle(id, old_huddle_id)

    return Response(getStateJson(id, user_id))

@api_view(['POST']) 
@check_params(['id', 'user_id'])
def createHuddle(request):
    id = helpers.getQueryValue(request, 'id')
    user_id = helpers.getQueryValue(request, 'user_id')
    old_huddle_id = rds.User.get_huddle(id, user_id)

    rds.Huddle.delete_user(id, old_huddle_id, user_id)
    new_huddle_id = rds.Room.add_huddle(id, {'id': id})
    rds.Huddle.add_user(id, new_huddle_id, user_id)

    if rds.Huddle.num_users(id, old_huddle_id) == 0:
        rds.Room.delete_huddle(id, old_huddle_id)

    return Response(getStateJson(id, user_id))

@api_view(['GET']) 
@check_params(['id', 'user_id'])
def state(request):
    id = helpers.getQueryValue(request, 'id')
    user_id = helpers.getQueryValue(request, 'user_id')
    return Response(getStateJson(id, user_id))

def getStateJson(id, user_id):
    response = {
        "id": id,
        "user_id": user_id,
        "huddle_id": int(rds.User.get_huddle(id, user_id)),
        "users": {}, # [u for u in rds.Room.list_users(id)],
        "rooms": []
    }
    for huddle_id in rds.Room.list_huddles(id):
        huddle_id = int(huddle_id)
        # users = [u for u in rds.Huddle.list_users(id, huddle_id)]

        for u in rds.Huddle.list_users(id, huddle_id):
            response['users'][u] = huddle_id

        response['rooms'] += [{"id" : huddle_id, "users": users}]

    return response

@api_view(['DELETE'])
def clear(request):
    rds.reset()
    return Response("Cleared database")