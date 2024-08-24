__version__ = 'v1'

import asyncio
from sqlalchemy.schema import CreateSchema

from . import models, schemas
from models import engine, session


async def startup():
    async with engine.connect() as conn:
        conn.execute(CreateSchema(__version__, if_not_exists=True))


asyncio.run(startup())
