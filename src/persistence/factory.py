from dataclasses import dataclass
from urllib.parse import quote_plus

from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .mongodb import MongoPersistence
from .postgresql import PostgresPersistence


@dataclass
class PersistenceResources:
    persistence: object


async def create_persistence(settings):
    """Create and validate the backend selected for this process."""
    if settings.PERSISTENCE_BACKEND == "mongodb":
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        database = client[settings.MONGODB_DATABASE]
        persistence = MongoPersistence(client, database)
        await persistence.initialize()
        return PersistenceResources(persistence=persistence)

    required = (
        settings.POSTGRES_USERNAME,
        settings.POSTGRES_PASSWORD,
        settings.POSTGRES_MAIN_DATABASE,
    )
    if not all(required):
        raise RuntimeError(
            "PostgreSQL credentials are required when PERSISTENCE_BACKEND=postgresql"
        )
    url = (
        f"postgresql+asyncpg://{quote_plus(settings.POSTGRES_USERNAME)}:"
        f"{quote_plus(settings.POSTGRES_PASSWORD)}@{settings.POSTGRES_HOST}:"
        f"{settings.POSTGRES_PORT}/{quote_plus(settings.POSTGRES_MAIN_DATABASE)}"
    )
    engine = create_async_engine(url)
    sessions = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    persistence = PostgresPersistence(engine, sessions)
    await persistence.initialize()
    return PersistenceResources(persistence=persistence)
