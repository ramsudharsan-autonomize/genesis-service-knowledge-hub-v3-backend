"""Service layer for dataset operations - implements business logic"""

from datetime import datetime, timezone
from beanie import PydanticObjectId
from beanie.operators import Set

from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreateRequest, DatasetUpdateRequest
from app.core.exceptions import DatasetNotFoundException, DatasetAlreadyExistsException
from app.utils.enums import DatasetStatus


class DatasetService:
    """Service class for dataset business logic using Repository pattern"""

    @staticmethod
    async def create_dataset(data: DatasetCreateRequest) -> Dataset:
        """
        Create a new dataset with validation

        Args:
            data: Dataset creation request data

        Returns:
            Created dataset document

        Raises:
            DatasetAlreadyExistsException: If dataset with same name exists
        """
        # Check for duplicate name
        existing = await Dataset.find_one(Dataset.name == data.name)

        if existing:
            raise DatasetAlreadyExistsException(data.name)

        # Create new dataset
        dataset = Dataset(
            name=data.name,
            description=data.description,
            tags=data.tags or [],
        )

        await dataset.insert()
        return dataset

    @staticmethod
    async def get_dataset_by_id(dataset_id: str) -> Dataset:
        """
        Get dataset by ID

        Args:
            dataset_id: Dataset ID

        Returns:
            Dataset document

        Raises:
            DatasetNotFoundException: If dataset not found
        """
        try:
            dataset = await Dataset.get(PydanticObjectId(dataset_id))
        except Exception:
            raise DatasetNotFoundException(dataset_id)

        if not dataset:
            raise DatasetNotFoundException(dataset_id)

        return dataset

    @staticmethod
    async def list_datasets(skip: int = 0, limit: int = 100, status: DatasetStatus | None = None) -> list[Dataset]:
        """
        List datasets with pagination and filtering

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status (optional)

        Returns:
            List of dataset documents
        """
        query = Dataset.find()

        if status:
            query = query.find(Dataset.status == status)

        datasets = await query.skip(skip).limit(limit).to_list()
        return datasets

    @staticmethod
    async def update_dataset(dataset_id: str, data: DatasetUpdateRequest) -> Dataset:
        """
        Update dataset with partial updates

        Args:
            dataset_id: Dataset ID
            data: Update request data

        Returns:
            Updated dataset document

        Raises:
            DatasetNotFoundException: If dataset not found
            DatasetAlreadyExistsException: If name conflicts with existing dataset
        """
        dataset = await DatasetService.get_dataset_by_id(dataset_id)

        # Check for name conflict if name is being updated
        if data.name and data.name != dataset.name:
            existing = await Dataset.find_one(Dataset.name == data.name)

            if existing:
                raise DatasetAlreadyExistsException(data.name)

        # Build update dictionary with only provided fields
        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.description is not None:
            update_data["description"] = data.description
        if data.tags is not None:
            update_data["tags"] = data.tags

        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)

        # Perform update
        await dataset.update(Set(update_data))

        # Fetch and return updated dataset
        return await DatasetService.get_dataset_by_id(dataset_id)

    @staticmethod
    async def delete_dataset(dataset_id: str, soft_delete: bool = True) -> Dataset:
        """
        Delete dataset (soft or hard delete)

        Args:
            dataset_id: Dataset ID
            soft_delete: If True, mark as deleted; if False, permanently delete

        Returns:
            Deleted dataset document (for soft delete) or None (for hard delete)

        Raises:
            DatasetNotFoundException: If dataset not found
        """
        dataset = await DatasetService.get_dataset_by_id(dataset_id)

        if soft_delete:
            # Soft delete - mark as deleted
            await dataset.update(Set({"status": DatasetStatus.DELETED, "updated_at": datetime.now(timezone.utc)}))
            return await DatasetService.get_dataset_by_id(dataset_id)
        else:
            # Hard delete - permanently remove
            await dataset.delete()
            return dataset
        
    @staticmethod
    async def add_pipeline_to_dataset(dataset_id: str, pipeline_id: str) -> Dataset:
        """
        Add a pipeline to the dataset's pipeline list

        Args:
            dataset_id: Dataset ID
            pipeline_id: Pipeline ID to add

        Returns:
            Updated dataset document

        Raises:
            DatasetNotFoundException: If dataset not found
        """
        dataset = await DatasetService.get_dataset_by_id(dataset_id)
        pipeline_id = PydanticObjectId(pipeline_id)

        if pipeline_id not in dataset.pipeline_ids:
            dataset.pipeline_ids.append(pipeline_id)
            dataset.updated_at = datetime.now(timezone.utc)
            await dataset.save()

        return dataset

