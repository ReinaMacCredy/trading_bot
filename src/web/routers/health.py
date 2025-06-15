from fastapi import APIRouter
import logging
from src.web.services import HealthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check(health_service: HealthService):
    """Check server health"""
    return await health_service.check_health() 