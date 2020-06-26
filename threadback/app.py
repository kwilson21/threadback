import importlib
import urllib.parse

from mongoengine import connect, disconnect
from redis import Redis
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from strawberry.asgi import GraphQL

from threadback import settings


def connect_to_db():
    connect(settings.DB_NAME, host=settings.MONGODB_URI)


def disconnect_from_db():
    disconnect(settings.DB_NAME)


urllib.parse.uses_netloc.append("redis")
url = urllib.parse.urlparse(settings.REDIS_URL)
conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)

app = Starlette(
    debug=settings.DEBUG, on_startup=[connect_to_db], on_shutdown=[disconnect_from_db],
)

module = "threadback.graphql_schema.schema"
schema_module = importlib.import_module(module)
graphql_app = GraphQL(schema_module.schema, debug=settings.DEBUG)

paths = ["/", "/graphql"]

for path in paths:
    app.add_route(path, graphql_app)
    app.add_websocket_route(path, graphql_app)

if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware, allow_headers=["*"], allow_origins=["*"], allow_methods=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
    )
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=list(settings.ALLOWED_HOSTS),
    )
