"""Pipeline schemas for request/response validation"""

from datetime import datetime
from pydantic import BaseModel, Field


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
