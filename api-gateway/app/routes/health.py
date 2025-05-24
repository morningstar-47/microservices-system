from fastapi import APIRouter
from services.health_check import check_services_health

router = APIRouter()

@router.get("/health")
async def health():
    return await check_services_health()
