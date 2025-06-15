"""
Use for webhooks
"""
from pydantic import BaseModel, Field
from typing import Optional
from src.web.models.enums import OrderSide, OrderType

class TradingViewSignal(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    side: OrderSide = Field(..., description="Signal side (buy/sell)")
    type: OrderType = Field(..., description="Order type (market/limit)")
    volume: float = Field(..., description="Order volume")
    price: Optional[float] = Field(None, description="Limit price (required for limit orders)")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")

__all__ = ["TradingViewSignal"]