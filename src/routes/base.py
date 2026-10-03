"""Expose the HTTP endpoints implemented by the base router."""

from fastapi import APIRouter, Depends
from helpers.config import get_settings, Settings
from tasks.mail_service import send_email_reports

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
    }


@base_router.get("/send_reports")
async def send_reports():
    """Queue the report-email simulation and return without blocking FastAPI."""
    task = send_email_reports.delay(mail_wait_seconds=3)

    return {
        "success": True,
        "task_id": task.id,
    }
