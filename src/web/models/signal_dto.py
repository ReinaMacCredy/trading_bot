from pydantic import BaseModel

class TradingViewSignal(BaseModel):
    symbol: str
    price: float
    action: str  # "buy" hoặc "sell"
    strategy: str | None = None

__all__ = ["TradingViewSignal"]