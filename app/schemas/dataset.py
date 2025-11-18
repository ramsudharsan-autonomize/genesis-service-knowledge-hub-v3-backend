"""Dataset schemas for request/response validation"""

from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from bson import ObjectId
from app.models import DatasetStatus
from app.utils.schema_utils import clean_tags, strip_whitespace


# Type aliases for cleaner field definitions
NonEmptyStr = Annotated[str, BeforeValidator(strip_whitespace)]
CleanTags = Annotated[list[str], BeforeValidator(clean_tags)]


class DatasetCreateRequest(BaseModel):
    """Request schema for creating a dataset - bare minimum fields"""

    name: NonEmptyStr = Field(..., min_length=1, max_length=200, description="Dataset name")
    description: NonEmptyStr = Field(..., min_length=1, max_length=1000, description="Dataset description")
    tags: CleanTags = Field(default_factory=list, description="Tags for categorization")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Claims Dataset - 2025",
                "description": "Claims uploaded by auditors",
                "tags": ["claims", "insurance"],
            }
        }
    )


class DatasetResponse(BaseModel):
    """Response schema for dataset"""

    id: str = Field(..., alias="_id", description="Dataset ID")
    name: str
    description: str
    tags: list[str]
    status: DatasetStatus
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    data_source_id: str | None = Field(None, alias="dataSourceId")
    pipeline_ids: list[str] = Field(default_factory=list, alias="pipelineIds")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Claims Dataset - 2025",
                "description": "Claims uploaded by auditors",
                "tags": ["claims", "insurance"],
                "status": "active",
                "createdAt": "2025-11-18T10:00:00Z",
                "updatedAt": "2025-11-18T10:00:00Z",
                "dataSourceId": None,
                "pipelineIds": [],
            }
        },
    )


class DatasetUpdateRequest(BaseModel):
    """Request schema for updating a dataset"""

    name: NonEmptyStr | None = Field(None, min_length=1, max_length=200)
    description: NonEmptyStr | None = Field(None, min_length=1, max_length=1000)
    tags: CleanTags | None = None
