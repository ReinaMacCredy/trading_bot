from pydantic import BaseModel, Field
from src.web.models.enums import OrderSide

class TradingViewSignal(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    side: OrderSide = Field(..., description="Signal side (buy/sell)")

__all__ = ["TradingViewSignal"]