"""Base routes used to validate the API configuration."""

import os

from fastapi import APIRouter

# All version-one endpoints share this prefix. Future route modules will use
# their own domain-specific paths below /api/v1.
base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)


@base_router.get("/")
async def welcome() -> dict[str, str | None]:
    """Return the configured application identity as a lightweight health check."""
    return {
        "app_name": os.getenv("APP_NAME"),
        "app_version": os.getenv("APP_VERSION"),
    }
