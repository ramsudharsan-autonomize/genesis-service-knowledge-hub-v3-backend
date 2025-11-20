"""Document API router with upload operations"""

from fastapi import APIRouter, status
from app.schemas.document_schema import (
    RequestUploadDetailsRequest,
    RequestUploadDetailsResponse,
    CompleteUploadRequest,
    DocumentResponse,
)
from app.services.document_service import DocumentService
from app.utils.error_handler import handle_exception
from app.utils.response_mapper import get_document_response


router = APIRouter()


@router.post(
    "/request-upload",
    response_model=RequestUploadDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request document upload",
    description="Create a document record and get a signed URL for uploading the file",
)
async def request_upload(request: RequestUploadDetailsRequest) -> RequestUploadDetailsResponse:
    """
    Request document upload and get signed URL

    Steps:
    1. Validates the dataset exists
    2. Creates a document record with UPLOADING status
    3. Generates a signed URL for direct upload to cloud storage
    4. Returns document ID and upload URL

    - **datasetId**: ID of the dataset to upload document to
    - **originalName**: Original filename
    - **mimeType**: MIME type of the file
    - **expectedSize**: Expected file size in bytes
    - **expectedHash**: Optional expected file hash for verification
    - **sourceType**: Source of upload (frontend-upload or datasource-sync)
    - **uploadedByEmail**: Email of user uploading the file
    """
    try:
        service = DocumentService()
        response = await service.get_upload_details(request)
        return response
    except Exception as e:
        handle_exception(e, "requesting upload")


@router.post(
    "/{document_id}/complete",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete document upload",
    description="Complete the upload process and verify checksums",
)
async def complete_upload(
    document_id: str,
    request: CompleteUploadRequest,
) -> DocumentResponse:
    """
    Complete document upload and verify checksums

    After uploading the file to the signed URL, call this endpoint to:
    1. Verify the file size matches expected size
    2. Verify the file hash matches expected hash
    3. Update document status to UPLOADED
    4. Update metadata with actual file details

    - **document_id**: ID of the document to complete
    - **sizeInBytes**: Actual uploaded file size in bytes
    - **hash**: Actual file hash (sha256)
    """
    try:
        service = DocumentService()
        document = await service.complete_upload(document_id, request)
        return get_document_response(document)
    except Exception as e:
        handle_exception(e, "completing upload")


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document by ID",
    description="Retrieve document details by document ID",
)
async def get_document(document_id: str) -> DocumentResponse:
    """
    Get document by ID

    Returns complete document information including:
    - File metadata (name, size, hash, MIME type)
    - Storage details (location, path)
    - Upload and processing status
    - Timestamps

    - **document_id**: ID of the document to retrieve
    """
    try:
        service = DocumentService()
        document = await service.get_document_by_id(document_id)
        return get_document_response(document)
    except Exception as e:
        handle_exception(e, "retrieving document")
