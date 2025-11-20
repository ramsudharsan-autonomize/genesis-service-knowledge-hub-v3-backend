"""Utility functions for converting models to responses"""

from app.models.document import Document
from app.schemas.document import (
    DocumentResponse,
    StorageDetailsResponse,
    SourceDetailsResponse,
    MetadataResponse,
)

def get_document_response(document: Document) -> DocumentResponse:
    """Convert Document model to DocumentResponse schema"""
    return DocumentResponse(
        id=str(document.id),
        dataset_id=str(document.dataset_id),
        original_name=document.original_name,
        mime_type=document.mime_type,
        expected_size=document.expected_size,
        expected_hash=document.expected_hash,
        storage=StorageDetailsResponse(
            type=document.storage.type,
            container=document.storage.container,
            path=document.storage.path,
        ),
        source=SourceDetailsResponse(
            type=document.source.type,
            data_source_id=str(document.source.data_source_id) if document.source.data_source_id else None,
            external_path=document.source.external_path,
        ),
        metadata=MetadataResponse(
            size_in_bytes=document.metadata.size_in_bytes,
            hash=document.metadata.hash,
            uploaded_by_email=document.metadata.uploaded_by_email,
        ),
        upload_status=document.upload_status,
        processing_status=document.processing_status,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )
