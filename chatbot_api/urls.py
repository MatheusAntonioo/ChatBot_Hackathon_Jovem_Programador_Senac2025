# chatbot_app/urls.py

from django.urls import path
from . import views

app_name = 'chatbot_app'

urlpatterns = [
    path('', views.chatbot_view, name='chatbot_view'),
]