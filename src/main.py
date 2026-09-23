from dotenv import load_dotenv
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

# Load the local configuration before the route modules read application values.
# The .env file is ignored by Git and therefore keeps secrets out of the codebase.
load_dotenv(".env")

from routes import base, data

# FastAPI is the HTTP entry point of RAG Document Intelligence. Future steps
# will add document ingestion, semantic search and answer-generation routes.
app = FastAPI(
    title="RAG Document Intelligence",
    version="0.1.0",
)


@app.on_event("startup")
async def connect_mongodb() -> None:
    """Create one asynchronous MongoDB client shared by all request handlers."""
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]


@app.on_event("shutdown")
async def disconnect_mongodb() -> None:
    """Release the MongoDB connection pool when FastAPI stops."""
    app.mongo_conn.close()

# Routers keep each API domain in its own module. This lets the application grow
# without concentrating document, search and generation endpoints in main.py.
app.include_router(base.base_router)
app.include_router(data.data_router)
