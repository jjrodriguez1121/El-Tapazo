from django.urls import path

from asistente.api import vistas

app_name = "asistente"

urlpatterns = [
    path("chat/", vistas.chat),
]
