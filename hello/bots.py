from django.shortcuts import render
# from django.http import Response

from rest_framework.decorators import api_view
from rest_framework.response import Response
from . import rdsfixed as rds
from .helpers import check_params
from . import helpers

from datetime import datetime

@api_view(['GET', 'POST', 'DELETE']) 
@check_params(['id', 'huddle_id'])
def codenames(request):
    id = helpers.getQueryValue(request, 'id')
    huddle_id = helpers.getQueryValue(request, 'huddle_id')

    if request.method == 'GET':
        return Response(rds.Room.get_bot(id, huddle_id))
    elif request.method == 'POST':
        url = "https://www.horsepaste.com/" + str(hash(datetime.now()))
        rds.Room.set_bot(id, huddle_id, url)
        return Response(url)
    elif request.method == 'DELETE':
        rds.Room.delete_bot(id, huddle_id)
        return Response('Deleted bot')
