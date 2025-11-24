"""Dataset schemas for request/response validation"""

from datetime import datetime
from typing import Annotated
from beanie import PydanticObjectId
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from app.utils.enums import DatasetStatus
from app.utils.schema_utils import clean_tags, strip_whitespace
from app.schemas.pipeline_schema import PipelineInfo


pydantic_config = ConfigDict(
    populate_by_name=True,
    from_attributes=True,
    use_enum_values=True,
)

# Type aliases for cleaner field definitions
NonEmptyStr = Annotated[str, BeforeValidator(strip_whitespace)]
CleanTags = Annotated[list[str], BeforeValidator(clean_tags)]


class DatasetCreateRequest(BaseModel):
    """Request schema for creating a dataset - bare minimum fields"""

    name: NonEmptyStr = Field(..., min_length=1, max_length=200, description="Dataset name")
    description: NonEmptyStr = Field(..., min_length=1, max_length=1000, description="Dataset description")
    tags: CleanTags = Field(default_factory=list, description="Tags for categorization")

    model_config = pydantic_config.copy()
    model_config.update(
        json_schema_extra={
            "example": {
                "name": "Claims Dataset - 2025",
                "description": "Claims uploaded by auditors",
                "tags": ["claims", "insurance"],
            }
        }
    )


class DatasetUpdateRequest(BaseModel):
    """Request schema for updating a dataset"""

    name: NonEmptyStr | None = Field(None, min_length=1, max_length=200)
    description: NonEmptyStr | None = Field(None, min_length=1, max_length=1000)
    tags: CleanTags | None = None


class DatasetAddPipelineRequest(BaseModel):
    """Request schema for adding a pipeline to a dataset"""

    pipeline_id: str = Field(..., alias="pipelineId", description="Pipeline UUID to add")
    model_config = pydantic_config.copy()
    model_config.update(
        json_schema_extra={
            "example": {
                "pipelineId": "87dd13f6-2249-4269-9dbc-5b1bac4dcd62",
            }
        }
    )


class DatasetResponse(BaseModel):
    """Response schema for dataset"""

    id: PydanticObjectId = Field(..., alias="_id", description="Dataset ID")
    name: str
    description: str
    tags: list[str]
    status: DatasetStatus
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    data_source_id: str | None = Field(None, alias="dataSourceId")
    pipeline_ids: list[str] = Field(default_factory=list, alias="pipelineIds")

    model_config = pydantic_config


class DatasetAddPipelineResponse(BaseModel):
    """Response schema for adding a pipeline to a dataset"""

    id: PydanticObjectId = Field(..., alias="_id", description="Dataset ID")
    pipeline_id: str = Field(..., alias="pipelineId", description="Pipeline UUID added")
    model_config = pydantic_config


class DatasetPipelinesResponse(BaseModel):
    """Response schema for listing pipelines attached to a dataset"""

    dataset_id: PydanticObjectId = Field(..., alias="datasetId", description="Dataset ID")
    dataset_name: str = Field(..., alias="datasetName", description="Dataset name")
    pipeline_ids: list[str] = Field(default_factory=list, alias="pipelineIds", description="List of pipeline UUIDs")
    pipelines: list[PipelineInfo] = Field(default_factory=list, description="Detailed pipeline information")
    pipeline_count: int = Field(..., alias="pipelineCount", description="Total number of pipelines")
    model_config = pydantic_config
