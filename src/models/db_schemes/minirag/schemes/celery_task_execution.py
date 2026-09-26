"""Define database schema objects for celery task execution persistence."""

from sqlalchemy import Column, DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB

from .minirag_base import SQLAlchemyBase


class CeleryTaskExecution(SQLAlchemyBase):
    """Encapsulate the responsibilities and state of the CeleryTaskExecution component."""
    __tablename__ = "celery_task_executions"

    execution_id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String, nullable=False)
    task_args_hash = Column(String(64), nullable=False)
    task_args = Column(JSONB, nullable=False)
    celery_task_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="PENDING")
    result = Column(JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index(
            "ix_celery_task_lookup",
            celery_task_id,
            task_name,
            task_args_hash,
            unique=True,
        ),
        Index("ix_celery_task_created_at", created_at),
    )
