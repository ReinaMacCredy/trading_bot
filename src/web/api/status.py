"""
Status API
Provides system status and monitoring endpoints
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

status_router = APIRouter()

class SystemStatus(BaseModel):
    """System status response model"""
    status: str
    timestamp: str
    services: Dict[str, Any]
    queue_stats: Dict[str, Any]
    uptime: str

@status_router.get("/health", response_model=SystemStatus)
async def get_system_health():
    """Get comprehensive system health status"""
    try:
        from ..main import redis_service, trading_service, order_matching
        
        services_status = {}
        
        # Check Redis service
        try:
            if redis_service:
                await redis_service.test_connection()
                services_status["redis"] = {"status": "healthy", "message": "Connected"}
            else:
                services_status["redis"] = {"status": "unavailable", "message": "Service not initialized"}
        except Exception as e:
            services_status["redis"] = {"status": "error", "message": str(e)}
        
        # Check Trading service
        try:
            if trading_service and trading_service.initialized:
                services_status["trading"] = {"status": "healthy", "message": "Initialized and ready"}
            else:
                services_status["trading"] = {"status": "unavailable", "message": "Service not initialized"}
        except Exception as e:
            services_status["trading"] = {"status": "error", "message": str(e)}
        
        # Check Order matching service
        try:
            if order_matching and order_matching.matching_loop_running:
                services_status["order_matching"] = {"status": "healthy", "message": "Loop running"}
            else:
                services_status["order_matching"] = {"status": "unavailable", "message": "Loop not running"}
        except Exception as e:
            services_status["order_matching"] = {"status": "error", "message": str(e)}
        
        # Get queue statistics
        queue_stats = {}
        try:
            if redis_service:
                queue_stats = await redis_service.get_queue_stats()
        except Exception as e:
            queue_stats = {"error": str(e)}
        
        # Determine overall status
        overall_status = "healthy"
        for service, status in services_status.items():
            if status["status"] in ["error", "unavailable"]:
                overall_status = "degraded"
                break
        
        return SystemStatus(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            services=services_status,
            queue_stats=queue_stats,
            uptime="N/A"  # Could implement uptime tracking
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting system health: {str(e)}")

@status_router.get("/redis")
async def get_redis_status():
    """Get Redis connection status"""
    try:
        from ..main import redis_service
        
        if not redis_service:
            return {"status": "unavailable", "message": "Redis service not initialized"}
        
        await redis_service.test_connection()
        stats = await redis_service.get_queue_stats()
        
        return {
            "status": "connected",
            "timestamp": datetime.now().isoformat(),
            "queue_stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Redis status check failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@status_router.get("/trading")
async def get_trading_status():
    """Get trading service status"""
    try:
        from ..main import trading_service
        
        if not trading_service:
            return {"status": "unavailable", "message": "Trading service not initialized"}
        
        if not trading_service.initialized:
            return {"status": "not_initialized", "message": "Trading service not initialized"}
        
        # Test price fetching
        test_price = await trading_service.get_current_price("BTCUSDT")
        
        return {
            "status": "healthy",
            "initialized": trading_service.initialized,
            "test_price": test_price,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Trading status check failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@status_router.get("/signals")
async def get_recent_signals():
    """Get recent TradingView signals"""
    try:
        from ..main import redis_service
        
        if not redis_service:
            return {"error": "Redis service not available"}
        
        signals = await redis_service.get_recent_signals(limit=10)
        
        return {
            "signals": signals,
            "count": len(signals),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting recent signals: {e}")
        return {"error": str(e)}

@status_router.get("/orders/summary")
async def get_orders_summary():
    """Get order statistics summary"""
    try:
        from ..main import redis_service
        
        if not redis_service:
            return {"error": "Redis service not available"}
        
        stats = await redis_service.get_queue_stats()
        
        return {
            "summary": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting orders summary: {e}")
        return {"error": str(e)} 