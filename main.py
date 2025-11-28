from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Allow all origins, methods, and headers for CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Set to True if your frontend needs to send cookies or authorization headers
    allow_methods=["*"],     # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],     # Allow all headers in the request
)

app.include_router(dataset_router, prefix="/api/v3/knowledge_hub/datasets", tags=["Datasets"])
app.include_router(document_router, prefix="/api/v3/knowledge_hub/documents", tags=["Documents"])
app.include_router(pipeline_router, prefix="/api/v3/knowledge_hub/pipelines", tags=["Pipelines"])
