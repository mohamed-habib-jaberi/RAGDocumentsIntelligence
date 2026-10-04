"""Orchestrate the two asynchronous stages of document ingestion.

The workflow deliberately separates responsibilities:

1. ``process_project_files`` reads uploaded documents, creates text chunks,
   and persists those chunks in PostgreSQL.
2. ``push_after_process_task`` converts the persisted chunks into embeddings
   and stores them in the configured Qdrant or PGVector backend.

Celery's ``chain`` passes the first task's return value to the second task and
does not start vector indexing when document processing raises an exception.
"""

from celery import chain
from celery_app import celery_app, get_setup_utils
from helpers.config import get_settings
import asyncio
from tasks.file_processing import process_project_files
from tasks.data_indexing import _index_data_content

import logging
logger = logging.getLogger(__name__)

@celery_app.task(
                 bind=True, name="tasks.process_workflow.push_after_process_task",
                 autoretry_for=(Exception,),
                 retry_kwargs={'max_retries': 3, 'countdown': 60}
                )
def push_after_process_task(self, prev_task_result):

    """Index the chunks after receiving a successful processing result."""
    # Recover the context produced by the document-processing stage. Celery
    # automatically provides this dictionary as the first argument in a chain.
    project_id = prev_task_result.get("project_id")
    do_reset = prev_task_result.get("do_reset")


    task_results = asyncio.run(
        _index_data_content(self, project_id, do_reset)
    )

    return {
        "project_id": project_id,
        "do_reset": do_reset,
        "task_results": task_results
    }


@celery_app.task(
                 bind=True, name="tasks.process_workflow.process_and_push_workflow",
                 autoretry_for=(Exception,),
                 retry_kwargs={'max_retries': 3, 'countdown': 60}
                )
def process_and_push_workflow(  self, project_id: int, 
                                file_id: int, chunk_size: int,
                                overlap_size: int, do_reset: int):

    """Schedule document processing followed by vector indexing."""
    # ``.s`` creates serializable Celery signatures. The first signature
    # performs Stage 1: file -> extracted text -> PostgreSQL chunks.
    workflow = chain(
        process_project_files.s(project_id, file_id, chunk_size, overlap_size, do_reset),
        # Celery passes Stage 1's return dictionary into this signature. It then
        # performs Stage 2: persisted chunks -> embeddings -> vector database.
        push_after_process_task.s()
    )

    result = workflow.apply_async()

    return {
        "signal": "WORKFLOW_STARTED",
        "workflow_id": result.id,
        "tasks": ["tasks.file_processing.process_project_files", 
                  "tasks.data_indexing.index_data_content"]
    }
