"""Expose the HTTP endpoints implemented by the data router."""

from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import aiofiles
from models import ResponseSignal
import logging
from .schemes.data import ProcessRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemes import DataChunk, Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
from controllers import NLPController
from tasks.file_processing import process_project_files
from tasks.process_workflow import process_and_push_workflow

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: int, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):


    """Validate and store an uploaded document for the requested project."""
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    # validate the file properties
    data_controller = DataController()

    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )

    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )

    # store the assets into the database
    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )

    asset_resource = Asset(
        asset_project_id=project.project_id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset=asset_resource)

    return JSONResponse(
            content={
                "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                # The processing endpoint resolves a file by its generated
                # storage name. Expose the SQL identifier separately so that
                # clients do not accidentally send it as ``file_id``.
                "file_id": asset_record.asset_name,
                "asset_id": str(asset_record.asset_id),
            }
        )

@data_router.post(
    "/process/{project_id}",
    summary="Split uploaded documents into text chunks",
    description=(
        "Queues a Celery task that reads one uploaded file, or every file in "
        "the project when file_id is omitted. The task extracts text, splits "
        "it into overlapping chunks, and persists those chunks in PostgreSQL. "
        "This endpoint does not generate embeddings and does not write to the "
        "vector database; call /api/v1/nlp/index/push/{project_id} afterward."
    ),
)
async def process_endpoint(request: Request, project_id: int, process_request: ProcessRequest):

    """Queue the document-to-chunks stage of the ingestion pipeline."""
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    # Stage 1: the worker converts the stored document into searchable text
    # units and saves them in the relational persistence database. Embedding
    # generation deliberately belongs to the separate indexing stage.
    task = process_project_files.delay(
        project_id=project_id,
        file_id=process_request.file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
        do_reset=do_reset,
    )

    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "task_id": task.id
        }
    )

@data_router.post(
    "/process-and-push/{project_id}",
    summary="Process documents and build their vector index",
    description=(
        "Queues the complete Celery workflow: extract document text, create "
        "and persist chunks, generate an embedding for each chunk, then store "
        "the vectors in the configured Qdrant or PGVector backend."
    ),
)
async def process_and_push_endpoint(request: Request, project_id: int, process_request: ProcessRequest):

    """Queue the complete document-processing and vector-indexing workflow."""
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    # Combined pipeline: Stage 1 creates relational chunks; Stage 2 converts
    # those chunks into embeddings and writes the vector index.
    workflow_task = process_and_push_workflow.delay(
        project_id=project_id,
        file_id=process_request.file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
        do_reset=do_reset,
    )

    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCESS_AND_PUSH_WORKFLOW_READY.value,
            "workflow_task_id": workflow_task.id
        }
    )
