"""Storage service for handling file uploads and signed URLs"""

import logging
from app.core.config import settings
from genesis_common_utility.services.flexstore_service import FlexstoreService

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing cloud storage operations"""

    @staticmethod
    def build_storage_path(dataset_name: str, filename: str) -> str:
        """
        Build storage path following the pattern: knowledge_hub_v3/:dataset_id/:filename

        Args:
            dataset_id: Dataset ID
            filename: Document filename

        Returns:
            Storage path string
        """
        return f"datasets/{dataset_name}/{filename}"

    @staticmethod
    async def get_upload_signed_url(
        file_name: str,
        storage_type: str,
        container_name: str,
        storage_account: str,
    ) -> str:
        """
        Get signed URL for uploading a file to cloud storage.
        This is a placeholder that should integrate with your actual
        get_upload_signed_url implementation.

        Args:
            file_name: Name of the file to upload
            storage_type: Type of storage (e.g., 'azureblobstorage')
            container_name: Storage container name
            storage_account: Storage account name

        Returns:
            Dictionary with signed URL and other upload details
        """
        request_payload = {
            "fileName": file_name,
            "sourceDetails": {
                "containerName": container_name,
                "storageAccount": storage_account,
            },
            "sourceType": storage_type,
        }

        signed_url = FlexstoreService.get_upload_signed_url(request_payload)
        logger.info(f"Signed URL for {file_name} generated.")
        return signed_url

    @staticmethod
    def get_default_storage_config() -> dict[str, str]:
        """
        Get default storage configuration from environment variables

        Returns:
            Dictionary with storage configuration
        """
        return {
            "storage_type": settings.STORAGE_TYPE,
            "storage_account": settings.STORAGE_ACCOUNT,
            "container": settings.STORAGE_CONTAINER,
        }

    @staticmethod
    def get_read_signed_url(
        file_name: str,
        storage_type: str,
        container_name: str,
        storage_account: str,
    ) -> str:
        """
        Get signed URL for reading/downloading a file from cloud storage.

        Args:
            file_name: Path to the file in storage
            storage_type: Type of storage (e.g., 'azureblobstorage')
            container_name: Storage container name
            storage_account: Storage account name

        Returns:
            Signed URL for reading the file
        """
        request_payload = {
            "fileName": file_name,
            "sourceDetails": {
                "containerName": container_name,
                "storageAccount": storage_account,
            },
            "sourceType": storage_type,
        }

        signed_url = FlexstoreService.get_read_signed_url(request_payload)
        logger.info(f"Read signed URL for {file_name} generated.")
        return signed_url
