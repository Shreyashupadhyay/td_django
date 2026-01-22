from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/room/(?P<room_code>\w+)/$', consumers.GameConsumer.as_asgi()),
    re_path(r'ws/standalone/(?P<session_id>[\w-]+)/$', consumers.StandaloneConsumer.as_asgi()),
]
