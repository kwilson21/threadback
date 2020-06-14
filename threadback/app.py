import importlib
import os

from dotenv import find_dotenv, load_dotenv
from huey import MemoryHuey, RedisHuey
from mongoengine import connect
from starlette.applications import Starlette
from strawberry.asgi import GraphQL

load_dotenv()

app_env = os.getenv("APP_ENV")

debug = app_env == "development"

if app_env == "development":
    connect("threadback")
else:
    connect(os.getenv("DB_NAME"), host=os.getenv("DB_HOST"))

huey = RedisHuey("jobs", url=os.getenv("REDIS_URL"), blocking=True, utc=False)

app = Starlette(debug=debug)

module = "threadback.graphql_schema.schema"
schema_module = importlib.import_module(module)
graphql_app = GraphQL(schema_module.schema, debug=debug)

paths = ["/", "/graphql"]

for path in paths:
    app.add_route(path, graphql_app)
    app.add_websocket_route(path, graphql_app)

if debug:
    sys.path.append(os.getcwd())

    reloader = hupper.start_reloader("run.run", verbose=False)

    reloader.watch_files([schema_module.__file__])

    app.add_middleware(
        CORSMiddleware, allow_headers=["*"], allow_origins=["*"], allow_methods=["*"],
    )
