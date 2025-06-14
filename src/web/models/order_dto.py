from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrderDTO(BaseModel):
    name: str
    description: Optional[str] = None
    topPrice: float
    bottomPrice: float
    profitTarget: List[float]
    lotSize: float
    stopLoss: List[float]
    action: bool  # True = Mua, False = Bán
    symbol: str
    expirationDate: datetime

__all__ = ["OrderDTO"]