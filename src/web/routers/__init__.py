from fastapi import APIRouter
from src.web.routers import orders
from .health import router as health_router

# Create main API router
api_router = APIRouter()

# Include all routers
# api_router.include_router(webhook.router)
# api_router.include_router(positions.router)
api_router.include_router(orders.router)
api_router.include_router(health_router, prefix="/health") 