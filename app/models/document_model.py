"""Document model for MongoDB"""

from datetime import datetime, timezone
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.utils.enums import StorageType, SourceType, UploadStatus

pydantic_config = ConfigDict(
    populate_by_name=True,
    use_enum_values=True,
)


class StorageDetails(BaseModel):
    """Embedded document for storage details"""

    type: StorageType
    storage_account: str = Field(..., alias="storageAccount")
    container: str
    path: str

    model_config = pydantic_config


class SourceDetails(BaseModel):
    """Embedded document for source details"""

    type: SourceType
    data_source_id: PydanticObjectId | None = Field(default=None, alias="dataSourceId")
    external_path: str | None = Field(default=None, alias="externalPath")

    model_config = pydantic_config


class Metadata(BaseModel):
    """Embedded document for file metadata"""

    size_in_bytes: int | None = Field(default=None, alias="sizeInBytes")
    hash: str | None = None
    uploaded_by_email: EmailStr | None = Field(default=None, alias="uploadedByEmail")

    model_config = pydantic_config


class Document(Document):
    """Document model for file uploads"""

    dataset_id: PydanticObjectId = Field(..., alias="datasetId")

    # File information
    original_name: str = Field(..., alias="originalName")
    mime_type: str = Field(..., alias="mimeType")
    expected_size: int | None = Field(default=None, alias="expectedSize")
    expected_hash: str | None = Field(default=None, alias="expectedHash")

    # Storage information
    storage: StorageDetails

    # Source information
    source: SourceDetails

    # Metadata
    metadata: Metadata = Field(default_factory=lambda: Metadata())

    # Status fields
    upload_status: UploadStatus = Field(default=UploadStatus.UPLOADING, alias="uploadStatus")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="createdAt")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="updatedAt")
    model_config = pydantic_config

    class Settings:
        name = "documents"
