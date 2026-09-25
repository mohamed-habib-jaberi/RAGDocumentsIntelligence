import asyncio
import logging

from tqdm.auto import tqdm

from celery_app import celery_app, get_setup_utils
from controllers import NLPController
from models import ResponseSignal

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.data_indexing.index_data_content",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def index_data_content(self, project_id: int, do_reset: int):

    logger.warning("index_data_content started")
    return asyncio.run(_index_data_content(self, project_id, do_reset))


async def _index_data_content(task_instance, project_id: int, do_reset: int):

    persistence, vectordb_client = None, None

    try:
        (
            persistence,
            generation_client,
            embedding_client,
            vectordb_client,
            template_parser,
        ) = await get_setup_utils()

        logger.warning("Setup utils were loaded!")

        project = await persistence.projects.get_or_create(project_id)

        if not project:
            task_instance.update_state(
                state="FAILURE",
                meta={"signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value},
            )

            raise Exception(f"No project found for project_id: {project_id}")

        nlp_controller = NLPController(
            vectordb_client=vectordb_client,
            generation_client=generation_client,
            embedding_client=embedding_client,
            template_parser=template_parser,
        )

        has_records = True
        page_no = 1
        inserted_items_count = 0
        idx = 0

        # create collection if not exists
        collection_name = nlp_controller.create_collection_name(
            project_id=project.project_id
        )

        _ = await vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=embedding_client.embedding_size,
            do_reset=do_reset,
        )

        # setup batching
        total_chunks_count = await persistence.chunks.count(project.id)
        pbar = tqdm(total=total_chunks_count, desc="Vector Indexing", position=0)

        while has_records:
            page_chunks = await persistence.chunks.list(project.id, page_no, 50)
            if len(page_chunks):
                page_no += 1

            if not page_chunks or len(page_chunks) == 0:
                has_records = False
                break

            # Stable batch IDs work in both vector adapters; backend-native
            # chunk IDs remain private to the persistence layer.
            chunks_ids = list(range(idx, idx + len(page_chunks)))
            idx += len(page_chunks)

            is_inserted = await nlp_controller.index_into_vector_db(
                project=project, chunks=page_chunks, chunks_ids=chunks_ids
            )

            if not is_inserted:
                task_instance.update_state(
                    state="FAILURE",
                    meta={"signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value},
                )

                raise Exception(
                    f"can not insert into vectorDB | project_id: {project_id}"
                )

            pbar.update(len(page_chunks))
            inserted_items_count += len(page_chunks)

        task_instance.update_state(
            state="SUCCESS",
            meta={
                "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
            },
        )

        return {
            "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_items_count": inserted_items_count,
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
