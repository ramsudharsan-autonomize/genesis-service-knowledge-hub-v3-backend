from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from beanie import Document
from pydantic import Field
from bson import ObjectId


class DatasetStatus(str, Enum):
    """Dataset status enumeration"""

    ACTIVE = "active"
    DELETED = "deleted"



class Dataset(Document):
    """Dataset model for storing document collections"""

    name: str = Field(..., description="Dataset name")
    description: str = Field(..., description="Dataset description")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    status: DatasetStatus = Field(default=DatasetStatus.ACTIVE, description="Dataset status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="createdAt")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="updatedAt")

    data_source_id: Optional[ObjectId] = Field(default=None, alias="dataSourceId")
    pipeline_ids: List[ObjectId] = Field(default_factory=list, alias="pipelineIds")


    class Settings:
        name = "datasets"
        use_enum_values = True

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
