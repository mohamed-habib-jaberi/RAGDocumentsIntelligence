"""Define Celery tasks for the maintenance workflow."""

from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import asyncio
from utils.idempotency_manager import IdempotencyManager

import logging
logger = logging.getLogger(__name__)

@celery_app.task(
                 bind=True, name="tasks.maintenance.clean_celery_executions_table",
                 autoretry_for=(Exception,),
                 retry_kwargs={'max_retries': 3, 'countdown': 60}
                )
def clean_celery_executions_table(self):

    """Schedule removal of task-execution records older than the retention period."""
    return asyncio.run(
        _clean_celery_executions_table(self)
    )

async def _clean_celery_executions_table(task_instance):

    """Delete expired Celery execution records inside the asynchronous worker context."""
    db_engine, vectordb_client = None, None

    try:

        (db_engine, db_client, llm_provider_factory, 
        vectordb_provider_factory,
        generation_client, embedding_client,
        vectordb_client, template_parser) = await get_setup_utils()

        # Create idempotency manager
        idempotency_manager = IdempotencyManager(db_client, db_engine)

        logger.warning(f"cleaning !!!")
        _ = await idempotency_manager.cleanup_old_tasks(5)

        return True

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise
    finally:
        try:
            if db_engine:
                db_engine.close()

            if vectordb_client:
                await vectordb_client.disconnect()
        except Exception as e:
            logger.error(f"Task failed while cleaning: {str(e)}")
