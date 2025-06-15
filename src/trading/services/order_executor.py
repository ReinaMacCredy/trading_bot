import logging
from typing import Optional, Dict, Any
from datetime import datetime
import MetaTrader5 as mt5

from src.web.models.order_dto import OrderDTO, Action, OrderType, Status
from src.trading.clients.mt5_client import MT5Client

logger = logging.getLogger(__name__)

class OrderExecutor:
    def __init__(self, mt5_client: MT5Client):
        self.mt5_client = mt5_client

    async def execute_order(self, order: OrderDTO) -> Dict[str, Any]:
        """
        Execute an order using MT5Client
        
        Args:
            order: OrderDTO object containing order details
            
        Returns:
            Dict containing execution result
        """
        try:
            if not self.mt5_client.is_connected():
                raise Exception("MT5 not connected")

            # Convert action to MT5 order type
            side = "buy" if order.action == Action.Mua else "sell"
            
            # Execute based on order type
            if order.order_type == OrderType.MARKET:
                result = await self.mt5_client.place_market_order(
                    symbol=order.symbol,
                    side=side,
                    volume=order.lot_size,
                    sl=order.stop_loss[0] if order.stop_loss else 0.0,
                    tp=order.take_profit[0] if order.take_profit else 0.0,
                    comment=order.comment or ""
                )
            else:
                # For limit/stop orders
                if not order.entry_price:
                    raise ValueError("Entry price required for limit/stop orders")
                
                # Determine pending order type
                if order.order_type == OrderType.LIMIT:
                    pending_type = f"{side}_limit"
                else:  # STOP or STOP_LIMIT
                    pending_type = f"{side}_stop"
                
                result = await self.mt5_client.place_pending_order(
                    symbol=order.symbol,
                    side=pending_type,
                    volume=order.lot_size,
                    price=order.entry_price,
                    sl=order.stop_loss[0] if order.stop_loss else 0.0,
                    tp=order.take_profit[0] if order.take_profit else 0.0,
                    comment=order.comment or ""
                )
            
            if result.success:
                order.status = Status.DaThucHien
                order.updated_at = datetime.now()
            else:
                order.status = Status.Cho
                order.error_message = result.error_message
                order.updated_at = datetime.now()

            return {
                "success": result.success,
                "order_id": result.order_id,
                "status": order.status,
                "error_message": result.error_message,
                "order": order.dict()
            }

        except Exception as e:
            logger.error(f"Error executing order: {e}")
            order.status = Status.Cho
            order.error_message = str(e)
            order.updated_at = datetime.now()
            
            return {
                "success": False,
                "error_message": str(e),
                "status": order.status,
                "order": order.dict()
            }

    async def cancel_order(self, order: OrderDTO) -> Dict[str, Any]:
        """
        Cancel an existing order
        
        Args:
            order: OrderDTO object containing order details
            
        Returns:
            Dict containing cancellation result
        """
        try:
            if not self.mt5_client.is_connected():
                raise Exception("MT5 not connected")

            # Get open orders
            orders = await self.mt5_client.fetch_open_orders(order.symbol)
            
            # Find matching order
            for mt5_order in orders:
                if (mt5_order.get('symbol') == order.symbol and 
                    mt5_order.get('magic') == (order.magic_number or 0)):
                    
                    # Cancel the order
                    result = await self.mt5_client.close_position(mt5_order['ticket'])
                    
                    if result.success:
                        order.status = Status.DaHuy
                        order.updated_at = datetime.now()
                        return {
                            "success": True,
                            "status": order.status,
                            "order": order.dict()
                        }
                    else:
                        return {
                            "success": False,
                            "error_message": result.error_message,
                            "status": order.status,
                            "order": order.dict()
                        }
            
            return {
                "success": False,
                "error_message": "Order not found",
                "status": order.status,
                "order": order.dict()
            }

        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "status": order.status,
                "order": order.dict()
            }

    async def get_order_status(self, order: OrderDTO) -> Dict[str, Any]:
        """
        Get current status of an order
        
        Args:
            order: OrderDTO object containing order details
            
        Returns:
            Dict containing order status
        """
        try:
            if not self.mt5_client.is_connected():
                raise Exception("MT5 not connected")

            # Check open orders
            orders = await self.mt5_client.fetch_open_orders(order.symbol)
            
            # Find matching order
            for mt5_order in orders:
                if (mt5_order.get('symbol') == order.symbol and 
                    mt5_order.get('magic') == (order.magic_number or 0)):
                    
                    # Update order status
                    order.updated_at = datetime.now()
                    return {
                        "success": True,
                        "status": order.status,
                        "order": order.dict(),
                        "mt5_order": mt5_order
                    }

            # Check positions if not found in open orders
            positions = await self.mt5_client.fetch_positions(order.symbol)
            for position in positions:
                if (position.get('symbol') == order.symbol and 
                    position.get('magic') == (order.magic_number or 0)):
                    
                    # Update order status to executed
                    order.status = Status.DaThucHien
                    order.updated_at = datetime.now()
                    return {
                        "success": True,
                        "status": order.status,
                        "order": order.dict(),
                        "position": position
                    }

            return {
                "success": True,
                "status": order.status,
                "order": order.dict(),
                "mt5_order": None
            }

        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "status": order.status,
                "order": order.dict()
            } 