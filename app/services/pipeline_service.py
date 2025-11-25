"""Pipeline service for triggering document processing pipelines"""

import asyncio
import logging
from beanie import PydanticObjectId
import httpx
from app.core.config import settings
from app.models.dataset_model import Dataset
from app.models.document_pipeline_run_model import DocumentPipelineRun
from app.schemas.pipeline_schema import PipelineInfo, PipelineExecutionResult
from app.services.dataset_service import DatasetService
from app.services.document_service import DocumentService
from app.services.document_pipeline_run_service import DocumentPipelineRunService
from app.services.storage_service import StorageService
from app.utils.enums import ProcessingStatus

logger = logging.getLogger(__name__)


class PipelineService:
    """Service for triggering, populating and everything related to document processing pipelines"""

    @staticmethod
    async def get_pipelines_by_dataset(dataset_id: PydanticObjectId) -> tuple[Dataset, list[PipelineInfo]]:
        """
        Get all pipelines attached to a dataset with detailed info

        Args:
            dataset_id: Dataset ID

        Returns:
            Tuple of (dataset, list of pipeline details)

        Raises:
            DatasetNotFoundException: If dataset not found
        """
        dataset = await DatasetService.get_dataset_by_id(dataset_id)

        # Fetch pipeline details from LangFlow
        pipelines = []
        if dataset.pipeline_ids:
            try:
                pipelines = await PipelineService.get_pipelines_by_ids(dataset.pipeline_ids)
            except Exception as e:
                logger.error(f"Failed to fetch pipeline details: {str(e)}")
                # Return empty pipelines list but don't fail the request

        return dataset, pipelines

    @staticmethod
    async def get_all_pipelines() -> list[PipelineInfo]:
        """
        Get all available pipelines from LangFlow.

        Returns:
            List of pipeline information objects
        """
        url = f"{settings.PIPELINE_BASE_URL}/flows/"
        headers = {
            "x-api-key": settings.PIPELINE_API_KEY,
            "Accept-Encoding": "gzip, deflate",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                logger.info("Fetching all pipelines from LangFlow")
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                flows = response.json()
                pipelines = [
                    PipelineInfo(
                        id=flow["id"],
                        name=flow.get("name", ""),
                        description=flow.get("description"),
                        icon=flow.get("icon"),
                        is_component=flow.get("is_component", False),
                        folder_id=flow.get("folder_id"),
                        updated_at=flow.get("updated_at"),
                    )
                    for flow in flows
                    if not flow.get("is_component", False)  # Filter out components
                ]

                logger.info(f"Retrieved {len(pipelines)} pipelines")
                return pipelines

            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to fetch pipelines: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"Error fetching pipelines: {str(e)}")
                raise

    @staticmethod
    async def get_pipeline_by_id(pipeline_id: str) -> PipelineInfo | None:
        """
        Get a specific pipeline by ID.

        Args:
            pipeline_id: The pipeline UUID

        Returns:
            Pipeline information or None if not found
        """
        url = f"{settings.PIPELINE_BASE_URL}/flows/{pipeline_id}"
        headers = {
            "x-api-key": settings.PIPELINE_API_KEY,
            "Accept-Encoding": "gzip, deflate",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                logger.info(f"Fetching pipeline: {pipeline_id}")
                response = await client.get(url, headers=headers)

                if response.status_code == 404:
                    logger.warning(f"Pipeline not found: {pipeline_id}")
                    return None

                response.raise_for_status()
                flow = response.json()

                return PipelineInfo(
                    id=flow["id"],
                    name=flow.get("name", ""),
                    description=flow.get("description"),
                    icon=flow.get("icon"),
                    is_component=flow.get("is_component", False),
                    folder_id=flow.get("folder_id"),
                    updated_at=flow.get("updated_at"),
                )

            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to fetch pipeline {pipeline_id}: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"Error fetching pipeline {pipeline_id}: {str(e)}")
                raise

    @staticmethod
    async def get_pipelines_by_ids(pipeline_ids: list[str]) -> list[PipelineInfo]:
        """
        Get multiple pipelines by their IDs.

        Args:
            pipeline_ids: List of pipeline UUIDs

        Returns:
            List of pipeline information objects (only found pipelines)
        """
        if not pipeline_ids:
            return []

        pipelines = []
        for pipeline_id in pipeline_ids:
            pipeline = await PipelineService.get_pipeline_by_id(pipeline_id)
            if pipeline:
                pipelines.append(pipeline)

        return pipelines

    @staticmethod
    async def trigger_all_pipelines_for_document(
        document_id: PydanticObjectId,
    ) -> list[PipelineExecutionResult]:
        """
        Trigger all pipelines for a document in parallel.

        This method:
        1. Gets the document and its storage details from MongoDB
        2. Gets all pipeline IDs from the dataset
        3. Creates DocumentPipelineRun records (PENDING)
        4. Generates a signed URL for the document
        5. Triggers all pipelines in parallel
        6. Updates each run's status based on result

        Args:
            document_id: The document ID

        Returns:
            List of PipelineExecutionResult with status for each pipeline

        Raises:
            DocumentNotFoundException: If document not found
            DatasetNotFoundException: If dataset not found
            ValidationException: If any other error occurs
        """
        try:
            # Step 1: Get document from MongoDB using DocumentService
            document = await DocumentService.get_document_by_id(document_id)

            # Step 2: Get dataset and its pipeline IDs
            dataset = await DatasetService.get_dataset_by_id(document.dataset_id)

            if not dataset.pipeline_ids:
                logger.info(f"No pipelines configured for dataset {document.dataset_id}")
                return []

            # Step 3: Create pipeline run records (batch insert, PENDING status)
            runs = await DocumentPipelineRunService.create_pipeline_runs_for_document(
                document_id=document_id,
                dataset_id=document.dataset_id,
                pipeline_ids=dataset.pipeline_ids,
            )

            if not runs:
                return []

            # Step 4: Generate signed URL for the document using storage details from document
            storage_config = StorageService.get_default_storage_config()
            document_url = StorageService.get_read_signed_url(
                file_name=document.storage.path,
                storage_type=document.storage.type.value,
                container_name=document.storage.container,
                storage_account=storage_config["storage_account"],
            )

            # Step 5: Trigger all pipelines in parallel
            tasks = [_execute_single_pipeline(run, document_url) for run in runs]

            results = await asyncio.gather(*tasks, return_exceptions=False)

            logger.info(f"Completed processing {len(results)} pipelines for document {document_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to trigger pipelines for document {document_id}: {e}")
            raise


