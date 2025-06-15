from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"

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

class Order(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    side: OrderSide = Field(..., description="Order side (buy/sell)")
    type: OrderType = Field(..., description="Order type (market/limit)")
    volume: float = Field(..., description="Order volume")
    price: Optional[float] = Field(None, description="Limit price (required for limit orders)")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")

class TradingViewSignal(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    side: OrderSide = Field(..., description="Signal side (buy/sell)")
    type: OrderType = Field(..., description="Order type (market/limit)")
    volume: float = Field(..., description="Order volume")
    price: Optional[float] = Field(None, description="Limit price (required for limit orders)")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")

class SuccessResponse(BaseModel):
    status: str = Field("success", description="Response status")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

class ErrorResponse(BaseModel):
    status: str = Field("error", description="Response status")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")

class PositionsResponse(BaseModel):
    status: str = Field("success", description="Response status")
    message: Optional[str] = Field(None, description="Success message")
    positions: List[Position] = Field(..., description="List of active positions") 