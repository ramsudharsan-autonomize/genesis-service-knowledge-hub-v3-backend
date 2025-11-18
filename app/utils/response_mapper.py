"""Utility functions for converting models to responses"""

from app.models.dataset import Dataset
from app.schemas.dataset import DatasetResponse


def get_dataset_response(dataset: Dataset) -> DatasetResponse:
    """Convert Dataset model to DatasetResponse schema"""
    return DatasetResponse(
        id=str(dataset.id),
        name=dataset.name,
        description=dataset.description,
        tags=dataset.tags,
        status=dataset.status,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        data_source_id=str(dataset.data_source_id) if dataset.data_source_id else None,
        pipeline_ids=[str(pid) for pid in dataset.pipeline_ids],
    )
