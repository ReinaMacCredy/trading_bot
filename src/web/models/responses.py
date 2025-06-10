"""
Response Models for Web API
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class APIResponse(BaseModel):
    """Base API response"""
    status: str
    message: str
    timestamp: str = datetime.now().isoformat()

class OrderResponse(APIResponse):
    """Order creation response"""
    order_id: str

class OrderStatusResponse(BaseModel):
    """Order status response"""
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