"""Utility functions for converting models to responses"""

from app.models.dataset import Dataset
from app.schemas.dataset import DatasetResponse


def get_dataset_response(dataset: Dataset) -> DatasetResponse:
    """Convert Dataset model to DatasetResponse schema"""
    return DatasetResponse(
        _id=str(dataset.id),
        name=dataset.name,
        description=dataset.description,
        tags=dataset.tags,
        status=dataset.status,
        createdAt=dataset.created_at,
        updatedAt=dataset.updated_at,
        dataSourceId=str(dataset.data_source_id) if dataset.data_source_id else None,
        pipelineIds=[str(pid) for pid in dataset.pipeline_ids],
    )
