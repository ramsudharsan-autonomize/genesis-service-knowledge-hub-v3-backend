"""Pipeline service for triggering document processing pipelines"""

import logging
from beanie import PydanticObjectId
import httpx
from app.models.dataset_model import Dataset
from app.models.document_model import Document
from app.schemas.pipeline_schema import PipelineInfo
from app.services.dataset_service import DatasetService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

# TODO: Move to config/env when ready hardcoded it for the time being with-
# the one example that Ram used
PIPELINE_RUN_ID = "acb4a50c-6a94-4bdc-b968-c79a55dce770"
PIPELINE_API_KEY = "sk-MLfyw35NdI8zbWcUJug_jdYIwG4bdPC3KqX6EWCGc6I"
PIPELINE_BASE_URL = "https://api-ai-studio.dev-v2.autonomize.ai/api/v1"


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
    async def trigger_dataset_pipelines(document: Document):
        dataset = await DatasetService.get_dataset_by_id(document.dataset_id)
        storage_config = StorageService.get_default_storage_config()

        # Get read signed URL for the document
        document_url = StorageService.get_read_signed_url(
            file_name=document.storage.path,
            storage_type=storage_config["storage_type"],
            container_name=document.storage.container,
            storage_account=storage_config["storage_account"],
        )
        # TODO


    @staticmethod
    async def trigger_pipeline(document_url: str, session_id: str) -> dict:
        """
        Trigger the pipeline to process an uploaded document.

        Args:
            document_url: Signed URL to the uploaded document
            session_id: Unique session identifier (e.g., dataset_id or document_id)

        Returns:
            Pipeline response data
        """
        url = f"{PIPELINE_BASE_URL}/run/{PIPELINE_RUN_ID}?stream=false"

        sample_payload = {
            "output_type": "chat",
            "input_type": "chat",
            "input_value": "Process this document",
            "tweaks": {"FilePathInput-dZGhC": {"input_value": document_url}},
            "session_id": session_id,
        }

        headers = {"Content-Type": "application/json", "x-api-key": PIPELINE_API_KEY}

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                logger.info(f"Triggering pipeline for session: {session_id}")
                response = await client.post(url, json=sample_payload, headers=headers)
                response.raise_for_status()

                result = response.json()
                logger.info(f"Pipeline triggered successfully for session: {session_id}")
                return result

            except httpx.HTTPStatusError as e:
                logger.error(f"Pipeline trigger failed with status {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Pipeline trigger error: {str(e)}")
                raise

    @staticmethod
    async def get_all_pipelines() -> list[PipelineInfo]:
        """
        Get all available pipelines from LangFlow.

        Returns:
            List of pipeline information objects
        """
        url = f"{PIPELINE_BASE_URL}/flows/"
        headers = {
            "x-api-key": PIPELINE_API_KEY,
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
        url = f"{PIPELINE_BASE_URL}/flows/{pipeline_id}"
        headers = {
            "x-api-key": PIPELINE_API_KEY,
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
