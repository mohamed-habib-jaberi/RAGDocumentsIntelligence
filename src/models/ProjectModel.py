"""MongoDB operations for logical document projects."""

from motor.motor_asyncio import AsyncIOMotorDatabase

from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseCollection


class ProjectModel(BaseDataModel):
    """Create projects lazily when their first document is uploaded or processed."""

    def __init__(self, db_client: AsyncIOMotorDatabase) -> None:
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseCollection.PROJECTS.value]

    async def get_project_or_create_one(self, project_id: str) -> Project:
        """Return the persisted project or create it atomically on first use."""
        record = await self.collection.find_one({"project_id": project_id})
        if record is not None:
            return Project.model_validate(record)

        project = Project(project_id=project_id)
        result = await self.collection.insert_one(project.model_dump(by_alias=True, exclude_none=True))
        project.id = result.inserted_id
        return project
