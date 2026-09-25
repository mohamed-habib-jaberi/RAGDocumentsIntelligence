from celery import Celery

from helpers.config import get_settings
from infrastructure.persistence import create_persistence
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory

settings = get_settings()


async def get_setup_utils():
    settings = get_settings()
    persistence = await create_persistence(settings)

    llm_provider_factory = LLMProviderFactory(settings)
    vectordb_provider_factory = VectorDBProviderFactory(config=settings)

    generation_client = llm_provider_factory.create(
        provider=settings.GENERATION_BACKEND
    )
    generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)
    embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    embedding_client.set_embedding_model(
        model_id=settings.EMBEDDING_MODEL_ID,
        embedding_size=settings.EMBEDDING_MODEL_SIZE,
    )
    vectordb_client = vectordb_provider_factory.create(
        provider=settings.VECTOR_DB_BACKEND
    )
    await vectordb_client.connect()
    template_parser = TemplateParser(
        language=settings.PRIMARY_LANG, default_language=settings.DEFAULT_LANG
    )

    return (
        persistence,
        generation_client,
        embedding_client,
        vectordb_client,
        template_parser,
    )


celery_app = Celery(
    "rag_documents_intelligence",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.file_processing",
        "tasks.data_indexing",
        "tasks.process_workflow",
        "tasks.maintenance",
    ],
)
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=[settings.CELERY_TASK_SERIALIZER],
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    task_routes={
        "tasks.file_processing.process_project_files": {"queue": "file_processing"},
        "tasks.data_indexing.index_data_content": {"queue": "data_indexing"},
        "tasks.process_workflow.process_and_push_workflow": {
            "queue": "file_processing"
        },
        "tasks.maintenance.clean_celery_executions_table": {"queue": "default"},
    },
    timezone="UTC",
)
celery_app.conf.task_default_queue = "default"
