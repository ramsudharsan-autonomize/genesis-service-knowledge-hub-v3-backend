from beanie import PydanticObjectId
from app.models.document_model import Document, Metadata, SourceDetails, StorageDetails
from app.schemas.document_schema import RequestUploadDetailsRequest
from app.utils.enums import ProcessingStatus, SourceType, StorageType, UploadStatus


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
        data_source_id: PydanticObjectId | None,
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