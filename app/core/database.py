import logging

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.dataset_model import Dataset
from app.models.document_model import Document
from app.models.document_pipeline_run_model import DocumentPipelineRun

logger = logging.getLogger(__name__)


async def init_db():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    await init_beanie(
        database=client[settings.DB_NAME],
        document_models=[Dataset, Document, DocumentPipelineRun],
    )
    logger.info("Beanie initialized and MongoDB connected.")
