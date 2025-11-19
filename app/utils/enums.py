"""Common enums used across models"""

from enum import Enum


class DatasetStatus(str, Enum):
    """Dataset status enumeration"""

    ACTIVE = "active"
    DELETED = "deleted"

class BronzeLayerStorageType(str, Enum):
    """Bronze layer storage type enumeration"""

    S3 = "s3"
    AZURE_BLOB_STORAGE = "azureblobstorage"
    GCS = "gcs"