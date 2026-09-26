from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from application.ports import Persistence

from .mongodb import MongoPersistence
from .postgresql import PostgresPersistence


async def create_persistence(settings) -> Persistence:
    """Composition root for the selected persistence adapter."""
    # Centralized selection: callers use this function without importing a
    # MongoDB or PostgreSQL implementation directly. PERSISTENCE_BACKEND is
    # the only setting that chooses the active persistence adapter.
    if settings.PERSISTENCE_BACKEND == "mongodb":
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        database = client[settings.MONGODB_DATABASE]
        persistence = MongoPersistence(client, database)
    elif settings.PERSISTENCE_BACKEND == "postgresql":
        url = URL.create(
            drivername="postgresql+asyncpg",
            username=settings.POSTGRES_USERNAME,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_MAIN_DATABASE,
        )
        engine = create_async_engine(url)
        sessions = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        persistence = PostgresPersistence(engine, sessions)
    else:
        raise ValueError(
            f"Unsupported persistence backend: {settings.PERSISTENCE_BACKEND}"
        )

    try:
        await persistence.initialize()
    except Exception:
        await persistence.close()
        raise
    return persistence
