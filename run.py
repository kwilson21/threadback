import importlib
import os
import sys

import hupper
import uvicorn
from dotenv import find_dotenv, load_dotenv
from starlette.middleware.cors import CORSMiddleware
from strawberry.asgi import GraphQL

from threadback.app import app

load_dotenv()

host = os.getenv("APP_HOST", "localhost")
port = os.getenv("APP_PORT", 8000)

app_env = os.getenv("APP_ENV")
debug = app_env == "development"


def run():
    module = "threadback.graphql_schema.schema"
    schema_module = importlib.import_module(module)
    if debug:
        sys.path.append(os.getcwd())

        reloader = hupper.start_reloader("run.run", verbose=False)

        reloader.watch_files([schema_module.__file__])

        app.add_middleware(
            CORSMiddleware,
            allow_headers=["*"],
            allow_origins=["*"],
            allow_methods=["*"],
        )

    graphql_app = GraphQL(schema_module.schema, debug=debug)

    paths = ["/", "/graphql"]

    for path in paths:
        app.add_route(path, graphql_app)
        app.add_websocket_route(path, graphql_app)

    print(f"Running app on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="error")


if __name__ == "__main__":
    run()
