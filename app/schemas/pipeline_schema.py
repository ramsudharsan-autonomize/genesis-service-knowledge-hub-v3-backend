"""Pipeline schemas for request/response validation"""

from datetime import datetime
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from app.utils.enums import ProcessingStatus


class PipelineInfo(BaseModel):
    """Pipeline information from LangFlow API"""

    id: str = Field(..., description="Pipeline UUID")
    name: str = Field(..., description="Pipeline name")
    description: str | None = Field(default=None, description="Pipeline description")
    icon: str | None = Field(default=None, description="Pipeline icon")
    is_component: bool = Field(default=False, alias="isComponent", description="Whether this is a component")
    folder_id: str | None = Field(default=None, alias="folderId", description="Folder ID")
    updated_at: datetime | None = Field(default=None, alias="updatedAt", description="Last update timestamp")

    class Config:
        populate_by_name = True


class PipelineListResponse(BaseModel):
    """Response for list of pipelines"""

    pipelines: list[PipelineInfo]
    total: int


class PipelineExecutionResult(BaseModel):
    """Result of a single pipeline execution"""

    pipeline_id: str = Field(..., alias="pipelineId")
    run_id: PydanticObjectId = Field(..., alias="runId")
    status: ProcessingStatus
    error_message: str | None = Field(default=None, alias="errorMessage")

    class Config:
        populate_by_name = True


class TriggerPipelinesResponse(BaseModel):
    """Response for triggering pipelines for a document"""

    document_id: PydanticObjectId = Field(..., alias="documentId")
    total_pipelines: int = Field(..., alias="totalPipelines")
    successful: int
    failed: int
    results: list[PipelineExecutionResult]

    class Config:
        populate_by_name = True
