import os

import uvicorn

from threadback import settings
from threadback.app import app


def start_dev():
    uvicorn.run(
        "run:app", host=settings.HOST, port=settings.PORT, reload=True,
    )
