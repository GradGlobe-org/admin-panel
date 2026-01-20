import os
import django
from django.core.asgi import get_asgi_application
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from django.views.decorators.csrf import csrf_exempt

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")

django.setup()
django_asgi_app = get_asgi_application()

from strawberry.channels import GraphQLWSConsumer
from .GlobalSchema import schema

websocket_urlpatterns = [
    path("graphql/", csrf_exempt(GraphQLWSConsumer.as_asgi(schema=schema))),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),
})
