import logging

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models import Dataset

logger = logging.getLogger(__name__)


async def init_db():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    await init_beanie(
        database=client[settings.DB_NAME],
        document_models=[Dataset],
    )
    logger.info("Beanie initialized and MongoDB connected.")
