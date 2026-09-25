from fastapi import FastAPI

from helpers.config import get_settings
from infrastructure.persistence import create_persistence
from routes import base, data, nlp
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory

# Import metrics setup
from utils.metrics import setup_metrics

app = FastAPI()

# Setup Prometheus metrics
setup_metrics(app)


async def startup_span():
    settings = get_settings()

    app.persistence_backend = settings.PERSISTENCE_BACKEND
    try:
        app.persistence = await create_persistence(settings)

        llm_provider_factory = LLMProviderFactory(settings)
        vectordb_provider_factory = VectorDBProviderFactory(config=settings)

        # generation client
        app.generation_client = llm_provider_factory.create(
            provider=settings.GENERATION_BACKEND
        )
        app.generation_client.set_generation_model(
            model_id=settings.GENERATION_MODEL_ID
        )

        # embedding client
        app.embedding_client = llm_provider_factory.create(
            provider=settings.EMBEDDING_BACKEND
        )
        app.embedding_client.set_embedding_model(
            model_id=settings.EMBEDDING_MODEL_ID,
            embedding_size=settings.EMBEDDING_MODEL_SIZE,
        )

        # vector db client
        app.vectordb_client = vectordb_provider_factory.create(
            provider=settings.VECTOR_DB_BACKEND
        )
        await app.vectordb_client.connect()

        app.template_parser = TemplateParser(
            language=settings.PRIMARY_LANG,
            default_language=settings.DEFAULT_LANG,
        )
    except Exception:
        if getattr(app, "vectordb_client", None) is not None:
            await app.vectordb_client.disconnect()
        if getattr(app, "persistence", None) is not None:
            await app.persistence.close()
        raise


async def shutdown_span():
    if getattr(app, "persistence", None) is not None:
        await app.persistence.close()
    if getattr(app, "vectordb_client", None) is not None:
        await app.vectordb_client.disconnect()


app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
