"""Document service for managing document uploads - following SOLID principles"""

import logging
from datetime import datetime, timezone
from beanie import PydanticObjectId
from app.factories.document_factory import DocumentFactory
from app.models.document_model import Document
from app.services.dataset_service import DatasetService
from app.utils.enums import StorageType, UploadStatus
from app.schemas.document_schema import (
    RequestUploadDetailsRequest,
    CompleteUploadRequest,
)
from app.services.storage_service import StorageService
from app.services.pipeline_service import PipelineService
from app.core.exceptions import (
    ValidationException,
    DocumentNotFoundException,
)

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service layer for document operations (Dependency Injection)

    This service orchestrates document upload operations by coordinating
    between validators, factories, repositories, and storage services.
    """

    @staticmethod
    async def get_upload_details(request: RequestUploadDetailsRequest) -> dict[str, str | PydanticObjectId]:
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
        storage_config = StorageService.get_default_storage_config()
        storage_type = StorageType(storage_config["storage_type"])
        storage_path = StorageService.build_storage_path(dataset_name=dataset.name, filename=request.original_name)

        # Step 3: Create document
        document = await _create_document(request, storage_type, storage_config, storage_path)

        # Step 4: Get signed URL
        try:
            upload_url = await StorageService.get_upload_signed_url(
                file_name=storage_path,
                storage_type=storage_type.value,
                container_name=storage_config["container"],
                storage_account=storage_config["storage_account"],
            )
        except Exception as e:
            await document.delete()
            raise ValidationException(f"Failed to generate upload URL: {str(e)}")

        return {
            "document_id": document.id,
            "upload_url": upload_url,
            "storage_path": storage_path,
        }

    @staticmethod
    async def complete_upload(document_id: PydanticObjectId, request: CompleteUploadRequest) -> Document:
        """
        Complete document upload and verify checksums

        This method:
        1. Retrieves the document
        2. Verifies it's in uploading state
        3. Validates checksums (size and hash)
        4. Updates document status to uploaded
        """
        # Step 1: Get document
        document = await DocumentService.get_document_by_id(document_id)

        # Step 2: Verify state
        _verify_upload_status_is_uploading(document)

        # Step 3: Verify checksums
        await _verify_checksums(document, request, str(document_id))

        # Step 4: Update document
        return await _finalize_upload(document, request)

    @staticmethod
    async def get_document_by_id(document_id: PydanticObjectId) -> Document:
        """Get document by ID (public API)"""
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

    @staticmethod
    async def update_processing_status(document_id: PydanticObjectId, processing_status: str) -> Document:
        """
        Update document processing status

        Args:
            document_id: Document ID
            processing_status: New processing status

        Returns:
            Updated document

        Raises:
            DocumentNotFoundException: If document not found
        """
        from app.utils.enums import ProcessingStatus

        document = await DocumentService.get_document_by_id(document_id)

        document.processing_status = ProcessingStatus(processing_status)
        document.updated_at = datetime.now(timezone.utc)

        await document.save()

        return document


async def _create_document(
    request: RequestUploadDetailsRequest,
    storage_type: StorageType,
    storage_config: dict,
    storage_path: str,
) -> Document:
    """Create and save document with all details"""
    storage_details = DocumentFactory.create_storage_details(
        storage_type=storage_type,
        container=storage_config["container"],
        storage_path=storage_path,
    )

    source_details = DocumentFactory.create_source_details(
        source_type=request.source_type,
        data_source_id=request.data_source_id,
        external_path=request.external_path,
    )

    metadata = DocumentFactory.create_metadata(uploaded_by_email=request.uploaded_by_email)

    document = DocumentFactory.create_document(
        request=request,
        storage_details=storage_details,
        source_details=source_details,
        metadata=metadata,
    )

    await document.insert()
    logger.info(f"Created document record: {document.id}")
    return document


def _verify_upload_status_is_uploading(document: Document) -> None:
    """Verify document is in correct state for completion"""
    if document.upload_status != UploadStatus.UPLOADING:
        raise ValidationException(f"Document is not in uploading state. Current status: {document.upload_status}")


async def _verify_checksums(
    document: Document,
    request: CompleteUploadRequest,
    document_id: str,
) -> None:
    """Verify file size and hash"""
    try:
        _verify_file_size(
            expected=document.expected_size,
            actual=request.size_in_bytes,
            document_id=document_id,
        )

        _verify_file_hash(
            expected=document.expected_hash,
            actual=request.hash,
            document_id=document_id,
        )
    except ValidationException:
        await _mark_document_as_error(document)
        raise


def _verify_file_size(expected: int | None, actual: int, document_id: str) -> None:
    """Verify file size matches expected size"""
    if expected and actual != expected:
        logger.warning(f"Size mismatch for document {document_id}: expected {expected}, got {actual}")
        raise ValidationException(f"File size mismatch: expected {expected} bytes, got {actual} bytes")


def _verify_file_hash(expected: str | None, actual: str, document_id: str) -> None:
    """Verify file hash matches expected hash"""
    if expected and actual != expected:
        logger.warning(f"Hash mismatch for document {document_id}: expected {expected}, got {actual}")
        raise ValidationException(f"File hash mismatch: expected {expected}, got {actual}")


async def _mark_document_as_error(document: Document) -> None:
    """Mark document as error and save"""
    document.upload_status = UploadStatus.ERROR
    document.updated_at = datetime.now(timezone.utc)
    await document.save()
    logger.warning(f"Marked document {document.id} as error")


async def _finalize_upload(
    document: Document,
    request: CompleteUploadRequest,
) -> Document:
    """Update document with final metadata and status"""
    document.metadata.size_in_bytes = request.size_in_bytes
    document.metadata.hash = request.hash
    document.upload_status = UploadStatus.UPLOADED
    document.updated_at = datetime.now(timezone.utc)

    await document.save()
    logger.info(f"Completed upload for document: {document.id}")

    # Trigger pipeline for document processing
    await _trigger_pipeline(document)

    return document


async def _trigger_pipeline(document: Document) -> None:
    """Trigger the processing pipeline for an uploaded document"""
    from app.utils.enums import ProcessingStatus

    try:
        storage_config = StorageService.get_default_storage_config()

        # Get read signed URL for the document
        document_url = StorageService.get_read_signed_url(
            file_name=document.storage.path,
            storage_type=storage_config["storage_type"],
            container_name=document.storage.container,
            storage_account=storage_config["storage_account"],
        )

        # Use document ID as session ID for tracking
        session_id = str(document.id)

        await PipelineService.trigger_pipeline(
            document_url=document_url,
            session_id=session_id,
        )

        # Update status to PROCESSING after successful trigger
        document.processing_status = ProcessingStatus.PROCESSING
        document.updated_at = datetime.now(timezone.utc)
        await document.save()

        logger.info(f"Pipeline triggered for document: {document.id}, status updated to PROCESSING")

    except Exception as e:
        # maybe we can implement a retry mech here? @Ram
        document.processing_status = ProcessingStatus.ERROR
        document.updated_at = datetime.now(timezone.utc)
        await document.save()
        logger.error(f"Failed to trigger pipeline for document {document.id}: {str(e)}")
        logger.error("&status updated to ERRORED")
