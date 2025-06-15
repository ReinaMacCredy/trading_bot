from functools import lru_cache
from src.trading.clients.mt5_client import MT5Client
from src.trading.core.legacy_trading import TradeExecutor
from src.web.api.services import OrderService, PositionService

@lru_cache()
def get_mt5_client() -> MT5Client:
    """Get MT5 client instance"""
    return MT5Client()

@lru_cache()
def get_trade_executor() -> TradeExecutor:
    """Get trade executor instance"""
    return TradeExecutor(get_mt5_client())

@lru_cache()
def get_order_service() -> OrderService:
    """Get order service instance"""
    return OrderService(get_mt5_client())

@lru_cache()
def get_position_service() -> PositionService:
    """Get position service instance"""
    return PositionService(get_mt5_client()) 