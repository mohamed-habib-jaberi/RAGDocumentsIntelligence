"""Document upload routes."""

import logging

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from controllers import DataController, ProcessController
from helpers.config import Settings, get_settings
from models import ChunkModel, DataChunk, ProjectModel, ResponseSignal
from routes.schemes.data import ProcessRequest

logger = logging.getLogger("uvicorn.error")
data_router = APIRouter(prefix="/api/v1/data", tags=["api_v1", "data"])


@data_router.post("/upload/{project_id}")
async def upload_data(
    request: Request,
    project_id: str,
    file: UploadFile,
    app_settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Validate and asynchronously persist one document within a project folder."""
    controller = DataController()
    is_valid, signal = controller.validate_uploaded_file(file)
    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"signal": signal})

    try:
        # Persist the project before its first physical document is written.
        project = await ProjectModel(request.app.db_client).get_project_or_create_one(project_id)
        file_path, file_id = controller.generate_unique_filepath(file.filename, project_id)
        uploaded_size = 0
        async with aiofiles.open(file_path, "wb") as destination:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                uploaded_size += len(chunk)
                is_valid, signal = controller.validate_file_size(uploaded_size)
                if not is_valid:
                    await file.close()
                    file_path.unlink(missing_ok=True)
                    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"signal": signal})
                await destination.write(chunk)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except OSError:
        logger.exception("Document upload failed for project %s", project_id)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": ResponseSignal.FILE_UPLOAD_FAILED.value},
        )
    finally:
        await file.close()

    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id,
            "project_id": project.project_id,
        }
    )


@data_router.post("/process/{project_id}")
async def process_document(
    request: Request,
    project_id: str,
    process_request: ProcessRequest,
) -> JSONResponse:
    """Load and chunk a project document in preparation for vector indexing."""
    try:
        controller = ProcessController(project_id)
        source_documents = controller.get_file_content(process_request.file_id)
        chunks = controller.process_file_content(
            source_documents,
            chunk_size=process_request.chunk_size,
            overlap_size=process_request.overlap_size,
        )
        project = await ProjectModel(request.app.db_client).get_project_or_create_one(project_id)
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except Exception:
        logger.exception("Document processing failed for project %s", project_id)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": ResponseSignal.PROCESSING_FAILED.value},
        )

    if not chunks:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.PROCESSING_FAILED.value},
        )

    records = [
        DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=index,
            chunk_project_id=project.id,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]
    chunk_model = ChunkModel(request.app.db_client)
    if process_request.do_reset:
        await chunk_model.delete_chunks_by_project_id(project.id)
    inserted_chunks = await chunk_model.insert_many_chunks(records)

    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": inserted_chunks,
        }
    )
