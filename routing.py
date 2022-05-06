from django.urls import re_path,path
from . import consumers

#将所有的websocket连接交给consumers.py去处理

websocket_urlpatterns = [
    #userone是你自己的id,usertwo是你想私聊的人的id
    re_path(r'ws/chat/(?P<usertwo_id>\w+)$', consumers.ChatConsumer),
    re_path(r'ws/chat',consumers.PushConsumer)
]