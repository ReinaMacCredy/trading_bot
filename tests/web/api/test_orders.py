"""
Tests for Order Management API
Tests order creation, status tracking, cancellation, and user management
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from fastapi import status

from tests.web.conftest import TestUtils, TestDataGenerator

class TestOrderCreation:
    """Test order creation endpoints"""
    
    @patch('src.web.api.orders.redis_service')
    @patch('src.web.api.orders.process_new_order')
    def test_create_valid_order(self, mock_process, mock_redis_service, 
                               client, sample_order_request):
        """Test creating a valid order"""
        mock_redis_service.add_order.return_value = "order_123456"
        
        response = client.post("/orders/create", json=sample_order_request)
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        TestUtils.assert_order_response(response_data, "queued")
        assert "order_123456" in response_data["order_id"]
    
    def test_create_order_missing_required_fields(self, client):
        """Test creating order with missing required fields"""
        invalid_order = {
            "symbol": "BTCUSDT",
            "side": "buy"
            # Missing user_id, order_type, quantity
        }
        
        response = client.post("/orders/create", json=invalid_order)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_order_invalid_side(self, client, sample_order_request):
        """Test creating order with invalid side"""
        sample_order_request["side"] = "invalid_side"
        
        response = client.post("/orders/create", json=sample_order_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_order_invalid_order_type(self, client, sample_order_request):
        """Test creating order with invalid order type"""
        sample_order_request["order_type"] = "invalid_type"
        
        response = client.post("/orders/create", json=sample_order_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_limit_order_without_price(self, client, sample_order_request):
        """Test creating limit order without price"""
        sample_order_request["order_type"] = "limit"
        sample_order_request["price"] = None
        
        response = client.post("/orders/create", json=sample_order_request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Price required for limit orders" in response.json()["detail"]
    
    def test_create_stop_order_without_stop_price(self, client, sample_order_request):
        """Test creating stop order without stop price"""
        sample_order_request["order_type"] = "stop"
        sample_order_request["stop_price"] = None
        
        response = client.post("/orders/create", json=sample_order_request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Stop price required for stop orders" in response.json()["detail"]
    
    def test_create_order_negative_quantity(self, client, sample_order_request):
        """Test creating order with negative quantity"""
        sample_order_request["quantity"] = -0.1
        
        response = client.post("/orders/create", json=sample_order_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('src.web.api.orders.redis_service', None)
    def test_create_order_redis_unavailable(self, client, sample_order_request):
        """Test creating order when Redis is unavailable"""
        response = client.post("/orders/create", json=sample_order_request)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Redis service not available" in response.json()["detail"]

class TestOrderStatus:
    """Test order status endpoints"""
    
    @patch('src.web.api.orders.redis_service')
    def test_get_order_status_success(self, mock_redis_service, client, sample_order_data):
        """Test getting order status successfully"""
        mock_redis_service.get_order.return_value = sample_order_data
        
        response = client.get("/orders/status/order_123456")
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["order_id"] == sample_order_data["order_id"]
        assert response_data["symbol"] == sample_order_data["symbol"]
        assert response_data["status"] == sample_order_data["status"]
    
    @patch('src.web.api.orders.redis_service')
    def test_get_order_status_not_found(self, mock_redis_service, client):
        """Test getting status for non-existent order"""
        mock_redis_service.get_order.return_value = None
        
        response = client.get("/orders/status/nonexistent_order")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Order not found" in response.json()["detail"]
    
    @patch('src.web.api.orders.redis_service')
    def test_get_order_status_redis_error(self, mock_redis_service, client):
        """Test getting order status when Redis fails"""
        mock_redis_service.get_order.side_effect = Exception("Redis error")
        
        response = client.get("/orders/status/order_123456")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

class TestUserOrders:
    """Test user order management endpoints"""
    
    @patch('src.web.api.orders.redis_service')
    def test_get_user_orders_success(self, mock_redis_service, client):
        """Test getting user orders successfully"""
        user_orders = [
            TestDataGenerator.generate_order_data({"order_id": "order_1", "status": "executed"}),
            TestDataGenerator.generate_order_data({"order_id": "order_2", "status": "pending"})
        ]
        mock_redis_service.get_user_orders.return_value = user_orders
        
        response = client.get("/orders/user/test_user_123")
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["user_id"] == "test_user_123"
        assert len(response_data["orders"]) == 2
        assert response_data["total"] == 2
    
    @patch('src.web.api.orders.redis_service')
    def test_get_user_orders_with_status_filter(self, mock_redis_service, client):
        """Test getting user orders with status filter"""
        all_orders = [
            TestDataGenerator.generate_order_data({"order_id": "order_1", "status": "executed"}),
            TestDataGenerator.generate_order_data({"order_id": "order_2", "status": "pending"}),
            TestDataGenerator.generate_order_data({"order_id": "order_3", "status": "executed"})
        ]
        mock_redis_service.get_user_orders.return_value = all_orders
        
        response = client.get("/orders/user/test_user_123?status=executed")
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert len(response_data["orders"]) == 2  # Only executed orders
        for order in response_data["orders"]:
            assert order["status"] == "executed"
    
    @patch('src.web.api.orders.redis_service')
    def test_get_user_orders_with_limit(self, mock_redis_service, client):
        """Test getting user orders with limit parameter"""
        mock_redis_service.get_user_orders.return_value = []
        
        response = client.get("/orders/user/test_user_123?limit=25")
        
        assert response.status_code == status.HTTP_200_OK
        mock_redis_service.get_user_orders.assert_called_with("test_user_123", 25)
    
    def test_get_user_orders_invalid_limit(self, client):
        """Test getting user orders with invalid limit"""
        # Limit too high
        response = client.get("/orders/user/test_user_123?limit=300")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Limit too low
        response = client.get("/orders/user/test_user_123?limit=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

class TestOrderCancellation:
    """Test order cancellation endpoints"""
    
    @patch('src.web.api.orders.redis_service')
    def test_cancel_order_success(self, mock_redis_service, client):
        """Test successful order cancellation"""
        pending_order = TestDataGenerator.generate_order_data({"status": "pending"})
        mock_redis_service.get_order.return_value = pending_order
        mock_redis_service.update_order_status = AsyncMock()
        
        response = client.put("/orders/cancel/order_123456")
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["status"] == "cancelled"
        assert "order_123456" in response_data["order_id"]
    
    @patch('src.web.api.orders.redis_service')
    def test_cancel_order_not_found(self, mock_redis_service, client):
        """Test cancelling non-existent order"""
        mock_redis_service.get_order.return_value = None
        
        response = client.put("/orders/cancel/nonexistent_order")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Order not found" in response.json()["detail"]
    
    @patch('src.web.api.orders.redis_service')
    def test_cancel_order_already_executed(self, mock_redis_service, client):
        """Test cancelling already executed order"""
        executed_order = TestDataGenerator.generate_order_data({"status": "executed"})
        mock_redis_service.get_order.return_value = executed_order
        
        response = client.put("/orders/cancel/order_123456")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Order cannot be cancelled" in response.json()["detail"]
    
    @patch('src.web.api.orders.redis_service')
    def test_cancel_order_already_cancelled(self, mock_redis_service, client):
        """Test cancelling already cancelled order"""
        cancelled_order = TestDataGenerator.generate_order_data({"status": "cancelled"})
        mock_redis_service.get_order.return_value = cancelled_order
        
        response = client.put("/orders/cancel/order_123456")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Order cannot be cancelled" in response.json()["detail"]

class TestQueueStatistics:
    """Test queue statistics endpoints"""
    
    @patch('src.web.api.orders.redis_service')
    def test_get_queue_stats_success(self, mock_redis_service, client):
        """Test getting queue statistics successfully"""
        mock_stats = {
            "pending_orders": 15,
            "matched_orders": 5,
            "executed_orders": 100,
            "failed_orders": 3,
            "timestamp": "2023-12-01T12:00:00Z"
        }
        mock_redis_service.get_queue_stats.return_value = mock_stats
        
        response = client.get("/orders/queue/stats")
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["pending_orders"] == 15
        assert response_data["matched_orders"] == 5
        assert response_data["executed_orders"] == 100
        assert response_data["failed_orders"] == 3
        assert "timestamp" in response_data
    
    @patch('src.web.api.orders.redis_service', None)
    def test_get_queue_stats_redis_unavailable(self, client):
        """Test getting queue stats when Redis is unavailable"""
        response = client.get("/orders/queue/stats")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

class TestOrderProcessing:
    """Test order processing logic"""
    
    @pytest_asyncio.async_test
    async def test_process_new_order_market_order(self, sample_order_request):
        """Test processing new market order"""
        from src.web.api.orders import process_new_order
        
        sample_order_request["order_type"] = "market"
        
        with patch('src.web.api.orders.order_matching') as mock_matching:
            mock_matching.execute_market_order = AsyncMock()
            
            await process_new_order(sample_order_request, "order_123")
            
            mock_matching.execute_market_order.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_process_new_order_limit_order(self, sample_order_request):
        """Test processing new limit order"""
        from src.web.api.orders import process_new_order
        
        sample_order_request["order_type"] = "limit"
        
        with patch('src.web.api.orders.order_matching') as mock_matching:
            mock_matching.add_to_matching_queue = AsyncMock()
            
            await process_new_order(sample_order_request, "order_123")
            
            mock_matching.add_to_matching_queue.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_process_new_order_matching_unavailable(self, sample_order_request):
        """Test processing new order when order matching is unavailable"""
        from src.web.api.orders import process_new_order
        
        with patch('src.web.api.orders.order_matching', None):
            # Should handle gracefully without raising exception
            await process_new_order(sample_order_request, "order_123")
    
    @pytest_asyncio.async_test
    async def test_process_new_order_error_handling(self, sample_order_request):
        """Test processing new order with error"""
        from src.web.api.orders import process_new_order
        
        with patch('src.web.api.orders.order_matching') as mock_matching:
            mock_matching.execute_market_order.side_effect = Exception("Processing error")
            
            with patch('src.web.api.orders.redis_service') as mock_redis:
                mock_redis.update_order_status = AsyncMock()
                
                await process_new_order(sample_order_request, "order_123")
                
                # Should update order status to failed
                mock_redis.update_order_status.assert_called_with(
                    "order_123",
                    "failed",
                    error_message="Processing error"
                )

class TestOrderValidation:
    """Test order validation logic"""
    
    def test_create_order_with_take_profit_and_stop_loss(self, client, sample_order_request):
        """Test creating order with take profit and stop loss"""
        sample_order_request.update({
            "take_profit": 46000.0,
            "stop_loss": 43000.0
        })
        
        with patch('src.web.api.orders.redis_service') as mock_redis:
            mock_redis.add_order.return_value = "order_123"
            
            response = client.post("/orders/create", json=sample_order_request)
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_create_order_with_complex_conditions(self, client, sample_order_request):
        """Test creating order with complex trigger conditions"""
        sample_order_request.update({
            "trigger_condition": "signal_match",
            "strategy_match": "MACD_RSI",
            "signal_source": "tradingview",
            "notes": "Complex conditional order",
            "tags": ["automation", "strategy_based"]
        })
        
        with patch('src.web.api.orders.redis_service') as mock_redis:
            mock_redis.add_order.return_value = "order_123"
            
            response = client.post("/orders/create", json=sample_order_request)
            
            assert response.status_code == status.HTTP_200_OK 