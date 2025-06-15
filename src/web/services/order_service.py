from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import logging
from src.web.models.orders import Order
from src.web.middlewares import ValidationError, NotFoundError
from src.trading.clients.mt5_client import MT5Client

logger = logging.getLogger(__name__)

@dataclass
class OrderResult:
    """Container for MT5 order execution results"""
    success: bool
    order_id: Optional[int] = None
    ticket: Optional[int] = None
    symbol: str = ""
    side: str = ""
    volume: float = 0.0
    price: float = 0.0
    sl: Optional[float] = None
    tp: Optional[float] = None
    comment: str = ""
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

class OrderService:
    """Service for handling order-related business logic"""
    
    def __init__(self, mt5_client: MT5Client):
        self.mt5_client = mt5_client

    async def create_order(self, order: Order) -> OrderResult:
        """
        Create a new order
        
        Args:
            order: Order data
            
        Returns:
            Dict with order creation result
            
        Raises:
            ValidationError: If order validation fails
        """
        try:
            if order.type.lower() == "limit":
                result = await self.mt5_client.place_pending_order(order.symbol, order.side, order.volume, order.price, order.stop_loss, order.take_profit, order.comment)
            else:
                result = await self.mt5_client.place_market_order(order.symbol, order.side, order.volume, order.stop_loss, order.take_profit, order.comment)

            return OrderResult(
                success=True,
                order_id=result.order_id,
                ticket=result.ticket,
                symbol=order.symbol,
                side=order.side,
                volume=order.volume,
                price=order.price,
                sl=order.stop_loss,
                tp=order.take_profit,
                comment=order.comment,
                error_code=result.error_code,
                error_message=result.error_message,
                metadata=result.metadata
            )
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise ValidationError(
                f"Error creating order: {str(e)}",
                {"error": str(e)}
            )
        
    async def get_orders(self) -> List[Dict]:
        """Get all orders"""
        return await self.mt5_client.fetch_open_orders()

__all__ = ["OrderService", "OrderResult"]