from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.routes import hello_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB and init mappings
    await init_db()
    yield
    # Shutdown: Connection closes automatically by Motor's cleanup
    pass


app = FastAPI(lifespan=lifespan, title="FastAPI + Beanie + uv")
app.include_router(hello_router, prefix="/hello", tags=["Hello"])
