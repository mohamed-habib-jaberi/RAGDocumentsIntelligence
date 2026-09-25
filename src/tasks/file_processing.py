from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import asyncio
from persistence import ChunkRecord
from models import ResponseSignal
from models.enums.AssetTypeEnum import AssetTypeEnum
from controllers import ProcessController
from controllers import NLPController
from utils.idempotency_manager import IdempotencyManager

import logging

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.file_processing.process_project_files",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def process_project_files(
    self,
    project_id: int,
    file_id: int,
    chunk_size: int,
    overlap_size: int,
    do_reset: int,
):

    return asyncio.run(
        _process_project_files(
            self, project_id, file_id, chunk_size, overlap_size, do_reset
        )
    )


async def _process_project_files(
    task_instance,
    project_id: int,
    file_id: int,
    chunk_size: int,
    overlap_size: int,
    do_reset: int,
):

    persistence, vectordb_client = None, None

    try:
        (
            persistence,
            llm_provider_factory,
            vectordb_provider_factory,
            generation_client,
            embedding_client,
            vectordb_client,
            template_parser,
        ) = await get_setup_utils()

        # Create idempotency manager
        idempotency_manager = IdempotencyManager(persistence)

        # Define task arguments for idempotency check
        task_args = {
            "project_id": project_id,
            "file_id": file_id,
            "chunk_size": chunk_size,
            "overlap_size": overlap_size,
            "do_reset": do_reset,
        }

        task_name = "tasks.file_processing.process_project_files"

        settings = get_settings()

        # Check if task should execute (600 seconds = 10 minutes timeout)
        should_execute, existing_task = await idempotency_manager.should_execute_task(
            task_name=task_name,
            task_args=task_args,
            celery_task_id=task_instance.request.id,
            task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
        )

        if not should_execute:
            logger.warning(f"Can not handle th task | status: {existing_task.status}")
            return existing_task.result

        task_record = None
        if existing_task:
            # Update existing task with new celery task ID
            await idempotency_manager.update_task_status(
                execution_id=existing_task.execution_id, status="PENDING"
            )
            task_record = existing_task
        else:
            # Create new task record
            task_record = await idempotency_manager.create_task_record(
                task_name=task_name,
                task_args=task_args,
                celery_task_id=task_instance.request.id,
            )

        # Update status to STARTED
        await idempotency_manager.update_task_status(
            execution_id=task_record.execution_id, status="STARTED"
        )

        project = await persistence.get_or_create_project(project_id)

        nlp_controller = NLPController(
            vectordb_client=vectordb_client,
            generation_client=generation_client,
            embedding_client=embedding_client,
            template_parser=template_parser,
        )

        project_files_ids = {}
        if file_id:
            asset_record = await persistence.get_asset(project.id, file_id)

            if asset_record is None:
                task_instance.update_state(
                    state="FAILURE",
                    meta={
                        "signal": ResponseSignal.FILE_ID_ERROR.value,
                    },
                )

                # Update task status to FAILURE
                await idempotency_manager.update_task_status(
                    execution_id=task_record.execution_id,
                    status="FAILURE",
                    result={"signal": ResponseSignal.FILE_ID_ERROR.value},
                )

                raise Exception(f"No assets for file: {file_id}")

            project_files_ids = {asset_record.id: asset_record.asset_name}

        else:
            project_files = await persistence.list_assets(
                project.id, AssetTypeEnum.FILE.value
            )

            project_files_ids = {
                record.id: record.asset_name for record in project_files
            }

        if len(project_files_ids) == 0:
            task_instance.update_state(
                state="FAILURE",
                meta={
                    "signal": ResponseSignal.NO_FILES_ERROR.value,
                },
            )

            # Update task status to FAILURE
            await idempotency_manager.update_task_status(
                execution_id=task_record.execution_id,
                status="FAILURE",
                result={
                    "signal": ResponseSignal.NO_FILES_ERROR.value,
                },
            )

            raise Exception(f"No files found for project_id: {project.project_id}")

        process_controller = ProcessController(project_id=project_id)

        no_records = 0
        no_files = 0

        if do_reset == 1:
            # delete associated vectors collection
            collection_name = nlp_controller.create_collection_name(
                project_id=project.project_id
            )
            _ = await vectordb_client.delete_collection(collection_name=collection_name)

            # delete associated chunks
            _ = await persistence.delete_chunks(project.id)

        for asset_id, file_id in project_files_ids.items():
            file_content = process_controller.get_file_content(file_id=file_id)

            if file_content is None:
                logger.error(f"Error while processing file: {file_id}")
                continue

            file_chunks = process_controller.process_file_content(
                file_content=file_content,
                file_id=file_id,
                chunk_size=chunk_size,
                overlap_size=overlap_size,
            )

            if file_chunks is None or len(file_chunks) == 0:
                logger.error(f"No chunks for file_id: {file_id}")
                pass

            file_chunks_records = [
                ChunkRecord(
                    chunk_text=chunk.page_content,
                    chunk_metadata=chunk.metadata,
                    chunk_order=i + 1,
                    chunk_project_id=project.id,
                    chunk_asset_id=asset_id,
                )
                for i, chunk in enumerate(file_chunks)
            ]

            no_records += await persistence.insert_chunks(file_chunks_records)
            no_files += 1

        task_instance.update_state(
            state="SUCCESS",
            meta={
                "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            },
        )

        await idempotency_manager.update_task_status(
            execution_id=task_record.execution_id,
            status="SUCCESS",
            result={"signal": ResponseSignal.PROCESSING_SUCCESS.value},
        )

        logger.warning(f"inserted_chunks: {no_records}")

        return {
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files,
            "project_id": project_id,
            "do_reset": do_reset,
        }

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise
    finally:
        try:
            if persistence:
                await persistence.close()

            if vectordb_client:
                await vectordb_client.disconnect()
        except Exception as e:
            logger.error(f"Task failed while cleaning: {str(e)}")
