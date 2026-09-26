"""Expose the HTTP endpoints implemented by the data router."""

import logging
import os

import aiofiles
from fastapi import APIRouter, Depends, Request, UploadFile, status
from fastapi.responses import JSONResponse

from controllers import DataController
from domain import AssetRecord
from helpers.config import Settings, get_settings
from models import ResponseSignal
from models.enums.AssetTypeEnum import AssetTypeEnum
from tasks.file_processing import process_project_files
from tasks.process_workflow import process_and_push_workflow

from .schemes.data import ProcessRequest

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(
    request: Request,
    project_id: int,
    file: UploadFile,
    app_settings: Settings = Depends(get_settings),
):

    """Validate and store an uploaded document for the requested project."""
    project = await request.app.persistence.projects.get_or_create(project_id)

    # validate the file properties
    data_controller = DataController()

    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"signal": result_signal}
        )

    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename, project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.FILE_UPLOAD_FAILED.value},
        )

    asset_resource = AssetRecord(
        id=None,
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path),
    )

    asset_record = await request.app.persistence.assets.create(asset_resource)

    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            # The processing endpoint looks up assets by their generated file
            # name. Keep database-native IDs private to the persistence adapter.
            "file_id": asset_record.asset_name,
        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(
    request: Request, project_id: int, process_request: ProcessRequest
):

    """Queue document extraction and chunk persistence for a project."""
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    task = process_project_files.delay(
        project_id=project_id,
        file_id=process_request.file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
        do_reset=do_reset,
    )

    return JSONResponse(
        content={"signal": ResponseSignal.PROCESSING_SUCCESS.value, "task_id": task.id}
    )


@data_router.post("/process-and-push/{project_id}")
async def process_and_push_endpoint(
    request: Request, project_id: int, process_request: ProcessRequest
):

    """Queue the complete document-processing and vector-indexing workflow."""
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

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
            "workflow_task_id": workflow_task.id,
        }
    )
