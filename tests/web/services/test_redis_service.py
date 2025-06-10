"""
Unit Tests for Redis Service
Tests order queuing, signal storage, and queue management functionality
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime
import json

from tests.web.conftest import TestDataGenerator, TestUtils

class TestRedisService:
    """Test cases for RedisService"""
    
    @pytest_asyncio.async_test
    async def test_connection_test_success(self, redis_service, mock_redis):
        """Test successful Redis connection"""
        mock_redis.ping.return_value = True
        
        result = await redis_service.test_connection()
        
        assert result is True
        mock_redis.ping.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_add_order_success(self, redis_service, mock_redis, sample_order_request):
        """Test successful order addition"""
        mock_redis.hset.return_value = 1
        mock_redis.lpush.return_value = 1
        
        order_id = await redis_service.add_order(sample_order_request)
        
        # Verify order ID format
        assert order_id.startswith("order_")
        assert len(order_id) > 10
        
        # Verify Redis calls
        mock_redis.hset.assert_called()
        assert mock_redis.lpush.call_count == 2  # pending queue + user queue
    
    @pytest_asyncio.async_test
    async def test_get_order_success(self, redis_service, mock_redis, sample_order_data):
        """Test successful order retrieval"""
        # Mock Redis response
        redis_data = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                     for k, v in sample_order_data.items()}
        mock_redis.hgetall.return_value = redis_data
        
        order = await redis_service.get_order("test_order_id")
        
        assert order is not None
        assert order["order_id"] == sample_order_data["order_id"]
        assert order["symbol"] == sample_order_data["symbol"]
        mock_redis.hgetall.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_store_tradingview_signal(self, redis_service, mock_redis, sample_tradingview_signal):
        """Test storing TradingView signal"""
        mock_redis.hset.return_value = 1
        mock_redis.expire.return_value = True
        
        signal_id = await redis_service.store_tradingview_signal(sample_tradingview_signal)
        
        # Verify signal ID format
        assert signal_id.startswith("signal_")
        assert len(signal_id) > 10
        
        # Verify Redis calls
        mock_redis.hset.assert_called()
        mock_redis.expire.assert_called_with(f"signal:{signal_id}", 86400)
    
    @pytest_asyncio.async_test
    async def test_get_queue_stats(self, redis_service, mock_redis):
        """Test getting queue statistics"""
        # Mock queue lengths
        mock_redis.llen.side_effect = [5, 3, 10, 2]  # pending, matched, executed, failed
        
        stats = await redis_service.get_queue_stats()
        
        assert stats["pending_orders"] == 5
        assert stats["matched_orders"] == 3
        assert stats["executed_orders"] == 10
        assert stats["failed_orders"] == 2
        assert "timestamp" in stats 