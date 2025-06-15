import logging
from typing import Dict, Optional
from datetime import datetime
from src.web.architecture.event_broker import Signal, EventBroker
from src.trading.services.order_executor import OrderExecutor
from src.web.api.models import Order
from src.trading.clients.mt5_client import MT5Client

logger = logging.getLogger(__name__)

class TradeExecutor:
    """Executes trades based on signals and manages positions"""
    
    def __init__(self, event_broker: EventBroker, mt5_client: MT5Client):
        self.event_broker = event_broker
        self.mt5_client = mt5_client
        self.order_executor = OrderExecutor(mt5_client)
        self.active_positions: Dict[str, Dict] = {}  # symbol -> position info
        
    async def start(self):
        """Start listening for execution signals"""
        self.event_broker.register_consumer("execution", self._handle_execution_signal)
        
    async def _handle_execution_signal(self, signal: Signal):
        """Handle execution signals"""
        try:
            if signal.source != "signal_processor":
                return
                
            order_data = signal.data.get("order")
            if not order_data:
                logger.error("No order data in execution signal")
                return
                
            # Convert order data to OrderDTO
            order = OrderDTO(**order_data)
            
            # Execute the order
            result = await self.order_executor.execute_order(order)
            
            if result["success"]:
                # Update active positions
                self.active_positions[order.symbol] = {
                    "order": order,
                    "entry_time": datetime.now(),
                    "status": "open"
                }
                
                # Emit position update signal
                position_signal = Signal(
                    source="trade_executor",
                    action=signal.action,
                    timestamp=datetime.now(),
                    data={
                        "symbol": order.symbol,
                        "position": self.active_positions[order.symbol]
                    }
                )
                await self.event_broker.emit_signal("position_update", position_signal)
                
            else:
                logger.error(f"Order execution failed: {result['error_message']}")
                
        except Exception as e:
            logger.error(f"Error handling execution signal: {e}")
            
    async def update_position(self, symbol: str, take_profit: Optional[float] = None, stop_loss: Optional[float] = None):
        """Update take profit or stop loss for an active position"""
        try:
            if symbol not in self.active_positions:
                logger.warning(f"No active position for {symbol}")
                return
                
            position = self.active_positions[symbol]
            order = position["order"]
            
            # Update order with new levels
            if take_profit is not None:
                order.take_profit = [take_profit]
            if stop_loss is not None:
                order.stop_loss = [stop_loss]
                
            # Update position in MT5
            result = await self.order_executor.modify_position(
                symbol=symbol,
                take_profit=take_profit,
                stop_loss=stop_loss
            )
            
            if result["success"]:
                # Update local position info
                position["order"] = order
                position["updated_at"] = datetime.now()
                
                # Emit position update signal
                position_signal = Signal(
                    source="trade_executor",
                    action="modify",
                    timestamp=datetime.now(),
                    data={
                        "symbol": symbol,
                        "position": position
                    }
                )
                await self.event_broker.emit_signal("position_update", position_signal)
                
            else:
                logger.error(f"Position update failed: {result['error_message']}")
                
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            
    async def close_position(self, symbol: str):
        """Close an active position"""
        try:
            if symbol not in self.active_positions:
                logger.warning(f"No active position for {symbol}")
                return
                
            position = self.active_positions[symbol]
            order = position["order"]
            
            # Close position in MT5
            result = await self.order_executor.cancel_order(order)
            
            if result["success"]:
                # Remove from active positions
                del self.active_positions[symbol]
                
                # Emit position close signal
                close_signal = Signal(
                    source="trade_executor",
                    action="close",
                    timestamp=datetime.now(),
                    data={
                        "symbol": symbol,
                        "position": position
                    }
                )
                await self.event_broker.emit_signal("position_close", close_signal)
                
            else:
                logger.error(f"Position close failed: {result['error_message']}")
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            
    def get_active_positions(self) -> Dict[str, Dict]:
        """Get all active positions"""
        return self.active_positions 