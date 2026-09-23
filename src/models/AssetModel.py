"""MongoDB operations for files uploaded to a project."""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums.DataBaseEnum import DataBaseCollection


class AssetModel(BaseDataModel):
    """Create and retrieve assets by owning project and server-side filename."""

    def __init__(self, db_client: AsyncIOMotorDatabase) -> None:
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseCollection.ASSETS.value]

    async def ensure_indexes(self) -> None:
        """Prevent duplicate filenames within the same project."""
        await self.collection.create_index([("asset_project_id", 1), ("asset_name", 1)], unique=True)

    async def create_asset(self, asset: Asset) -> Asset:
        result = await self.collection.insert_one(asset.model_dump(by_alias=True, exclude_none=True))
        asset.id = result.inserted_id
        return asset

    async def get_project_assets(self, project_id: ObjectId) -> list[Asset]:
        records = await self.collection.find({"asset_project_id": project_id}).to_list(length=None)
        return [Asset.model_validate(record) for record in records]

    async def get_project_asset(self, project_id: ObjectId, asset_name: str) -> Asset | None:
        record = await self.collection.find_one({"asset_project_id": project_id, "asset_name": asset_name})
        return Asset.model_validate(record) if record else None
