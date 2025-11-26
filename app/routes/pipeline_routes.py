"""Pipeline API router for LangFlow pipeline operations"""

import math
from beanie import PydanticObjectId
from fastapi import APIRouter, Query

from app.schemas.dataset_schema import DatasetPipelinesResponse
from app.schemas.pipeline_schema import (
    PipelineInfo,
    DocumentPipelineRunResponse,
    PaginatedPipelineRunsResponse,
)
from app.services.pipeline_service import PipelineService
from app.services.document_pipeline_run_service import DocumentPipelineRunService
from app.utils.enums import ProcessingStatus
from app.utils.error_handler import handle_exception


router = APIRouter()


@router.get(
    "/{dataset_id}/pipelines",
    response_model=DatasetPipelinesResponse,
    summary="Get all pipelines attached to a dataset",
)
async def get_dataset_pipelines(
    dataset_id: PydanticObjectId,
) -> DatasetPipelinesResponse:
    """
    Get all pipelines attached to a specific dataset with detailed information

    - **dataset_id**: The ID of the dataset
    """
    try:
        dataset, pipelines = await PipelineService.get_pipelines_by_dataset(dataset_id)
        response = DatasetPipelinesResponse(
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            pipeline_ids=dataset.pipeline_ids,
            pipelines=pipelines,
            pipeline_count=len(dataset.pipeline_ids),
        )
        return response
    except Exception as e:
        handle_exception(e, "retrieving pipelines for the dataset")


@router.get(
    "/",
    response_model=list[PipelineInfo],
    summary="Get all available pipelines",
)
async def list_pipelines() -> list[PipelineInfo]:
    """
    Get all available pipelines from LangFlow

    Returns a list of all pipelines (excluding components) that can be
    attached to datasets for document processing.
    """
    try:
        pipelines = await PipelineService.get_all_pipelines()
        return pipelines
    except Exception as e:
        handle_exception(e, "retrieving pipelines")


@router.get(
    "/{pipeline_id}",
    response_model=PipelineInfo,
    summary="Get pipeline by ID",
)
async def get_pipeline(pipeline_id: str) -> PipelineInfo:
    """
    Get a specific pipeline by ID

    - **pipeline_id**: The UUID of the pipeline to retrieve

    Returns detailed information about the pipeline including name,
    description, icon, and metadata.
    """
    try:
        pipeline = await PipelineService.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            from app.core.exceptions import BaseAppException

            raise BaseAppException(message=f"Pipeline with ID '{pipeline_id}' not found", error_code=404)
        return pipeline
    except Exception as e:
        handle_exception(e, "retrieving the pipeline")


@router.get(
    "/runs",
    response_model=PaginatedPipelineRunsResponse,
    summary="Get all pipeline runs (paginated)",
)
async def get_pipeline_runs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    status: ProcessingStatus | None = Query(None, description="Filter by processing status"),
) -> PaginatedPipelineRunsResponse:
    """
    Get all document pipeline runs with pagination.

    - **page**: Page number (starting from 1)
    - **page_size**: Number of items per page (1-100)
    - **status**: Optional filter by processing status

    Returns a paginated list of pipeline run records.
    """
    try:
        runs, total = await DocumentPipelineRunService.get_all_runs_paginated(
            page=page,
            page_size=page_size,
            status=status,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        items = [
            DocumentPipelineRunResponse(
                id=str(run.id),
                document_id=str(run.document_id),
                dataset_id=str(run.dataset_id),
                pipeline_id=run.pipeline_id,
                status=run.status,
                error_message=run.error_message,
                created_at=run.created_at,
                updated_at=run.updated_at,
            )
            for run in runs
        ]

        return PaginatedPipelineRunsResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        handle_exception(e, "retrieving pipeline runs")
