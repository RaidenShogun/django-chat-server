#配置routing,让其处理websocket

from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
import chat.routing

application = ProtocolTypeRouter({
    'websocket':SessionMiddlewareStack(  #用了这个中间件才可以在ws中使用session
        URLRouter(
                chat.routing.websocket_urlpatterns  #相当于urls.py的作用，给这个websocket请求相应的Consumer处理
            )
        )

    })