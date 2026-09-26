"""Implement persistence operations for the AssetModel domain model."""

from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId
from sqlalchemy.future import select

class AssetModel(BaseDataModel):

    """Provide persistence behavior for the Asset domain entity."""
    def __init__(self, db_client: object):
        """Initialize asset persistence for the selected database client."""
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        """Create a model instance bound to the configured database client."""
        instance = cls(db_client)
        return instance

    async def create_asset(self, asset: Asset):

        """Persist metadata describing an uploaded project asset."""
        async with self.db_client() as session:
            async with session.begin():
                session.add(asset)
            await session.commit()
            await session.refresh(asset)
        return asset

    async def get_all_project_assets(self, asset_project_id: str, asset_type: str):

        """Return all persisted assets of the requested type for a project."""
        async with self.db_client() as session:
            stmt = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_type == asset_type
            )
            result = await session.execute(stmt)
            records = result.scalars().all()
        return records

    async def get_asset_record(self, asset_project_id: str, asset_name: str):

        """Retrieve one asset from its project and generated file name."""
        async with self.db_client() as session:
            stmt = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_name == asset_name
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
        return record


