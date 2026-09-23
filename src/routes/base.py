"""Base API routes."""

from fastapi import APIRouter, Depends

from helpers.config import Settings, get_settings

base_router = APIRouter(prefix="/api/v1", tags=["api_v1"])


@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Return the application identity to confirm configuration is available."""
    return {
        "app_name": app_settings.APP_NAME,
        "app_version": app_settings.APP_VERSION,
    }
