import logging

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings

logger = logging.getLogger(__name__)

async def init_db():
    # 1. Create the Motor Client (Connection Pooling)
    client = AsyncIOMotorClient(settings.MONGO_URL)

    # 2. Initialize Beanie with the database and list of models
    await init_beanie(
        database=client[settings.DB_NAME],
        document_models=[],
    )
    logger.info("Beanie initialized and MongoDB connected.")
