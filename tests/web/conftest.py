"""
Test Configuration for Web Server Components
Provides fixtures and test utilities for FastAPI testing
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock
import redis.asyncio as redis
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.web.main import app
from src.web.services.redis_service import RedisService
from src.web.services.trading_service import TradingService
from src.web.services.order_matching import OrderMatchingService
from src.config.config_loader import ConfigLoader

# Test Configuration
TEST_CONFIG = {
    "redis": {
        "host": "localhost",
        "port": 6379,
        "password": None,
        "db": 1  # Use different DB for testing
    },
    "web_server": {
        "host": "127.0.0.1",
        "port": 8001,
        "ssl_certfile": None,
        "ssl_keyfile": None
    },
    "trading": {
        "sandbox_mode": True,
        "max_risk_per_trade": 0.01
    }
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """Provide test configuration"""
    return TEST_CONFIG

@pytest_asyncio.fixture
async def mock_redis():
    """Mock Redis client for testing"""
    mock_redis = AsyncMock(spec=redis.Redis)
    mock_redis.ping.return_value = True
    mock_redis.hset.return_value = 1
    mock_redis.hgetall.return_value = {}
    mock_redis.llen.return_value = 0
    mock_redis.lpush.return_value = 1
    mock_redis.lrange.return_value = []
    mock_redis.keys.return_value = []
    return mock_redis

@pytest_asyncio.fixture
async def redis_service(mock_redis):
    """Redis service with mocked client"""
    service = RedisService(mock_redis)
    return service

@pytest_asyncio.fixture
async def mock_trading_service():
    """Mock trading service for testing"""
    mock_service = AsyncMock(spec=TradingService)
    mock_service.initialized = True
    mock_service.get_current_price.return_value = 45000.0
    mock_service.execute_trade.return_value = {
        "success": True,
        "trade_id": "test_trade_123",
        "executed_price": 45000.0,
        "executed_quantity": 0.1
    }
    mock_service.validate_order.return_value = {"valid": True}
    return mock_service

@pytest_asyncio.fixture
async def order_matching_service(redis_service, mock_trading_service):
    """Order matching service with mocked dependencies"""
    service = OrderMatchingService(redis_service, mock_trading_service)
    return service

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client for FastAPI"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_tradingview_signal():
    """Sample TradingView webhook signal for testing"""
    return {
        "symbol": "BTCUSDT",
        "action": "buy",
        "price": 45000.0,
        "quantity": 0.1,
        "strategy": "test_strategy",
        "timeframe": "1h",
        "timestamp": "2023-12-01T12:00:00Z",
        "indicators": {
            "rsi": 65.5,
            "macd": 0.5
        }
    }

@pytest.fixture
def sample_order_request():
    """Sample order request for testing"""
    return {
        "user_id": "test_user_123",
        "symbol": "BTCUSDT",
        "side": "buy",
        "order_type": "limit",
        "quantity": 0.1,
        "price": 44000.0,
        "trigger_condition": "signal_match",
        "strategy_match": "test_strategy",
        "signal_source": "tradingview",
        "take_profit": 46000.0,
        "stop_loss": 43000.0,
        "notes": "Test order"
    }

@pytest.fixture
def sample_order_data():
    """Sample order data stored in Redis"""
    return {
        "order_id": "order_20231201_120000_123456",
        "user_id": "test_user_123",
        "symbol": "BTCUSDT",
        "side": "buy",
        "order_type": "limit",
        "quantity": "0.1",
        "price": "44000.0",
        "status": "pending",
        "created_at": "2023-12-01T12:00:00Z",
        "source": "web_frontend",
        "trigger_condition": "signal_match",
        "strategy_match": "test_strategy"
    }

@pytest.fixture
def sample_signal_data():
    """Sample signal data for testing"""
    return {
        "signal_id": "signal_20231201_120000_123456",
        "symbol": "BTCUSDT",
        "action": "buy",
        "price": 45000.0,
        "strategy": "test_strategy",
        "source": "tradingview",
        "received_at": "2023-12-01T12:00:00Z"
    }

# Test Data Generators
class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_order_data(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate order data with optional overrides"""
        base_data = {
            "user_id": "test_user",
            "symbol": "BTCUSDT",
            "side": "buy",
            "order_type": "market",
            "quantity": 0.1,
            "status": "pending"
        }
        if overrides:
            base_data.update(overrides)
        return base_data
    
    @staticmethod
    def generate_signal_data(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate signal data with optional overrides"""
        base_data = {
            "symbol": "BTCUSDT",
            "action": "buy",
            "price": 45000.0,
            "strategy": "test_strategy",
            "source": "tradingview"
        }
        if overrides:
            base_data.update(overrides)
        return base_data

# Test Utilities
class TestUtils:
    """Utility functions for testing"""
    
    @staticmethod
    def assert_order_response(response_data: Dict[str, Any], expected_status: str = None):
        """Assert order response has required fields"""
        assert "order_id" in response_data
        assert "status" in response_data
        assert "message" in response_data
        assert "timestamp" in response_data
        
        if expected_status:
            assert response_data["status"] == expected_status
    
    @staticmethod
    def assert_signal_response(response_data: Dict[str, Any]):
        """Assert signal response has required fields"""
        assert "status" in response_data
        assert "signal_id" in response_data
        assert "message" in response_data
        assert "timestamp" in response_data

# Global test fixtures
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Set test environment variables
    import os
    os.environ["ENVIRONMENT"] = "test"
    os.environ["REDIS_DB"] = "1"
    
    yield
    
    # Cleanup after tests
    pass

# Async test marker
pytest_plugins = ("pytest_asyncio",) 