"""Dataset API router with CRUD operations"""

from fastapi import APIRouter, Query, Response
from fastapi import status

from app.schemas.dataset import DatasetCreateRequest, DatasetResponse, DatasetUpdateRequest
from app.services.dataset_service import DatasetService
from app.models import DatasetStatus
from app.utils.error_handler import handle_exception
from app.utils.response_mapper import get_dataset_response


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
        return get_dataset_response(dataset)
    except Exception as e:
        handle_exception(e, "creating the dataset")


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get dataset by ID",
)
async def get_dataset(dataset_id: str) -> DatasetResponse:
    """
    Get a specific dataset by ID

    - **dataset_id**: The ID of the dataset to retrieve
    """
    try:
        dataset = await DatasetService.get_dataset_by_id(dataset_id)
        return get_dataset_response(dataset)
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
        return [get_dataset_response(dataset) for dataset in datasets]
    except Exception as e:
        handle_exception(e, "listing datasets")


@router.patch(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Update a dataset",
)
async def update_dataset(dataset_id: str, data: DatasetUpdateRequest) -> DatasetResponse:
    """
    Update a dataset (partial update)

    - **dataset_id**: The ID of the dataset to update
    - **name**: Optional new name
    - **description**: Optional new description
    - **tags**: Optional new tags list
    """
    try:
        dataset = await DatasetService.update_dataset(dataset_id, data)
        return get_dataset_response(dataset)
    except Exception as e:
        handle_exception(e, "updating the dataset")


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a dataset",
)
async def delete_dataset(
    dataset_id: str, permanent: bool = Query(False, description="Permanently delete (hard delete) if True")
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
