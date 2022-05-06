from django.urls import path
from .views import *
# HTTP URL
urlpatterns = [
    path('',chatpage.as_view(),name="chat"),
    path('message_ajax/<str:userid>',message_ajax,name='message_ajax')
]