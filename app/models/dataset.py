from datetime import datetime, timezone
from beanie import Document, PydanticObjectId
from pydantic import Field
from app.models.enums import DatasetStatus


class Dataset(Document):
    """Dataset model for storing document collections"""

    name: str = Field(..., description="Dataset name")
    description: str = Field(..., description="Dataset description")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    status: DatasetStatus = Field(default=DatasetStatus.ACTIVE, description="Dataset status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="createdAt")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="updatedAt")

    data_source_id: PydanticObjectId | None = Field(default=None, alias="dataSourceId")
    pipeline_ids: list[PydanticObjectId] = Field(default_factory=list, alias="pipelineIds")

    class Settings:
        name = "datasets"
        use_enum_values = True

    class Config:
        json_encoders = {PydanticObjectId: str, datetime: lambda v: v.isoformat()}
