from typing import Dict, List, Optional
import logging
from datetime import datetime
from src.web.models.order_dto import OrderDTO, Action, OrderType
from src.architecture.event_broker import Signal, EventBroker
from src.trading.clients.mt5_client import MT5Client

logger = logging.getLogger(__name__)

class SignalProcessor:
    """Processes trading signals and matches them with OrderDTOs"""
    
    def __init__(self, event_broker: EventBroker, mt5_client: MT5Client):
        self.event_broker = event_broker
        self.mt5_client = mt5_client
        self.pending_orders: Dict[str, List[OrderDTO]] = {}  # symbol -> list of orders
        self.required_timeframes = ["1h", "4h", "15m", "1d"]  # Example timeframes
        
    async def register_tradingview_signal(self, symbol: str, timeframe: str, action: str, data: Dict):
        """Register a signal from TradingView"""
        signal = Signal(
            source=f"tradingview_{timeframe}",
            action=action,
            timestamp=datetime.now(),
            data=data,
            timeframe=timeframe
        )
        
        await self.event_broker.emit_signal(f"tradingview_{timeframe}", signal)
        
    async def check_price_condition(self, symbol: str, order: OrderDTO) -> bool:
        """Check if current price is within the order's price range"""
        try:
            current_price = await self.mt5_client.get_current_price(symbol)
            if not current_price:
                return False
                
            # For market orders, just check if price is within range
            if order.order_type == OrderType.MARKET:
                return True
                
            # For limit/stop orders, check if price is within range
            if order.entry_price:
                # Add some tolerance (e.g., 0.1%)
                tolerance = current_price * 0.001
                return abs(current_price - order.entry_price) <= tolerance
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking price condition: {e}")
            return False
            
    async def process_signals(self, symbol: str):
        """Process signals for a symbol"""
        try:
            # Wait for signals from all required timeframes
            signals = await self.event_broker.wait_for_signals(
                [f"tradingview_{tf}" for tf in self.required_timeframes]
            )
            
            if not signals:
                logger.warning(f"No signals received for {symbol}")
                return
                
            # Check if all signals agree on action
            actions = [signal.action for signal in signals.values()]
            if not all(action == actions[0] for action in actions):
                logger.info(f"Conflicting signals for {symbol}: {actions}")
                return
                
            # Get matching orders
            matching_orders = self._find_matching_orders(symbol, actions[0])
            if not matching_orders:
                logger.info(f"No matching orders found for {symbol}")
                return
                
            # Check price conditions for each order
            for order in matching_orders:
                if await self.check_price_condition(symbol, order):
                    # Emit execution signal
                    execution_signal = Signal(
                        source="signal_processor",
                        action=actions[0],
                        timestamp=datetime.now(),
                        data={"order": order.dict()}
                    )
                    await self.event_broker.emit_signal("execution", execution_signal)
                    
        except Exception as e:
            logger.error(f"Error processing signals: {e}")
            
    def _find_matching_orders(self, symbol: str, action: str) -> List[OrderDTO]:
        """Find orders matching the signal action"""
        if symbol not in self.pending_orders:
            return []
            
        matching_orders = []
        for order in self.pending_orders[symbol]:
            if (order.action == Action.Mua and action == "buy") or \
               (order.action == Action.Ban and action == "sell"):
                matching_orders.append(order)
                
        return matching_orders
        
    def add_pending_order(self, order: OrderDTO):
        """Add a new pending order"""
        if order.symbol not in self.pending_orders:
            self.pending_orders[order.symbol] = []
        self.pending_orders[order.symbol].append(order)
        
    def remove_pending_order(self, order: OrderDTO):
        """Remove a pending order"""
        if order.symbol in self.pending_orders:
            self.pending_orders[order.symbol] = [
                o for o in self.pending_orders[order.symbol]
                if o != order
            ] 