from django.shortcuts import render
# from django.http import Response

from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from typing import Dict, List
from . import rdsfixed as rds
from .helpers import check_params
from . import helpers

@api_view(['GET']) 
def ping(request: Request) -> Response:
    return Response("Hello World!")

# @api_view(['POST']) 
# @check_params(['name'])
# def createRoom(request):
#     id = rds.Room.create(helpers.getQueryDict(request))
#     return Response({"id": id})

@api_view(['GET'])
@check_params(['id'])
def roomExists(request: Request) -> Response:
    """
    Checks if a room exists in the redis database.
    :param request: includes the id of the room
    :return: response that contains a 1 if room exists, 0 if it does not
    """
    room_id: str = helpers.getQueryValue(request, 'id')
    r: int = rds.Room.exists(room_id)
    return Response(r)

@api_view(['POST']) 
@check_params(['id', 'user_id'])
def joinRoom(request: Request) -> Response:
    #TODO error handling for adding duplicate users to a room
    """
    A user tries to joins a room.
    If the room does not exist, create a new room.
    If joined, the user is automatically placed in the original huddle in the room.
    :param request: contains the id of the room and the user
    :return: json that reflects the state of the room.
    """
    room_id: str = helpers.getQueryValue(request, 'id')
    user_id: str = helpers.getQueryValue(request, 'user_id')

    if not rds.Room.exists(room_id):
        rds.Room.create(room_id, {'name': 'default'})
    try:
        rds.Room.add_user_to_huddle(room_id, user_id, rds.Room.get_zeroth_huddle(room_id))
    except Exception as m:
        helpers.throwHBasicError(m)

    rds.Room.updateStateCounter(room_id)

    return Response(getStateJson(room_id, user_id))

@api_view(['DELETE']) 
@check_params(['id', 'user_id'])
def leaveRoom(request: Request) -> Response:
    #TODO error handling for when the user does not exist in the room and when room does not exist
    """
    A user tries to leave the room.
    Changes room state.
    :param request: contains the id of the room and the user
    :return: True response
    """
    room_id: str = helpers.getQueryValue(request, 'id')
    user_id: str = helpers.getQueryValue(request, 'user_id')

    try:
        rds.Room.delete_user(
            room_id,
            user_id,
        )
    except Exception as m:
        helpers.throwHBasicError(m)

    # TODO potentially change this when preserving rooms
    if rds.Room.num_users(room_id) == 0:
        try:
            rds.Room.delete(room_id)
        except Exception as m:
            helpers.throwHBasicError(m)

    rds.Room.updateStateCounter(room_id)
    return Response(True)


@api_view(['POST']) 
@check_params(['id', 'user_id', 'new_huddle_id'])
def joinHuddle(request: Request) -> Response:
    #TODO error handling for when user/huddle/room does not exist
    """
    Moves a user within a room to a new huddle.
    :param request: request: contains the id of the room, user, and the new huddle.
    :return: json that reflects the state of the room.
    """
    room_id: str = helpers.getQueryValue(request, 'id')
    new_huddle_id: str = helpers.getQueryValue(request, 'new_huddle_id')
    user_id: str = helpers.getQueryValue(request, 'user_id')

    try:
        rds.Room.add_user_to_huddle(room_id, user_id, new_huddle_id)
        rds.Room.updateStateCounter(room_id)
    except Exception as m:
        helpers.throwHBasicError(m)

    return Response(getStateJson(room_id, user_id))

@api_view(['POST']) 
@check_params(['id', 'user_id'])
def createHuddle(request: Request) -> Response:
    #TODO verify if user/room exists
    """
    Creates a new huddle and moves a user into it.
    :param request: request: contains the id of the room, and a user.
    :return: json that reflects the updated state of the room.
    """
    room_id: str = helpers.getQueryValue(request, 'id')
    user_id: str = helpers.getQueryValue(request, 'user_id')

    try:
        rds.Room.add_user_to_new_huddle(room_id, user_id)
        rds.Room.updateStateCounter(room_id)
    except Exception as m:
        helpers.throwHBasicError(m)

    return Response(getStateJson(room_id, user_id))

@api_view(['GET']) 
@check_params(['id', 'user_id'])
def state(request: Request) -> Response:
    """
    Checks the state of the room.
    :param request: contains the id of the room, and a user.
    :return: json that reflects the current state of the room.
    """
    room_id: str = helpers.getQueryValue(request, 'id')
    user_id: str = helpers.getQueryValue(request, 'user_id')
    return Response(getStateJson(room_id, user_id))


@api_view(['POST'])
@check_params(['id', 'username', 'body'])
def sendMessage(request: Request) -> Response:
    # TODO: error handling for empty message
    # TODO: include a timestamp for all messages
    """
    Sends a new message to the room from a user.
    :param request: contains the id of the room, the username of the sender,
    and the body of the message.
    :return: list that contains all the messages in a room.
    """
    room_id: str = helpers.getQueryValue(request, 'id')
    username: str = helpers.getQueryValue(request, 'username')
    body: str = helpers.getQueryValue(request, 'body')
    messages: List = list()
    try:
        rds.Room.add_message(room_id, username, body)
        messages = rds.Room.list_messages(room_id)
    except Exception as m:
        helpers.throwHBasicError(m)

    return Response(messages)


@api_view(['GET'])
@check_params(['id'])
def getMessages(request: Request) -> Response:
    """
    Retrieves full list of messages sent in a room.
    :param request: contains the id of the room
    :return: list that contains all the messages in a room.
    """
    room_id: str = helpers.getQueryValue(request, 'id')
    messages: List = list()
    try:
        messages: List = rds.Room.list_messages(room_id)
    except Exception as m:
        helpers.throwHBasicError(m)

    return Response(messages)


@api_view(['DELETE'])
def clear(request: Request) -> Response:
    rds.reset()
    return Response("Cleared database")

def getStateJson(id: str, user_id: str) -> Dict:
    """
    Based on a user and the room they're in, return the latest
    state representation.
    ----------------------
    state_counter: running number of when the state response changes
    id: id of the room
    user_id: id of the user
    users: map of all users in the room to the huddle they belong in
    huddle_id: id of the huddle the specified user is in
    ----------------------
    :param id: id of the room
    :param user_id: id of the user
    :return: json that reflects the current state of the room.
    """
    response: Dict = {
        "state_counter": rds.Room.getStateCounter(id),
        "id": id,
        "user_id": user_id,
        "users": {},
    }

    room_state: Dict = rds.Room.get_map(id)

    for k in room_state.keys():
        response['users'][k.decode("utf-8")] = int(room_state[k])

    response['huddle_id'] = response['users'][user_id]
    return response

