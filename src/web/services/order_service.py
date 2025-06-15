from typing import Dict, Any, List
import logging
from src.web.architecture.signal_processor import SignalProcessor
from src.web.api.models import Order
from src.web.middleware import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

class OrderService:
    """Service for handling order-related business logic"""
    
    def __init__(self, signal_processor: SignalProcessor):
        self.signal_processor = signal_processor
    
    async def create_order(self, order: Order) -> Dict[str, Any]:
        """
        Create a new pending order
        
        Args:
            order: Order data
            
        Returns:
            Dict with order creation result
            
        Raises:
            ValidationError: If order validation fails
        """
        try:
            self.signal_processor.add_pending_order(order)
            return {
                "status": "success",
                "message": "Order added to pending orders",
                "order": order.dict()
            }
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise ValidationError(
                f"Error creating order: {str(e)}",
                {"error": str(e)}
            )
    
    async def get_orders(self, symbol: str) -> Dict[str, Any]:
        """
        Get all pending orders for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dict with list of orders
            
        Raises:
            NotFoundError: If symbol not found
        """
        try:
            orders = self.signal_processor.pending_orders.get(symbol, [])
            return {
                "status": "success",
                "orders": [order.dict() for order in orders]
            }
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            raise NotFoundError(
                f"Error getting orders: {str(e)}",
                {"symbol": symbol, "error": str(e)}
            )
    
    async def cancel_orders(self, symbol: str) -> Dict[str, Any]:
        """
        Cancel all pending orders for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dict with cancellation result
            
        Raises:
            NotFoundError: If symbol not found
        """
        try:
            orders = self.signal_processor.pending_orders.get(symbol, [])
            for order in orders:
                self.signal_processor.remove_pending_order(order)
            return {
                "status": "success",
                "message": f"Cancelled {len(orders)} orders for {symbol}"
            }
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            raise NotFoundError(
                f"Error cancelling orders: {str(e)}",
                {"symbol": symbol, "error": str(e)}
            )
