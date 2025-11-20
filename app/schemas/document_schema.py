"""Document schemas for request/response validation"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.utils.enums import StorageType, SourceType, UploadStatus, ProcessingStatus
from app.utils.schema_utils import NonEmptyStr

pydantic_config = ConfigDict(
    populate_by_name=True,
    from_attributes=True,
    use_enum_values=True,
)


class RequestUploadRequest(BaseModel):
    """Request schema for initiating document upload"""

    dataset_id: str = Field(..., alias="datasetId", description="Dataset ID to upload document to")
    original_name: NonEmptyStr = Field(
        ..., alias="originalName", min_length=1, max_length=255, description="Original filename"
    )
    mime_type: str = Field(..., alias="mimeType", description="MIME type of the file")
    expected_size: int = Field(..., alias="expectedSize", gt=0, description="Expected file size in bytes")
    expected_hash: str | None = Field(None, alias="expectedHash", description="Expected file hash for verification")

    # Source information
    source_type: SourceType = Field(default=SourceType.FRONTEND_UPLOAD, alias="sourceType")
    data_source_id: str | None = Field(None, alias="dataSourceId", description="Data source ID if sync")
    external_path: str | None = Field(None, alias="externalPath", description="External path if sync")

    # Metadata
    uploaded_by_email: EmailStr | None = Field(
        default=None, alias="uploadedByEmail", description="Email of user who uploaded the file"
    )

    model_config = pydantic_config.copy()
    model_config.update(
        json_schema_extra={
            "example": {
                "datasetId": "507f1f77bcf86cd799439011",
                "originalName": "guideline_312.pdf",
                "mimeType": "application/pdf",
                "expectedSize": 238289,
                "expectedHash": "sha256:abcd...",
                "sourceType": "frontend-upload",
                "uploadedByEmail": "user@company.com",
            }
        },
    )


class RequestUploadResponse(BaseModel):
    """Response schema for request upload"""

    document_id: str = Field(..., serialization_alias="documentId")
    upload_url: str = Field(..., serialization_alias="uploadUrl")
    storage_path: str = Field(..., serialization_alias="storagePath")
    expires_at: str | None = Field(None, serialization_alias="expiresAt")

    model_config = pydantic_config


class CompleteUploadRequest(BaseModel):
    """Request schema for completing document upload"""

    size_in_bytes: int = Field(..., alias="sizeInBytes", gt=0, description="Actual uploaded file size")
    hash: str = Field(..., description="Actual file hash (sha256)")

    model_config = pydantic_config


class StorageDetailsResponse(BaseModel):
    """Response schema for storage details"""

    type: StorageType
    container: str
    path: str


class SourceDetailsResponse(BaseModel):
    """Response schema for source details"""

    type: SourceType
    data_source_id: str | None = Field(None, serialization_alias="dataSourceId")
    external_path: str | None = Field(None, serialization_alias="externalPath")


class MetadataResponse(BaseModel):
    """Response schema for metadata"""

    size_in_bytes: int | None = Field(None, serialization_alias="sizeInBytes")
    hash: str | None = None
    uploaded_by_email: str | None = Field(None, serialization_alias="uploadedByEmail")


class DocumentResponse(BaseModel):
    """Response schema for document"""

    id: str = Field(..., serialization_alias="_id")
    dataset_id: str = Field(..., serialization_alias="datasetId")

    original_name: str = Field(..., serialization_alias="originalName")
    mime_type: str = Field(..., serialization_alias="mimeType")
    expected_size: int | None = Field(None, serialization_alias="expectedSize")
    expected_hash: str | None = Field(None, serialization_alias="expectedHash")

    storage: StorageDetailsResponse
    source: SourceDetailsResponse
    metadata: MetadataResponse

    upload_status: UploadStatus = Field(..., serialization_alias="uploadStatus")
    processing_status: ProcessingStatus = Field(..., serialization_alias="processingStatus")

    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")

    model_config = pydantic_config


class UploadUrlResponse(BaseModel):
    """Response schema for upload URL"""

    document_id: str = Field(..., serialization_alias="documentId")
    upload_url: str = Field(..., serialization_alias="uploadUrl")
    document: DocumentResponse

    model_config = pydantic_config
