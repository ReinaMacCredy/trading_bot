from pydantic import BaseModel, Field
from typing import Optional
from src.web.models.enums import OrderSide, OrderType

class Order(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    side: OrderSide = Field(..., description="Order side (buy/sell)")
    type: OrderType = Field(..., description="Order type (market/limit)")
    volume: float = Field(..., description="Order volume") # lot size
    price: float = Field(0.0, description="Limit price (required for limit orders)")
    stop_loss: Optional[float] = Field(0.0, description="Stop loss price")
    take_profit: Optional[float] = Field(0.0, description="Take profit price")
    comment: str = Field("Discord Bot", description="Order comment")
    
__all__ = ["Order"]