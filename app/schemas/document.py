from pydantic import BaseModel

from app.utils.enums import BronzeLayerStorageType

class SourceDetails(BaseModel):
    bucketName: str | None = None
    folderName: str | None = None
    region: str | None = None
    storageAccount: str | None = None
    containerName: str | None = None

class BronzeLayerStorageDetails(BaseModel):
    """Schema for Bronze Layer Storage Details"""

    sourceType: BronzeLayerStorageType
    sourceDetails: SourceDetails