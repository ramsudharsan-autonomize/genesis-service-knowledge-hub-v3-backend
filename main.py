from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.routes.dataset_routes import router as dataset_router
from app.routes.document_routes import router as document_router
from app.routes.pipeline_routes import router as pipeline_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    # Shutdown: Connection closes automatically by Motor's cleanup
    pass


app = FastAPI(lifespan=lifespan, title="Knowledge Hub V3")
app.include_router(dataset_router, prefix="/api/v3/knowledge_hub/datasets", tags=["Datasets"])
app.include_router(document_router, prefix="/api/v3/knowledge_hub/documents", tags=["Documents"])
app.include_router(pipeline_router, prefix="/api/v3/knowledge_hub/pipelines", tags=["Pipelines"])
