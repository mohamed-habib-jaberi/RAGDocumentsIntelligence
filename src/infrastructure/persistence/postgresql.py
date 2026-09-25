from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from domain import AssetRecord, ChunkRecord, ProjectRecord, TaskExecutionRecord
from models.db_schemes.minirag.schemes import (
    Asset,
    CeleryTaskExecution,
    DataChunk,
    Project,
)


class PostgresProjectRepository:
    def __init__(self, sessions):
        self.sessions = sessions

    async def get_or_create(self, project_id):
        numeric_id = int(project_id)
        async with self.sessions() as session:
            statement = (
                insert(Project)
                .values(project_id=numeric_id)
                .on_conflict_do_nothing(index_elements=[Project.project_id])
            )
            await session.execute(statement)
            await session.commit()
            project = await session.get(Project, numeric_id)
            return ProjectRecord(str(project.project_id), str(project.project_id))


class PostgresAssetRepository:
    def __init__(self, sessions):
        self.sessions = sessions

    async def create(self, asset):
        async with self.sessions() as session:
            record = Asset(
                asset_project_id=int(asset.asset_project_id),
                asset_type=asset.asset_type,
                asset_name=asset.asset_name,
                asset_size=asset.asset_size,
                asset_config=asset.asset_config,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return self._to_record(record)

    async def get(self, project_id, asset_name):
        async with self.sessions() as session:
            result = await session.execute(
                select(Asset).where(
                    Asset.asset_project_id == int(project_id),
                    Asset.asset_name == asset_name,
                )
            )
            record = result.scalar_one_or_none()
            return self._to_record(record) if record else None

    async def list(self, project_id, asset_type):
        async with self.sessions() as session:
            result = await session.execute(
                select(Asset).where(
                    Asset.asset_project_id == int(project_id),
                    Asset.asset_type == asset_type,
                )
            )
            return [self._to_record(record) for record in result.scalars().all()]

    @staticmethod
    def _to_record(record):
        return AssetRecord(
            id=str(record.asset_id),
            asset_project_id=str(record.asset_project_id),
            asset_type=record.asset_type,
            asset_name=record.asset_name,
            asset_size=record.asset_size,
            asset_config=record.asset_config,
        )


class PostgresChunkRepository:
    def __init__(self, sessions):
        self.sessions = sessions

    async def delete_by_project(self, project_id):
        async with self.sessions() as session:
            result = await session.execute(
                delete(DataChunk).where(DataChunk.chunk_project_id == int(project_id))
            )
            await session.commit()
            return result.rowcount

    async def insert_many(self, chunks):
        async with self.sessions() as session:
            records = [
                DataChunk(
                    chunk_text=chunk.chunk_text,
                    chunk_metadata=chunk.chunk_metadata,
                    chunk_order=chunk.chunk_order,
                    chunk_project_id=int(chunk.chunk_project_id),
                    chunk_asset_id=int(chunk.chunk_asset_id),
                )
                for chunk in chunks
            ]
            session.add_all(records)
            await session.commit()
            for record in records:
                await session.refresh(record)
            for chunk, record in zip(chunks, records):
                chunk.id = str(record.chunk_id)
            return len(records)

    async def list(self, project_id, page, page_size):
        async with self.sessions() as session:
            result = await session.execute(
                select(DataChunk)
                .where(DataChunk.chunk_project_id == int(project_id))
                .order_by(DataChunk.chunk_order)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            return [self._to_record(record) for record in result.scalars().all()]

    async def count(self, project_id):
        async with self.sessions() as session:
            result = await session.execute(
                select(func.count(DataChunk.chunk_id)).where(
                    DataChunk.chunk_project_id == int(project_id)
                )
            )
            return result.scalar_one()

    @staticmethod
    def _to_record(record):
        return ChunkRecord(
            id=str(record.chunk_id),
            chunk_text=record.chunk_text,
            chunk_metadata=record.chunk_metadata or {},
            chunk_order=record.chunk_order,
            chunk_project_id=str(record.chunk_project_id),
            chunk_asset_id=str(record.chunk_asset_id),
        )


class PostgresTaskExecutionRepository:
    def __init__(self, sessions):
        self.sessions = sessions

    async def create(self, task_name, args_hash, task_args, celery_task_id):
        async with self.sessions() as session:
            record = CeleryTaskExecution(
                task_name=task_name,
                task_args_hash=args_hash,
                task_args=task_args,
                celery_task_id=celery_task_id,
                status="PENDING",
                started_at=datetime.now(timezone.utc),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return self._to_record(record)

    async def update(self, execution_id, status, result=None):
        async with self.sessions() as session:
            record = await session.get(CeleryTaskExecution, int(execution_id))
            if record:
                record.status = status
                if result is not None:
                    record.result = result
                if status in {"SUCCESS", "FAILURE"}:
                    record.completed_at = datetime.now(timezone.utc)
                await session.commit()

    async def find(self, task_name, args_hash, celery_task_id):
        async with self.sessions() as session:
            result = await session.execute(
                select(CeleryTaskExecution).where(
                    CeleryTaskExecution.celery_task_id == celery_task_id,
                    CeleryTaskExecution.task_name == task_name,
                    CeleryTaskExecution.task_args_hash == args_hash,
                )
            )
            record = result.scalar_one_or_none()
            return self._to_record(record) if record else None

    async def cleanup(self, cutoff):
        async with self.sessions() as session:
            result = await session.execute(
                delete(CeleryTaskExecution).where(
                    CeleryTaskExecution.created_at < cutoff
                )
            )
            await session.commit()
            return result.rowcount

    @staticmethod
    def _to_record(record):
        return TaskExecutionRecord(
            execution_id=str(record.execution_id),
            status=record.status,
            result=record.result,
            started_at=record.started_at,
        )


class PostgresPersistence:
    def __init__(self, engine, sessions):
        self.engine = engine
        self.projects = PostgresProjectRepository(sessions)
        self.assets = PostgresAssetRepository(sessions)
        self.chunks = PostgresChunkRepository(sessions)
        self.task_executions = PostgresTaskExecutionRepository(sessions)

    async def initialize(self):
        async with self.engine.connect() as connection:
            await connection.execute(select(1))

    async def close(self):
        await self.engine.dispose()
