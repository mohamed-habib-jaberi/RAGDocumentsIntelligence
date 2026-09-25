import asyncio
import logging

from celery_app import celery_app
from helpers.config import get_settings
from infrastructure.persistence import create_persistence
from utils.idempotency_manager import IdempotencyManager

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.maintenance.clean_celery_executions_table",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def clean_celery_executions_table(self):

    return asyncio.run(_clean_celery_executions_table(self))


async def _clean_celery_executions_table(task_instance):

    persistence = None

    try:
        persistence = await create_persistence(get_settings())

        # Create idempotency manager
        idempotency_manager = IdempotencyManager(persistence.task_executions)

        logger.warning("cleaning !!!")
        _ = await idempotency_manager.cleanup_old_tasks(5)

        return True

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise
    finally:
        try:
            if persistence:
                await persistence.close()

        except Exception as e:
            logger.error(f"Task failed while cleaning: {str(e)}")
