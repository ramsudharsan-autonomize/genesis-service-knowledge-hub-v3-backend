"""Common enums used across models"""

from enum import Enum


class DatasetStatus(str, Enum):
    """Dataset status enumeration"""

    ACTIVE = "active"
    DELETED = "deleted"


class StorageType(str, Enum):
    """Storage type enumeration"""

    AZURE_BLOB_STORAGE = "azureblobstorage"
    S3 = "s3"
    GCS = "gcs"


class SourceType(str, Enum):
    """Document source type enumeration"""

    FRONTEND_UPLOAD = "frontend-upload"
    DATASOURCE_SYNC = "datasource-sync"


class UploadStatus(str, Enum):
    """Upload status enumeration"""

    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    ERROR = "error"


class ProcessingStatus(str, Enum):
    """Processing status enumeration"""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"
