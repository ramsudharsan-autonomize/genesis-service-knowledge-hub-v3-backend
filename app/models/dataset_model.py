from datetime import datetime, timezone
from beanie import Document, PydanticObjectId
from pydantic import ConfigDict, Field
from app.utils.enums import DatasetStatus

pydantic_config = ConfigDict(
    populate_by_name=True,
    use_enum_values=True,
)


class Dataset(Document):
    """Dataset model for storing document collections"""

    name: str = Field(..., description="Dataset name")
    description: str = Field(..., description="Dataset description")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    status: DatasetStatus = Field(default=DatasetStatus.ACTIVE, description="Dataset status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="createdAt")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="updatedAt")

    data_source_id: PydanticObjectId | None = Field(default=None, alias="dataSourceId")
    pipeline_ids: list[str] = Field(default_factory=list, alias="pipelineIds", description="LangFlow pipeline UUIDs")

    model_config = pydantic_config

    class Settings:
        name = "datasets"
