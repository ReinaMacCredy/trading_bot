# from fastapi import APIRouter, Depends
# import logging
# from src.web.services import HealthService

# logger = logging.getLogger(__name__)
# router = APIRouter(prefix="/health", tags=["health"])

# @router.get("/", response_model=None)  # disable automatic response model inferrence
# async def health_check(health_service: HealthService = Depends()):
#     """Check server health"""
#     return await health_service.check_health()
