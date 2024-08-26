from sqlalchemy.ext.asyncio import AsyncSession
from .models import engine


def get_session() -> AsyncSession:
    return AsyncSession(engine)
