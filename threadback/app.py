import importlib
import os

from huey import MemoryHuey, RedisHuey
from mongoengine import connect, disconnect
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from strawberry.asgi import GraphQL

from threadback import settings


def connect_to_db():
    connect(settings.DB_NAME, host=settings.MONGODB_URI)


def disconnect_from_db():
    disconnect(settings.DB_NAME)


huey = RedisHuey("jobs", url=settings.REDIS_URL, blocking=True, utc=False)


@huey.on_startup()
def _connect_to_db():
    connect(settings.DB_NAME, host=settings.MONGODB_URI)


@huey.on_shutdown()
def disconnect_from_db():
    disconnect(settings.DB_NAME)


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
