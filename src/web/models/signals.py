"""
Use for webhooks
"""
from pydantic import BaseModel, Field
from typing import Optional
from src.web.models.enums import OrderSide, OrderType

class TradingViewSignal(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    side: OrderSide = Field(..., description="Signal side (buy/sell)")

__all__ = ["TradingViewSignal"]