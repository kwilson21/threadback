import os

from dotenv import find_dotenv, load_dotenv
from huey import MemoryHuey, RedisHuey
from mongoengine import connect
from starlette.applications import Starlette

load_dotenv()

app_env = os.getenv("APP_ENV")

if app_env == "development":
    connect("threadback")
else:
    connect(os.getenv("DB_NAME"), host=os.getenv("DB_HOST"))

huey = RedisHuey("jobs", host=os.getenv("REDIS_URL"), blocking=True, utc=False)

debug = app_env == "development"

app = Starlette(debug=debug)
