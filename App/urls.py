# chatbot_project/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/', include('chatbot_api.urls')), # <--- Esta linha é crucial!
]
