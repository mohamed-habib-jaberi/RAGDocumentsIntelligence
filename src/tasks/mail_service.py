"""Celery tasks for sending report notifications outside HTTP requests."""

import logging
from datetime import datetime, timezone
from time import sleep

from celery_app import celery_app


logger = logging.getLogger("celery.task")


@celery_app.task(
    bind=True,
    name="tasks.mail_service.send_email_reports",
)
def send_email_reports(task_instance, mail_wait_seconds: int = 3):
    """Simulate a report-email batch while publishing task progress."""
    started_at = datetime.now(timezone.utc).isoformat()
    task_instance.update_state(
        state="PROGRESS",
        meta={"started_at": started_at, "sent": 0, "total": 15},
    )

    for index in range(15):
        logger.info("Send email to user: %s", index)
        sleep(mail_wait_seconds)
        task_instance.update_state(
            state="PROGRESS",
            meta={"started_at": started_at, "sent": index + 1, "total": 15},
        )

    return {
        "no_emails": 15,
        "ended_at": datetime.now(timezone.utc).isoformat(),
    }
