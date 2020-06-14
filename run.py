import os
import sys

import hupper
import uvicorn
from dotenv import find_dotenv, load_dotenv
from starlette.middleware.cors import CORSMiddleware

from threadback.app import app
