from starlette.config import Config

config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
DB_NAME = config("DB_NAME")
MONGODB_URI = config("MONGODB_URI")
REDISTOGO_URL = config("REDISTOGO_URL")
HOST = config("HOST", default="localhost")
PORT = config("PORT", cast=int, default=8000)
