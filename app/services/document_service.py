"""Document service for managing document uploads - following SOLID principles"""

import logging
from datetime import datetime, timezone
from beanie import PydanticObjectId
from app.models.document_model import Document, StorageDetails, SourceDetails, Metadata
from app.services.dataset_service import DatasetService
from app.utils.enums import StorageType, SourceType, UploadStatus, ProcessingStatus
from app.schemas.document_schema import (
    RequestUploadDetailsRequest,
    CompleteUploadRequest,
)
from app.services.storage_service import StorageService
from app.core.exceptions import (
    ValidationException,
    DocumentNotFoundException,
)

logger = logging.getLogger(__name__)


class DocumentFactory:
    """Factory for creating document objects (Factory Pattern)"""

    @staticmethod
    def create_storage_details(
        storage_type: StorageType,
        container: str,
        storage_path: str,
    ) -> StorageDetails:
        """Create StorageDetails object"""
        return StorageDetails(
            type=storage_type,
            container=container,
            path=storage_path,
        )

    @staticmethod
    def create_source_details(
        source_type: SourceType,
        data_source_id: str | None,
        external_path: str | None,
    ) -> SourceDetails:
        """Create SourceDetails object"""
        return SourceDetails(
            type=source_type,
            data_source_id=PydanticObjectId(data_source_id) if data_source_id else None,
            external_path=external_path,
        )

    @staticmethod
    def create_metadata(uploaded_by_email: str | None) -> Metadata:
        """Create Metadata object"""
        return Metadata(uploaded_by_email=uploaded_by_email)

    @staticmethod
    def create_document(
        request: RequestUploadDetailsRequest,
        storage_details: StorageDetails,
        source_details: SourceDetails,
        metadata: Metadata,
    ) -> Document:
        """Create Document object from request"""
        return Document(
            dataset_id=PydanticObjectId(request.dataset_id),
            original_name=request.original_name,
            mime_type=request.mime_type,
            expected_size=request.expected_size,
            expected_hash=request.expected_hash,
            storage=storage_details,
            source=source_details,
            metadata=metadata,
            upload_status=UploadStatus.UPLOADING,
            processing_status=ProcessingStatus.PENDING,
        )


class UploadVerifier:
    """Verifier for upload completion checks (Single Responsibility)"""

    @staticmethod
    def verify_upload_status_is_uploading(document: Document) -> None:
        """Verify document is in correct state for completion"""
        if document.upload_status != UploadStatus.UPLOADING:
            raise ValidationException(f"Document is not in uploading state. Current status: {document.upload_status}")

    @staticmethod
    def verify_file_size(expected: int | None, actual: int, document_id: str) -> None:
        """Verify file size matches expected size"""
        if expected and actual != expected:
            logger.warning(f"Size mismatch for document {document_id}: expected {expected}, got {actual}")
            raise ValidationException(f"File size mismatch: expected {expected} bytes, got {actual} bytes")

    @staticmethod
    def verify_file_hash(expected: str | None, actual: str, document_id: str) -> None:
        """Verify file hash matches expected hash"""
        if expected and actual != expected:
            logger.warning(f"Hash mismatch for document {document_id}: expected {expected}, got {actual}")
            raise ValidationException(f"File hash mismatch: expected {expected}, got {actual}")


class DocumentRepository:
    """Repository for document data access (Repository Pattern)"""

    @staticmethod
    async def save(document: Document) -> Document:
        """Save document to database"""
        await document.insert()
        logger.info(f"Created document record: {document.id}")
        return document

    @staticmethod
    async def update(document: Document) -> Document:
        """Update document in database"""
        document.updated_at = datetime.now(timezone.utc)
        await document.save()
        return document

    @staticmethod
    async def get_by_id(document_id: PydanticObjectId) -> Document:
        """Get document by ID"""
        try:
            document = await Document.get(document_id)
            if not document:
                raise DocumentNotFoundException(f"Document with ID {document_id} not found")
            return document
        except Exception as e:
            if isinstance(e, DocumentNotFoundException):
                raise
            raise ValidationException(f"Invalid document ID: {document_id}")

    @staticmethod
    async def mark_as_error(document: Document) -> None:
        """Mark document as error and save"""
        document.upload_status = UploadStatus.ERROR
        document.updated_at = datetime.now(timezone.utc)
        await document.save()


