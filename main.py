from fastapi import FastAPI
from dotenv import load_dotenv

# Load the local configuration before the route modules read application values.
# The .env file is ignored by Git and therefore keeps secrets out of the codebase.
load_dotenv(".env")

from routes import base

# FastAPI is the HTTP entry point of RAG Document Intelligence. Future steps
# will add document ingestion, semantic search and answer-generation routes.
app = FastAPI(
    title="RAG Document Intelligence",
    version="0.1.0",
)

# Routers keep each API domain in its own module. This lets the application grow
# without concentrating document, search and generation endpoints in main.py.
app.include_router(base.base_router)
