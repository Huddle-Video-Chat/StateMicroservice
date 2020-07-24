from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

import hello.views

# To add a new path, first import the app:
# import blog
#
# Then add the new path:
# path('blog/', blog.urls, name="blog")
#
# Learn more here: https://docs.djangoproject.com/en/2.1/topics/http/urls/

urlpatterns = [
    # path("", hello.views.index, name="index"),
    # path("db/", hello.views.db, name="db"),
    # path("admin/", admin.site.urls),

    path('ping', hello.views.ping),
    path('room/state', hello.views.state),
    # path('room/create', hello.views.createRoom),
    # path('room/delete', hello.views.deleteRoom),

    path('room/exists', hello.views.roomExists),

    path('room/join', hello.views.joinRoom),
    path('room/leave', hello.views.leaveRoom),

    path('huddle/join', hello.views.joinHuddle),

    path('huddle/create', hello.views.createHuddle),

    path('messages/send', hello.views.sendMessage),
    path('messages/get', hello.views.getMessages),

    path('clear', hello.views.clear),
]