class DocumentService:
    """
    Service layer for document operations (Dependency Injection)

    This service orchestrates document upload operations by coordinating
    between validators, factories, repositories, and storage services.
    """

    def __init__(
        self,
        storage_service: StorageService | None = None,
        document_factory: DocumentFactory | None = None,
        document_repository: DocumentRepository | None = None,
        upload_verifier: UploadVerifier | None = None,
    ):
        self.storage_service = storage_service or StorageService()
        self.document_factory = document_factory or DocumentFactory()
        self.document_repository = document_repository or DocumentRepository()
        self.upload_verifier = upload_verifier or UploadVerifier()

    async def get_upload_details(self, request: RequestUploadDetailsRequest) -> dict[str, any]:
        """
        Create a document record and get signed upload URL

        This method:
        1. Validates the dataset exists
        2. Creates document record with storage details
        3. Generates signed upload URL
        4. Returns response with document ID and URL
        """
        # Step 1: Validate dataset
        dataset = await DatasetService.get_dataset_by_id(request.dataset_id)

        # Step 2: Prepare storage configuration
        storage_config = self.storage_service.get_default_storage_config()
        storage_type = StorageType(storage_config["storage_type"])
        storage_path = self.storage_service.build_storage_path(
            dataset_name=dataset.name, filename=request.original_name
        )

        # Step 3: Create document
        document = await self._create_document(request, storage_type, storage_config, storage_path)

        # Step 4: Get signed URL
        try:
            upload_url = await self._get_signed_url(storage_path, storage_type, storage_config)
        except Exception as e:
            await document.delete()
            raise ValidationException(f"Failed to generate upload URL: {str(e)}")

        return {
            "document_id": document.id,
            "upload_url": upload_url,
            "storage_path": storage_path,
        }

    async def _create_document(
        self,
        request: RequestUploadDetailsRequest,
        storage_type: StorageType,
        storage_config: dict,
        storage_path: str,
    ) -> Document:
        """Create and save document with all details"""
        storage_details = self.document_factory.create_storage_details(
            storage_type=storage_type,
            container=storage_config["container"],
            storage_path=storage_path,
        )

        source_details = self.document_factory.create_source_details(
            source_type=request.source_type,
            data_source_id=request.data_source_id,
            external_path=request.external_path,
        )

        metadata = self.document_factory.create_metadata(uploaded_by_email=request.uploaded_by_email)

        document = self.document_factory.create_document(
            request=request,
            storage_details=storage_details,
            source_details=source_details,
            metadata=metadata,
        )

        return await self.document_repository.save(document)

    async def _get_signed_url(
        self,
        storage_path: str,
        storage_type: StorageType,
        storage_config: dict,
    ) -> str:
        """Get signed URL from storage service"""
        try:
            upload_url_response = await self.storage_service.get_upload_signed_url(
                file_name=storage_path,
                storage_type=storage_type.value,
                container_name=storage_config["container"],
                storage_account=storage_config["storage_account"],
            )

            upload_url = upload_url_response.get("url") or upload_url_response.get("uploadUrl")

            if not upload_url:
                raise ValidationException("Failed to get upload URL from storage service")

            logger.info(f"Generated signed URL for storage path: {storage_path}")
            return upload_url

        except NotImplementedError:
            upload_url = (
                f"https://{storage_config['storage_account']}.blob.core.windows.net/"
                f"{storage_config['container']}/{storage_path}?sas_token=placeholder"
            )
            logger.warning("Using placeholder upload URL - get_upload_signed_url not implemented")
            return upload_url

    async def complete_upload(self, document_id: PydanticObjectId, request: CompleteUploadRequest) -> Document:
        """
        Complete document upload and verify checksums

        This method:
        1. Retrieves the document
        2. Verifies it's in uploading state
        3. Validates checksums (size and hash)
        4. Updates document status to uploaded
        """
        # Step 1: Get document
        document = await self.document_repository.get_by_id(document_id)

        # Step 2: Verify state
        self.upload_verifier.verify_upload_status_is_uploading(document)

        # Step 3: Verify checksums
        await self._verify_checksums(document, request, document_id)

        # Step 4: Update document
        return await self._finalize_upload(document, request)

    async def _verify_checksums(
        self,
        document: Document,
        request: CompleteUploadRequest,
        document_id: str,
    ) -> None:
        """Verify file size and hash"""
        try:
            self.upload_verifier.verify_file_size(
                expected=document.expected_size,
                actual=request.size_in_bytes,
                document_id=document_id,
            )

            self.upload_verifier.verify_file_hash(
                expected=document.expected_hash,
                actual=request.hash,
                document_id=document_id,
            )
        except ValidationException:
            await self.document_repository.mark_as_error(document)
            raise

    async def _finalize_upload(
        self,
        document: Document,
        request: CompleteUploadRequest,
    ) -> Document:
        """Update document with final metadata and status"""
        document.metadata.size_in_bytes = request.size_in_bytes
        document.metadata.hash = request.hash
        document.upload_status = UploadStatus.UPLOADED

        document = await self.document_repository.update(document)
        logger.info(f"Completed upload for document: {document.id}")
        return document

    async def get_document_by_id(self, document_id: PydanticObjectId) -> Document:
        """Get document by ID"""
        return await self.document_repository.get_by_id(document_id)

    @staticmethod
    async def get_documents_by_dataset(
        dataset_id: PydanticObjectId,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        """
        Get all documents for a specific dataset with pagination

        Args:
            dataset_id: Dataset ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of document objects
        """
        await DatasetService.get_dataset_by_id(dataset_id)

        documents = await Document.find(Document.dataset_id == dataset_id).skip(skip).limit(limit).to_list()
        return documents
