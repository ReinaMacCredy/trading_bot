"""
Web Frontend Orders API
Handles user orders from web interface
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field, validator

from ..services.redis_service import RedisService

logger = logging.getLogger(__name__)

orders_router = APIRouter()

class OrderRequest(BaseModel):
    """Order request from web frontend"""
    user_id: str = Field(..., description="User identifier")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="buy or sell")
    order_type: str = Field(..., description="market, limit, stop")
    quantity: float = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(default=None, description="Order price for limit orders")
    stop_price: Optional[float] = Field(default=None, description="Stop price for stop orders")
    
    # Order conditions
    trigger_condition: Optional[str] = Field(default=None, description="Trigger condition for order execution")
    strategy_match: Optional[str] = Field(default=None, description="Required strategy signal to match")
    signal_source: Optional[str] = Field(default=None, description="Required signal source (e.g., tradingview)")
    
    # Risk management
    take_profit: Optional[float] = Field(default=None, description="Take profit price")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss price")
    
    # Metadata
    notes: Optional[str] = Field(default="", description="Order notes")
    tags: List[str] = Field(default_factory=list, description="Order tags")

    @validator('side')
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('Side must be buy or sell')
        return v.lower()
    
    @validator('order_type')
    def validate_order_type(cls, v):
        if v.lower() not in ['market', 'limit', 'stop', 'stop_limit']:
            raise ValueError('Invalid order type')
        return v.lower()

class OrderResponse(BaseModel):
    """Order response model"""
    order_id: str
    status: str
    message: str
    timestamp: str

class OrderStatus(BaseModel):
    """Order status model"""
    order_id: str
    user_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str
    created_at: str
    updated_at: Optional[str]
    executed_price: Optional[float]
    executed_quantity: Optional[float]
    notes: str

@orders_router.post("/create", response_model=OrderResponse)
async def create_order(
    order: OrderRequest,
    background_tasks: BackgroundTasks
):
    """
    Create new order from web frontend
    
    Orders are queued in Redis and will be matched against TradingView signals
    or executed when conditions are met.
    """
    try:
        logger.info(f"📝 Creating order: {order.symbol} {order.side} {order.quantity}")
        
        # Validate order data
        if order.order_type in ['limit', 'stop_limit'] and not order.price:
            raise HTTPException(status_code=400, detail="Price required for limit orders")
        
        if order.order_type in ['stop', 'stop_limit'] and not order.stop_price:
            raise HTTPException(status_code=400, detail="Stop price required for stop orders")
        
        # Prepare order data
        order_data = order.dict()
        order_data["source"] = "web_frontend"
        order_data["created_by"] = "web_user"
        
        # Add to Redis queue
        from ..main import redis_service
        if not redis_service:
            raise HTTPException(status_code=500, detail="Redis service not available")
        
        order_id = await redis_service.add_order(order_data)
        
        # Process order in background
        background_tasks.add_task(process_new_order, order_data, order_id)
        
        return OrderResponse(
            order_id=order_id,
            status="queued",
            message=f"Order created successfully: {order.symbol} {order.side} {order.quantity}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating order: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@orders_router.get("/status/{order_id}", response_model=OrderStatus)
async def get_order_status(order_id: str):
    """Get order status by ID"""
    try:
        from ..main import redis_service
        if not redis_service:
            raise HTTPException(status_code=500, detail="Redis service not available")
        
        order_data = await redis_service.get_order(order_id)
        if not order_data:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return OrderStatus(**order_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting order status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting order status: {str(e)}")

@orders_router.get("/user/{user_id}")
async def get_user_orders(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    status: Optional[str] = Query(default=None)
):
    """Get user's orders"""
    try:
        from ..main import redis_service
        if not redis_service:
            raise HTTPException(status_code=500, detail="Redis service not available")
        
        orders = await redis_service.get_user_orders(user_id, limit)
        
        # Filter by status if provided
        if status:
            orders = [order for order in orders if order.get("status") == status]
        
        return {
            "user_id": user_id,
            "orders": orders,
            "total": len(orders),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting user orders: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting user orders: {str(e)}")

@orders_router.put("/cancel/{order_id}")
async def cancel_order(order_id: str):
    """Cancel pending order"""
    try:
        from ..main import redis_service
        if not redis_service:
            raise HTTPException(status_code=500, detail="Redis service not available")
        
        order_data = await redis_service.get_order(order_id)
        if not order_data:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order_data.get("status") not in ["pending", "matched"]:
            raise HTTPException(status_code=400, detail="Order cannot be cancelled")
        
        await redis_service.update_order_status(
            order_id, 
            "cancelled",
            cancelled_at=datetime.now().isoformat()
        )
        
        return {
            "order_id": order_id,
            "status": "cancelled",
            "message": "Order cancelled successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling order: {str(e)}")

@orders_router.get("/queue/stats")
async def get_queue_statistics():
    """Get order queue statistics"""
    try:
        from ..main import redis_service
        if not redis_service:
            raise HTTPException(status_code=500, detail="Redis service not available")
        
        stats = await redis_service.get_queue_stats()
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting queue stats: {str(e)}")

async def process_new_order(order_data: Dict[str, Any], order_id: str):
    """Process new order for immediate or conditional execution"""
    try:
        logger.info(f"🔄 Processing new order {order_id}")
        
        from ..main import order_matching
        if not order_matching:
            logger.error("Order matching service not available")
            return
        
        # Check if order can be executed immediately
        if order_data["order_type"] == "market":
            await order_matching.execute_market_order(order_data)
        else:
            # Add to matching queue for conditional execution
            await order_matching.add_to_matching_queue(order_data)
        
        logger.info(f"✅ Order {order_id} processed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error processing order {order_id}: {e}")
        
        # Update order status to failed
        from ..main import redis_service
        if redis_service:
            await redis_service.update_order_status(
                order_id,
                "failed",
                error_message=str(e)
            ) 