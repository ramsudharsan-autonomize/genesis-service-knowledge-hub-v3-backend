"""Service for managing document pipeline runs"""

import logging
from datetime import datetime, timezone
from beanie import PydanticObjectId
from app.models.document_pipeline_run_model import DocumentPipelineRun
from app.utils.enums import ProcessingStatus
from app.core.exceptions import ValidationException, PipelineRunNotFoundException

logger = logging.getLogger(__name__)


class DocumentPipelineRunService:
    """Service for creating and managing document pipeline run records"""

    @staticmethod
    async def create_pipeline_runs_for_document(
        document_id: PydanticObjectId,
        dataset_id: PydanticObjectId,
        pipeline_ids: list[str],
    ) -> list[DocumentPipelineRun]:
        """
        Create pipeline run records for all pipelines in a dataset (batch insert).

        Args:
            document_id: The document ID
            dataset_id: The dataset ID
            pipeline_ids: List of pipeline IDs to create runs for

        Returns:
            List of created DocumentPipelineRun records

        Raises:
            ValidationException: If batch insert fails
        """
        if not pipeline_ids:
            logger.info(f"No pipelines to run for document {document_id}")
            return []

        # Build all run objects first
        runs = [
            DocumentPipelineRun(
                document_id=document_id,
                dataset_id=dataset_id,
                pipeline_id=pid,
                status=ProcessingStatus.PENDING,
            )
            for pid in pipeline_ids
        ]

        try:
            # Batch insert all runs at once
            result = await DocumentPipelineRun.insert_many(runs)
            logger.info(f"Created {len(result.inserted_ids)} pipeline runs for document {document_id}")
            return runs
        except Exception as e:
            logger.error(f"Failed to create pipeline runs for document {document_id}: {e}")
            raise ValidationException(f"Failed to create pipeline runs: {str(e)}")

    @staticmethod
    async def update_run_status(
        run_id: PydanticObjectId,
        status: ProcessingStatus,
        error_message: str | None = None,
    ) -> DocumentPipelineRun:
        """
        Update the status of a pipeline run.

        Args:
            run_id: The pipeline run ID
            status: New status
            error_message: Optional error message (for ERROR status)

        Returns:
            Updated DocumentPipelineRun

        Raises:
            PipelineRunNotFoundException: If run not found
        """
        run = await DocumentPipelineRun.get(run_id)

        if not run:
            raise PipelineRunNotFoundException(run_id)

        try:
            run.status = status
            run.updated_at = datetime.now(timezone.utc)

            if error_message:
                run.error_message = error_message

            await run.save()
            logger.info(f"Updated pipeline run {run_id} status to {status.value}")
            return run
        except Exception as e:
            logger.error(f"Failed to update pipeline run {run_id}: {e}")
            raise ValidationException(f"Failed to update pipeline run status: {str(e)}")

    @staticmethod
    async def update_run_status_by_instance(
        run: DocumentPipelineRun,
        status: ProcessingStatus,
        error_message: str | None = None,
    ) -> DocumentPipelineRun:
        """
        Update the status of a pipeline run (using existing instance to avoid extra DB call).

        Args:
            run: The pipeline run instance
            status: New status
            error_message: Optional error message (for ERROR status)

        Returns:
            Updated DocumentPipelineRun
        """
        try:
            run.status = status
            run.updated_at = datetime.now(timezone.utc)

            if error_message:
                run.error_message = error_message

            await run.save()
            logger.info(f"Updated pipeline run {run.id} status to {status.value}")
            return run
        except Exception as e:
            logger.error(f"Failed to update pipeline run {run.id}: {e}")
            raise ValidationException(f"Failed to update pipeline run status: {str(e)}")

    @staticmethod
    async def get_runs_by_document(document_id: PydanticObjectId) -> list[DocumentPipelineRun]:
        """
        Get all pipeline runs for a document.

        Args:
            document_id: The document ID

        Returns:
            List of DocumentPipelineRun records

        Raises:
            ValidationException: If query fails
        """
        try:
            runs = await DocumentPipelineRun.find(DocumentPipelineRun.document_id == document_id).to_list()
            return runs
        except Exception as e:
            logger.error(f"Failed to get runs for document {document_id}: {e}")
            raise ValidationException(f"Failed to get pipeline runs: {str(e)}")

    @staticmethod
    async def get_runs_by_dataset(dataset_id: PydanticObjectId) -> list[DocumentPipelineRun]:
        """
        Get all pipeline runs for a dataset.

        Args:
            dataset_id: The dataset ID

        Returns:
            List of DocumentPipelineRun records

        Raises:
            ValidationException: If query fails
        """
        try:
            runs = await DocumentPipelineRun.find(DocumentPipelineRun.dataset_id == dataset_id).to_list()
            return runs
        except Exception as e:
            logger.error(f"Failed to get runs for dataset {dataset_id}: {e}")
            raise ValidationException(f"Failed to get pipeline runs: {str(e)}")

    @staticmethod
    async def get_pending_runs() -> list[DocumentPipelineRun]:
        """
        Get all pending pipeline runs (useful for retry/recovery).

        Returns:
            List of DocumentPipelineRun records with PENDING status

        Raises:
            ValidationException: If query fails
        """
        try:
            runs = await DocumentPipelineRun.find(DocumentPipelineRun.status == ProcessingStatus.PENDING).to_list()
            return runs
        except Exception as e:
            logger.error(f"Failed to get pending runs: {e}")
            raise ValidationException(f"Failed to get pending pipeline runs: {str(e)}")
