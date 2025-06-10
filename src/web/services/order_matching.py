"""
Order Matching Service
Matches orders against TradingView signals and market conditions
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .redis_service import RedisService
from .trading_service import TradingService

logger = logging.getLogger(__name__)

class OrderMatchingService:
    """Handles order matching and execution logic"""
    
    def __init__(self, redis_service: RedisService, trading_service: TradingService):
        self.redis = redis_service
        self.trading = trading_service
        self.matching_loop_running = False
    
    async def start_matching_loop(self):
        """Start the background order matching loop"""
        if self.matching_loop_running:
            logger.warning("Order matching loop already running")
            return
        
        self.matching_loop_running = True
        logger.info("🔄 Starting order matching loop")
        
        while self.matching_loop_running:
            try:
                await self.process_pending_orders()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"❌ Error in matching loop: {e}")
                await asyncio.sleep(5)  # Wait longer on errors
    
    def stop_matching_loop(self):
        """Stop the order matching loop"""
        self.matching_loop_running = False
        logger.info("🛑 Stopping order matching loop")
    
    async def process_pending_orders(self):
        """Process pending orders for matching and execution"""
        try:
            pending_orders = await self.redis.get_pending_orders(limit=50)
            
            for order in pending_orders:
                await self.evaluate_order_for_execution(order)
                
        except Exception as e:
            logger.error(f"❌ Error processing pending orders: {e}")
    
    async def evaluate_order_for_execution(self, order: Dict[str, Any]):
        """Evaluate if an order should be executed"""
        try:
            order_id = order["order_id"]
            
            # Check market conditions
            if await self.should_execute_order(order):
                logger.info(f"📈 Order {order_id} meets execution criteria")
                await self.execute_order(order)
            
        except Exception as e:
            logger.error(f"❌ Error evaluating order {order.get('order_id', 'unknown')}: {e}")
    
    async def should_execute_order(self, order: Dict[str, Any]) -> bool:
        """Determine if order should be executed based on conditions"""
        try:
            order_type = order.get("order_type", "").lower()
            symbol = order.get("symbol", "")
            
            # Market orders execute immediately
            if order_type == "market":
                return True
            
            # Get current market price
            current_price = await self.trading.get_current_price(symbol)
            if not current_price:
                logger.warning(f"Could not get price for {symbol}")
                return False
            
            # Limit order execution
            if order_type == "limit":
                target_price = float(order.get("price", 0))
                side = order.get("side", "").lower()
                
                if side == "buy" and current_price <= target_price:
                    return True
                elif side == "sell" and current_price >= target_price:
                    return True
            
            # Stop order execution
            elif order_type == "stop":
                stop_price = float(order.get("stop_price", 0))
                side = order.get("side", "").lower()
                
                if side == "buy" and current_price >= stop_price:
                    return True
                elif side == "sell" and current_price <= stop_price:
                    return True
            
            # Check signal-based conditions
            if order.get("trigger_condition"):
                return await self.check_signal_conditions(order)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking execution conditions: {e}")
            return False
    
    async def check_signal_conditions(self, order: Dict[str, Any]) -> bool:
        """Check if order meets signal-based trigger conditions"""
        try:
            # Get recent signals
            recent_signals = await self.redis.get_recent_signals(limit=10)
            
            required_strategy = order.get("strategy_match")
            required_source = order.get("signal_source")
            symbol = order.get("symbol")
            
            for signal in recent_signals:
                # Check symbol match
                if signal.get("symbol") != symbol:
                    continue
                
                # Check strategy match
                if required_strategy and signal.get("strategy") != required_strategy:
                    continue
                
                # Check source match
                if required_source and signal.get("source") != required_source:
                    continue
                
                # Check signal direction matches order side
                signal_action = signal.get("action", "").lower()
                order_side = order.get("side", "").lower()
                
                if (signal_action in ["buy", "long"] and order_side == "buy") or \
                   (signal_action in ["sell", "short"] and order_side == "sell"):
                    logger.info(f"📡 Signal condition met for order {order['order_id']}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking signal conditions: {e}")
            return False
    
    async def execute_order(self, order: Dict[str, Any]):
        """Execute a matched order"""
        try:
            order_id = order["order_id"]
            symbol = order["symbol"]
            side = order["side"]
            quantity = float(order["quantity"])
            
            logger.info(f"⚡ Executing order {order_id}: {symbol} {side} {quantity}")
            
            # Update status to matched
            await self.redis.update_order_status(order_id, "matched")
            
            # Execute trade
            execution_result = await self.trading.execute_trade(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=order.get("order_type", "market"),
                price=order.get("price"),
                stop_price=order.get("stop_price")
            )
            
            if execution_result["success"]:
                # Update order with execution details
                await self.redis.update_order_status(
                    order_id,
                    "executed",
                    executed_price=execution_result.get("executed_price"),
                    executed_quantity=execution_result.get("executed_quantity"),
                    trade_id=execution_result.get("trade_id"),
                    execution_time=datetime.now().isoformat()
                )
                
                logger.info(f"✅ Order {order_id} executed successfully")
                
                # Handle take profit and stop loss
                if order.get("take_profit") or order.get("stop_loss"):
                    await self.create_exit_orders(order, execution_result)
                
            else:
                # Mark as failed
                await self.redis.update_order_status(
                    order_id,
                    "failed",
                    error_message=execution_result.get("error", "Execution failed")
                )
                
                logger.error(f"❌ Order {order_id} execution failed: {execution_result.get('error')}")
            
        except Exception as e:
            logger.error(f"❌ Error executing order {order.get('order_id', 'unknown')}: {e}")
            await self.redis.update_order_status(
                order["order_id"],
                "failed",
                error_message=str(e)
            )
    
    async def create_exit_orders(self, original_order: Dict[str, Any], execution_result: Dict[str, Any]):
        """Create take profit and stop loss orders"""
        try:
            symbol = original_order["symbol"]
            quantity = execution_result.get("executed_quantity", original_order["quantity"])
            
            # Reverse side for exit orders
            exit_side = "sell" if original_order["side"] == "buy" else "buy"
            
            # Create take profit order
            if original_order.get("take_profit"):
                tp_order = {
                    "user_id": original_order["user_id"],
                    "symbol": symbol,
                    "side": exit_side,
                    "order_type": "limit",
                    "quantity": quantity,
                    "price": original_order["take_profit"],
                    "parent_order_id": original_order["order_id"],
                    "order_category": "take_profit",
                    "source": "auto_exit"
                }
                await self.redis.add_order(tp_order)
                logger.info(f"📈 Created take profit order for {original_order['order_id']}")
            
            # Create stop loss order
            if original_order.get("stop_loss"):
                sl_order = {
                    "user_id": original_order["user_id"],
                    "symbol": symbol,
                    "side": exit_side,
                    "order_type": "stop",
                    "quantity": quantity,
                    "stop_price": original_order["stop_loss"],
                    "parent_order_id": original_order["order_id"],
                    "order_category": "stop_loss",
                    "source": "auto_exit"
                }
                await self.redis.add_order(sl_order)
                logger.info(f"🛑 Created stop loss order for {original_order['order_id']}")
                
        except Exception as e:
            logger.error(f"❌ Error creating exit orders: {e}")
    
    async def process_signal_matching(self, signal_data: Dict[str, Any], criteria: Dict[str, Any]):
        """Process signal for order matching"""
        try:
            logger.info(f"🔍 Processing signal matching for {signal_data.get('symbol')}")
            
            # Find orders that match this signal
            matching_orders = await self.redis.find_matching_orders(criteria)
            
            for order in matching_orders:
                if await self.signal_matches_order(signal_data, order):
                    logger.info(f"🎯 Signal matches order {order['order_id']}")
                    await self.execute_order(order)
            
        except Exception as e:
            logger.error(f"❌ Error processing signal matching: {e}")
    
    async def signal_matches_order(self, signal: Dict[str, Any], order: Dict[str, Any]) -> bool:
        """Check if signal matches order requirements"""
        try:
            # Symbol must match
            if signal.get("symbol") != order.get("symbol"):
                return False
            
            # Check signal direction matches order side
            signal_action = signal.get("action", "").lower()
            order_side = order.get("side", "").lower()
            
            if signal_action in ["buy", "long"] and order_side != "buy":
                return False
            if signal_action in ["sell", "short"] and order_side != "sell":
                return False
            
            # Check strategy match if required
            if order.get("strategy_match") and signal.get("strategy") != order.get("strategy_match"):
                return False
            
            # Check source match if required
            if order.get("signal_source") and signal.get("source") != order.get("signal_source"):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking signal match: {e}")
            return False
    
    async def execute_market_order(self, order_data: Dict[str, Any]):
        """Execute market order immediately"""
        try:
            logger.info(f"⚡ Executing market order immediately: {order_data['order_id']}")
            await self.execute_order(order_data)
        except Exception as e:
            logger.error(f"❌ Error executing market order: {e}")
    
    async def add_to_matching_queue(self, order_data: Dict[str, Any]):
        """Add order to matching queue for conditional execution"""
        try:
            logger.info(f"📋 Order {order_data['order_id']} added to matching queue")
            # Order is already in Redis pending queue, just log
        except Exception as e:
            logger.error(f"❌ Error adding to matching queue: {e}") 