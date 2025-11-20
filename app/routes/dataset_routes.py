"""Dataset API router with CRUD operations"""

from beanie import PydanticObjectId
from fastapi import APIRouter, Query, Response
from fastapi import status

from app.schemas.dataset_schema import (
    DatasetAddPipelineRequest,
    DatasetAddPipelineResponse,
    DatasetCreateRequest,
    DatasetPipelinesResponse,
    DatasetResponse,
    DatasetUpdateRequest,
)
from app.schemas.document_schema import DocumentResponse
from app.services.dataset_service import DatasetService
from app.services.document_service import DocumentService
from app.utils.enums import DatasetStatus
from app.utils.error_handler import handle_exception


router = APIRouter()


@router.post(
    "/",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new dataset",
)
async def create_dataset(data: DatasetCreateRequest) -> DatasetResponse:
    """
    Create a new dataset with validation

    - **name**: Dataset name
    - **description**: Dataset description
    - **tags**: Optional list of tags for categorization
    """
    try:
        dataset = await DatasetService.create_dataset(data)
        response = DatasetResponse.model_validate(dataset)
        return response
    except Exception as e:
        handle_exception(e, "creating the dataset")


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get dataset by ID",
)
async def get_dataset(dataset_id: PydanticObjectId) -> DatasetResponse:
    """
    Get a specific dataset by ID

    - **dataset_id**: The ID of the dataset to retrieve
    """
    try:
        dataset = await DatasetService.get_dataset_by_id(dataset_id)
        response = DatasetResponse.model_validate(dataset)
        return response
    except Exception as e:
        handle_exception(e, "retrieving the dataset")


@router.get(
    "/",
    response_model=list[DatasetResponse],
    summary="List all datasets",
)
async def list_datasets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    status: DatasetStatus | None = Query(None, description="Filter by status"),
) -> list[DatasetResponse]:
    """
    List datasets with pagination and optional filtering

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **status**: Optional filter by status
    """
    try:
        datasets = await DatasetService.list_datasets(skip=skip, limit=limit, status=status)
        response = [DatasetResponse.model_validate(dataset) for dataset in datasets]
        return response
    except Exception as e:
        handle_exception(e, "listing datasets")


@router.patch(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Update a dataset",
)
async def update_dataset(dataset_id: PydanticObjectId, data: DatasetUpdateRequest) -> DatasetResponse:
    """
    Update a dataset (partial update)

    - **dataset_id**: The ID of the dataset to update
    - **name**: Optional new name
    - **description**: Optional new description
    - **tags**: Optional new tags list
    """
    try:
        dataset = await DatasetService.update_dataset(dataset_id, data)
        response = DatasetResponse.model_validate(dataset)
        return response
    except Exception as e:
        handle_exception(e, "updating the dataset")


@router.get(
    "/{dataset_id}/pipelines",
    response_model=DatasetPipelinesResponse,
    summary="Get all pipelines attached to a dataset",
)
async def get_dataset_pipelines(
    dataset_id: PydanticObjectId,
) -> DatasetPipelinesResponse:
    """
    Get all pipelines attached to a specific dataset

    - **dataset_id**: The ID of the dataset
    """
    try:
        dataset = await DatasetService.get_pipelines_by_dataset(dataset_id)
        response = DatasetPipelinesResponse(
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            pipeline_ids=dataset.pipeline_ids,
            pipeline_count=len(dataset.pipeline_ids),
        )
        return response
    except Exception as e:
        handle_exception(e, "retrieving pipelines for the dataset")


@router.get(
    "/{dataset_id}/documents",
    response_model=list[DocumentResponse],
    summary="Get all documents for a dataset",
)
async def get_dataset_documents(
    dataset_id: PydanticObjectId,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
) -> list[DocumentResponse]:
    """
    Get all documents attached to a specific dataset with pagination (limit and skip based)

    - **dataset_id**: The ID of the dataset
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (max 100)
    """
    try:
        documents = await DocumentService.get_documents_by_dataset(
            dataset_id=dataset_id,
            skip=skip,
            limit=limit,
        )
        response = [DocumentResponse.model_validate(doc) for doc in documents]
        return response
    except Exception as e:
        handle_exception(e, "Failed retrieving documents for the dataset")


@router.patch(
    "/{dataset_id}/add-pipeline",
    summary="Add a pipeline to a dataset",
    response_model=DatasetAddPipelineResponse,
)
async def add_pipeline_to_dataset(
    dataset_id: PydanticObjectId, data: DatasetAddPipelineRequest
) -> DatasetAddPipelineResponse:
    """
    Add a pipeline to a dataset

    - **dataset_id**: The ID of the dataset
    - **pipeline_id**: The ID of the pipeline to add
    """
    try:
        dataset = await DatasetService.add_pipeline_to_dataset(dataset_id, data.pipeline_id)
        response = DatasetAddPipelineResponse.model_validate({**dataset.model_dump(), "pipeline_id": data.pipeline_id})
        return response
    except Exception as e:
        handle_exception(e, "adding pipeline to the dataset")


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a dataset",
)
async def delete_dataset(
    dataset_id: PydanticObjectId,
    permanent: bool = Query(False, description="Permanently delete (hard delete) if True"),
):
    """
    Delete a dataset

    - **dataset_id**: The ID of the dataset to delete
    - **permanent**: If True, permanently delete; if False, soft delete (default: False)
    """
    try:
        await DatasetService.delete_dataset(dataset_id, soft_delete=not permanent)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        handle_exception(e, "deleting the dataset")
