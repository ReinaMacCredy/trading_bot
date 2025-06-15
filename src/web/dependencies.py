from archi import Broker
from contextlib import asynccontextmanager
from src.trading.clients.mt5_client import MT5Client
from src.web.services.order_service import OrderService

from logging import getLogger

logger = getLogger(__name__)

_broker = None
_mt5_client = None
_order_service = None

def get_broker():
    if _broker is None:
        raise RuntimeError("Broker not initialized")
    
    return _broker

def get_mt5_client():
    if _mt5_client is None:
        raise RuntimeError("MT5 client not initialized")
    
    return _mt5_client

def get_order_service():
    if _order_service is None:
        raise RuntimeError("Order service not initialized")
    
    return _order_service

@asynccontextmanager
async def life_span():
    # starts up
    global _broker, _mt5_client, _order_service
    try:
        _broker = Broker()
        _mt5_client = MT5Client()
        _order_service = OrderService(_mt5_client)

        yield
        
        _mt5_client.shutdown()
        logger.info("HTTP server shutdown complete")

    except Exception as e:
        logger.error(f"Error during life span: {e}")
        raise

    # shuts down

__all__ = ["get_broker", "life_span"]