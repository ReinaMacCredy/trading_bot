"""
Request Models for Web API
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

class TradingViewWebhookRequest(BaseModel):
    """TradingView webhook request model"""
    symbol: str
    action: str  # buy, sell, close
    price: float
    quantity: Optional[float] = 0
    strategy: Optional[str] = ""
    timeframe: Optional[str] = ""
    timestamp: Optional[str] = ""

class WebOrderRequest(BaseModel):
    """Web frontend order request"""
    user_id: str
    symbol: str
    side: str  # buy, sell
    order_type: str  # market, limit, stop
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    
    # Conditions
    trigger_condition: Optional[str] = None
    strategy_match: Optional[str] = None
    signal_source: Optional[str] = None
    
    # Risk management
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    
    @validator('side')
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('Side must be buy or sell')
        return v.lower() 