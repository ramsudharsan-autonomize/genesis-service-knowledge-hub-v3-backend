

from fastapi import APIRouter


router = APIRouter()

@router.get("/")
async def say_hello():
    return {"message": "Hello from genesis-service-knowledge-hub-v3-backend!"}