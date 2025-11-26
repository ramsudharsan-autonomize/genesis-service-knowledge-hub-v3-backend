"""Document API router with upload operations"""

from beanie import PydanticObjectId
from fastapi import APIRouter, status
from app.schemas.document_schema import (
    RequestUploadDetailsRequest,
    RequestUploadDetailsResponse,
    CompleteUploadRequest,
    DocumentResponse,
)
from app.schemas.pipeline_schema import TriggerPipelinesResponse
from app.services.document_service import DocumentService
from app.services.pipeline_service import PipelineService
from app.utils.error_handler import handle_exception


router = APIRouter()


@router.post(
    "/request-upload-details",
    response_model=RequestUploadDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request document upload",
    description="Create a document record and get a signed URL for uploading the file",
)
async def request_upload_details(request: RequestUploadDetailsRequest) -> RequestUploadDetailsResponse:
    """
    Request document upload details and get signed URL

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
        upload_details = await DocumentService.get_upload_details(request)
        response = RequestUploadDetailsResponse.model_validate(upload_details)
        return response
    except Exception as e:
        handle_exception(e, "requesting upload")


@router.post(
    "/{document_id}/complete_upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete document upload and trigger dataset pipelines",
    description="Complete the upload process and verify checksums",
)
async def complete_upload_and_trigger_pipelines(
    document_id: PydanticObjectId,
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
        document = await DocumentService.complete_upload(document_id, request)
        response = DocumentResponse.model_validate(document)
        return response
    except Exception as e:
        handle_exception(e, "completing upload")


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document by ID",
    description="Retrieve document details by document ID",
)
async def get_document(document_id: PydanticObjectId) -> DocumentResponse:
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
        document = await DocumentService.get_document_by_id(document_id)
        response = DocumentResponse.model_validate(document)
        return response
    except Exception as e:
        handle_exception(e, "retrieving document")


@router.post(
    "/{document_id}/trigger-pipelines",
    response_model=TriggerPipelinesResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger all dataset pipelines for a document",
    description="Manually trigger all pipelines associated with the document's dataset",
)
async def trigger_pipelines_for_document(
    document_id: PydanticObjectId,
) -> TriggerPipelinesResponse:
    """
    Trigger all dataset pipelines for a document

    This endpoint manually triggers all pipelines associated with the document's dataset.
    Pipeline execution happens synchronously and results are returned.

    Use cases:
    - Re-run pipelines after a failed execution
    - Manually trigger pipelines for testing
    - Process documents that were uploaded before pipelines were configured

    - **document_id**: ID of the document to process
    """
    try:
        results = await PipelineService.trigger_all_pipelines_for_document(document_id)

        successful = sum(1 for r in results if r.status.value == "processed")
        failed = len(results) - successful

        return TriggerPipelinesResponse(
            document_id=document_id,
            total_pipelines=len(results),
            successful=successful,
            failed=failed,
            results=results,
        )
    except Exception as e:
        handle_exception(e, "triggering pipelines")
