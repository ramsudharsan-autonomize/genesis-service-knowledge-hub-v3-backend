from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.routes import dataset_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    # Shutdown: Connection closes automatically by Motor's cleanup
    pass


app = FastAPI(lifespan=lifespan, title="Knowledge Hub V3")
app.include_router(dataset_router, prefix="/api/v3/knowledge_hub/datasets", tags=["Datasets"])
