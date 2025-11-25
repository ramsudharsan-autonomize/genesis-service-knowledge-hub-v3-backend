"""Document Pipeline Run model for tracking pipeline executions on documents"""

from datetime import datetime, timezone
from beanie import Document, PydanticObjectId
from pydantic import ConfigDict, Field
from app.utils.enums import ProcessingStatus

pydantic_config = ConfigDict(
    populate_by_name=True,
    use_enum_values=True,
)


class DocumentPipelineRun(Document):
    """
    Model to track pipeline execution for each document.

    When a document is uploaded, a DocumentPipelineRun is created for each
    pipeline associated with the dataset.
    """

    document_id: PydanticObjectId = Field(..., alias="documentId")
    dataset_id: PydanticObjectId = Field(..., alias="datasetId")
    pipeline_id: str = Field(..., alias="pipelineId")  # LangFlow pipeline ID (UUID string)

    # Processing status
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, alias="status")

    # Error tracking
    error_message: str | None = Field(default=None, alias="errorMessage")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="createdAt")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="updatedAt")

    model_config = pydantic_config

    class Settings:
        name = "document_pipeline_runs"
