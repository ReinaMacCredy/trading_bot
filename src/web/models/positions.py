from pydantic import BaseModel, Field
from typing import Optional
from src.web.models.enums import OrderSide

class Position(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    side: OrderSide = Field(..., description="Position side (buy/sell)")
    volume: float = Field(..., description="Position volume")
    entry_price: float = Field(..., description="Entry price")
    current_price: float = Field(..., description="Current market price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    profit: float = Field(..., description="Current profit/loss")

class PositionUpdate(BaseModel):
    take_profit: Optional[float] = Field(None, description="New take profit price")
    stop_loss: Optional[float] = Field(None, description="New stop loss price")


__all__ = ["Position", "PositionUpdate"]