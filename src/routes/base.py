"""Expose the HTTP endpoints implemented by the base router."""

import logging

from fastapi import APIRouter, Depends

from helpers.config import Settings, get_settings

logger = logging.getLogger("uvicorn.error")

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)

@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):

    """Return API metadata and the currently active backend configuration."""
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION

    return {
        "app_name": app_name,
        "app_version": app_version,
        "persistence_backend": app_settings.PERSISTENCE_BACKEND,
        "vector_db_backend": app_settings.VECTOR_DB_BACKEND,
    }
