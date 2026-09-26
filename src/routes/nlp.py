"""Expose the HTTP endpoints implemented by the nlp router."""

import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from controllers import NLPController
from models import ResponseSignal
from routes.schemes.nlp import PushRequest, SearchRequest
from tasks.data_indexing import index_data_content

logger = logging.getLogger("uvicorn.error")

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)


@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: int, push_request: PushRequest):

    """Index the persisted chunks of a project in the active vector database."""
    task = index_data_content.delay(
        project_id=project_id, do_reset=push_request.do_reset
    )

    return JSONResponse(
        content={
            "signal": ResponseSignal.DATA_PUSH_TASK_READY.value,
            "task_id": task.id,
        }
    )


@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: int):

    """Return vector-index metadata for the requested project."""
    project = await request.app.persistence.projects.get_or_create(project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    collection_info = await nlp_controller.get_vector_db_collection_info(
        project=project
    )

    if collection_info is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": ResponseSignal.VECTORDB_COLLECTION_NOT_FOUND.value},
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info,
        }
    )


@nlp_router.post("/index/search/{project_id}")
async def search_index(
    request: Request, project_id: int, search_request: SearchRequest
):

    """Embed a query and return the most similar project documents."""
    project = await request.app.persistence.projects.get_or_create(project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    results = await nlp_controller.search_vector_db_collection(
        project=project, text=search_request.text, limit=search_request.limit
    )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value},
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "results": [result.dict() for result in results],
        }
    )


@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request: Request, project_id: int, search_request: SearchRequest):

    """Retrieve project context and return a generated answer for the submitted question."""
    project = await request.app.persistence.projects.get_or_create(project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
        project=project,
        query=search_request.text,
        limit=search_request.limit,
    )

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.RAG_ANSWER_ERROR.value},
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history,
        }
    )
