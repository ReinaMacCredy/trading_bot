"""
Redis Service for Order Queue Management
Handles order queuing, matching, and status tracking
"""
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for order management"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
        # Queue names
        self.PENDING_ORDERS = "orders:pending"
        self.MATCHED_ORDERS = "orders:matched" 
        self.EXECUTED_ORDERS = "orders:executed"
        self.FAILED_ORDERS = "orders:failed"
        
        # Key prefixes
        self.ORDER_PREFIX = "order:"
        self.USER_ORDERS_PREFIX = "user:orders:"
        self.SIGNAL_PREFIX = "signal:"
        
    async def test_connection(self) -> bool:
        """Test Redis connection"""
        try:
            await self.redis.ping()
            logger.info("✅ Redis connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        await self.redis.aclose()
    
    # Order Management
    async def add_order(self, order_data: Dict[str, Any]) -> str:
        """Add order to pending queue"""
        order_id = f"order_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        order_data["order_id"] = order_id
        order_data["created_at"] = datetime.now().isoformat()
        order_data["status"] = "pending"
        
        # Store order data
        await self.redis.hset(
            f"{self.ORDER_PREFIX}{order_id}",
            mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                    for k, v in order_data.items()}
        )
        
        # Add to pending queue
        await self.redis.lpush(self.PENDING_ORDERS, order_id)
        
        # Add to user's order list
        user_id = order_data.get("user_id", "unknown")
        await self.redis.lpush(f"{self.USER_ORDERS_PREFIX}{user_id}", order_id)
        
        logger.info(f"📝 Added order {order_id} to pending queue")
        return order_id
    
    async def get_pending_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending orders for matching"""
        order_ids = await self.redis.lrange(self.PENDING_ORDERS, 0, limit - 1)
        orders = []
        
        for order_id in order_ids:
            order_data = await self.get_order(order_id)
            if order_data:
                orders.append(order_data)
        
        return orders
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order data by ID"""
        try:
            data = await self.redis.hgetall(f"{self.ORDER_PREFIX}{order_id}")
            if not data:
                return None
            
            # Parse JSON fields
            parsed_data = {}
            for key, value in data.items():
                try:
                    parsed_data[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_data[key] = value
            
            return parsed_data
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    async def update_order_status(self, order_id: str, status: str, **updates):
        """Update order status and additional fields"""
        updates["status"] = status
        updates["updated_at"] = datetime.now().isoformat()
        
        # Update order data
        await self.redis.hset(
            f"{self.ORDER_PREFIX}{order_id}",
            mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                    for k, v in updates.items()}
        )
        
        # Move to appropriate queue
        if status == "matched":
            await self.redis.lrem(self.PENDING_ORDERS, 1, order_id)
            await self.redis.lpush(self.MATCHED_ORDERS, order_id)
        elif status == "executed":
            await self.redis.lrem(self.MATCHED_ORDERS, 1, order_id)
            await self.redis.lpush(self.EXECUTED_ORDERS, order_id)
        elif status == "failed":
            await self.redis.lrem(self.PENDING_ORDERS, 1, order_id)
            await self.redis.lrem(self.MATCHED_ORDERS, 1, order_id)
            await self.redis.lpush(self.FAILED_ORDERS, order_id)
        
        logger.info(f"📋 Updated order {order_id} status to {status}")
    
    async def get_user_orders(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's orders"""
        order_ids = await self.redis.lrange(f"{self.USER_ORDERS_PREFIX}{user_id}", 0, limit - 1)
        orders = []
        
        for order_id in order_ids:
            order_data = await self.get_order(order_id)
            if order_data:
                orders.append(order_data)
        
        return orders
    
    # Signal Management
    async def store_tradingview_signal(self, signal_data: Dict[str, Any]) -> str:
        """Store TradingView webhook signal"""
        signal_id = f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        signal_data["signal_id"] = signal_id
        signal_data["received_at"] = datetime.now().isoformat()
        
        # Store signal
        await self.redis.hset(
            f"{self.SIGNAL_PREFIX}{signal_id}",
            mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                    for k, v in signal_data.items()}
        )
        
        # Set expiration (signals expire after 24 hours)
        await self.redis.expire(f"{self.SIGNAL_PREFIX}{signal_id}", 86400)
        
        logger.info(f"📡 Stored TradingView signal {signal_id}")
        return signal_id
    
    async def get_recent_signals(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent TradingView signals"""
        # This is a simplified implementation
        # In production, you might want to use a sorted set for better signal management
        signal_keys = await self.redis.keys(f"{self.SIGNAL_PREFIX}*")
        signals = []
        
        for key in signal_keys[-limit:]:
            signal_data = await self.redis.hgetall(key)
            if signal_data:
                parsed_signal = {}
                for k, v in signal_data.items():
                    try:
                        parsed_signal[k] = json.loads(v)
                    except (json.JSONDecodeError, TypeError):
                        parsed_signal[k] = v
                signals.append(parsed_signal)
        
        return sorted(signals, key=lambda x: x.get("received_at", ""), reverse=True)
    
    # Order Matching Support
    async def find_matching_orders(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find orders matching specific criteria"""
        pending_orders = await self.get_pending_orders(limit=100)
        matching_orders = []
        
        for order in pending_orders:
            if self._order_matches_criteria(order, criteria):
                matching_orders.append(order)
        
        return matching_orders
    
    def _order_matches_criteria(self, order: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if order matches criteria"""
        # Symbol matching
        if criteria.get("symbol") and order.get("symbol") != criteria["symbol"]:
            return False
        
        # Side matching (buy/sell)
        if criteria.get("side") and order.get("side") != criteria["side"]:
            return False
        
        # Price range matching
        if criteria.get("price_min") and float(order.get("price", 0)) < criteria["price_min"]:
            return False
        
        if criteria.get("price_max") and float(order.get("price", 0)) > criteria["price_max"]:
            return False
        
        return True
    
    # Statistics and Monitoring
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "pending_orders": await self.redis.llen(self.PENDING_ORDERS),
            "matched_orders": await self.redis.llen(self.MATCHED_ORDERS), 
            "executed_orders": await self.redis.llen(self.EXECUTED_ORDERS),
            "failed_orders": await self.redis.llen(self.FAILED_ORDERS),
            "timestamp": datetime.now().isoformat()
        } 