async def _execute_single_pipeline(
    run: DocumentPipelineRun,
    document_url: str,
) -> PipelineExecutionResult:
    """
    Execute a single pipeline and update its status.

    Args:
        run: The DocumentPipelineRun record
        document_url: Signed URL to the document
        session_id: Session ID for the pipeline (usually document_id)

    Returns:
        PipelineExecutionResult with the execution outcome
    """
    pipeline_id = run.pipeline_id

    try:
        # Update status to PROCESSING
        await DocumentPipelineRunService.update_run_status_by_instance(
            run=run,
            status=ProcessingStatus.PROCESSING,
        )

        # Trigger the pipeline
        await _call_langflow_pipeline(
            pipeline_id=pipeline_id,
            document_url=document_url,
            run_id=run.id,
        )

        # Update status to PROCESSED
        await DocumentPipelineRunService.update_run_status_by_instance(
            run=run,
            status=ProcessingStatus.PROCESSED,
        )

        logger.info(f"Pipeline {pipeline_id} completed successfully for run {run.id}")
        return PipelineExecutionResult(
            pipeline_id=pipeline_id,
            run_id=run.id,
            status=ProcessingStatus.PROCESSED,
        )

    except Exception as e:
        error_message = str(e)
        logger.error(f"Pipeline {pipeline_id} failed for run {run.id}: {error_message}")

        # Update status to ERROR
        try:
            await DocumentPipelineRunService.update_run_status_by_instance(
                run=run,
                status=ProcessingStatus.ERROR,
                error_message=error_message,
            )
        except Exception as update_error:
            logger.error(f"Failed to update error status for run {run.id}: {update_error}")

        return PipelineExecutionResult(
            pipeline_id=pipeline_id,
            run_id=run.id,
            status=ProcessingStatus.ERROR,
            error_message=error_message,
        )


async def _call_langflow_pipeline(
    pipeline_id: str,
    document_url: str,
    run_id: str,
) -> dict:
    """
    Call the LangFlow API to run a pipeline.

    Args:
        pipeline_id: The LangFlow pipeline/flow ID
        document_url: Signed URL to the document
        session_id: Session identifier

    Returns:
        Pipeline response data

    Raises:
        httpx.HTTPStatusError: If the API call fails
        Exception: For any other errors
    """
    url = f"{settings.PIPELINE_BASE_URL}/run/{pipeline_id}?stream=false"

    # TODO: These tweaks may need to be configurable per pipeline
    payload = {
        "output_type": "chat",
        "input_type": "text",
        "input_value": document_url,
        "session_id": run_id,
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.PIPELINE_API_KEY,
    }

    timeout = float(settings.PIPELINE_RUN_TIMEOUT_SECONDS)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"Calling LangFlow pipeline {pipeline_id} for session {run_id}")
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            logger.info(f"LangFlow pipeline {pipeline_id} returned successfully")
            return result

    except httpx.TimeoutException as e:
        logger.error(f"Pipeline {pipeline_id} timed out for session {run_id}")
        raise Exception(f"Pipeline request timed out after {timeout} seconds") from e
    except httpx.HTTPStatusError as e:
        logger.error(f"Pipeline {pipeline_id} failed with status {e.response.status_code}: {e.response.text}")
        raise Exception(f"Pipeline API returned {e.response.status_code}: {e.response.text}") from e
    except Exception as e:
        logger.error(f"Pipeline {pipeline_id} error for session {run_id}: {e}")
        raise
