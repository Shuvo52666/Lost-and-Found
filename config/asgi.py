

import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

import socketio
from config.socketio import sio

application = socketio.ASGIApp(
    sio,
    other_asgi_app=django_asgi_app
)
