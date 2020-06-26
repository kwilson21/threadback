from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings

config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
DB_NAME = config("DB_NAME")
MONGODB_URI = config("MONGODB_URI")
REDIS_URL = config("REDIS_URL", default="redis://127.0.0.1:6379")
HOST = config("HOST", default="localhost")
PORT = config("PORT", cast=int, default=8000)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", cast=CommaSeparatedStrings, default="127.0.0.1,localhost",
)
