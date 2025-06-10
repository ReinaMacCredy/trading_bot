"""
Tests for TradingView Webhook API
Tests webhook signal processing, validation, and error handling
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from fastapi import status

from tests.web.conftest import TestUtils

class TestTradingViewWebhook:
    """Test TradingView webhook endpoints"""
    
    def test_webhook_endpoint_exists(self, client):
        """Test that webhook endpoint exists and accepts POST"""
        response = client.post("/webhooks/tradingview", json={})
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != status.HTTP_404_NOT_FOUND
    
    @patch('src.web.api.webhooks.redis_service')
    @patch('src.web.api.webhooks.process_tradingview_signal')
    def test_valid_tradingview_signal(self, mock_process_signal, mock_redis_service, 
                                     client, sample_tradingview_signal):
        """Test processing valid TradingView signal"""
        # Mock Redis service
        mock_redis_service.store_tradingview_signal.return_value = "signal_123"
        
        response = client.post("/webhooks/tradingview", json=sample_tradingview_signal)
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        TestUtils.assert_signal_response(response_data)
        assert response_data["status"] == "received"
        assert "signal_id" in response_data
    
    def test_invalid_signal_missing_required_fields(self, client):
        """Test webhook with missing required fields"""
        invalid_signal = {
            "symbol": "BTCUSDT",
            # Missing action and price
        }
        
        response = client.post("/webhooks/tradingview", json=invalid_signal)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_invalid_signal_wrong_action(self, client, sample_tradingview_signal):
        """Test webhook with invalid action value"""
        sample_tradingview_signal["action"] = "invalid_action"
        
        response = client.post("/webhooks/tradingview", json=sample_tradingview_signal)
        
        # Should handle validation error gracefully
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]
    
    def test_invalid_signal_negative_price(self, client, sample_tradingview_signal):
        """Test webhook with negative price"""
        sample_tradingview_signal["price"] = -100.0
        
        response = client.post("/webhooks/tradingview", json=sample_tradingview_signal)
        
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]
    
    @patch('src.web.api.webhooks.redis_service', None)
    def test_webhook_redis_service_unavailable(self, client, sample_tradingview_signal):
        """Test webhook when Redis service is unavailable"""
        response = client.post("/webhooks/tradingview", json=sample_tradingview_signal)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        response_data = response.json()
        assert "error" in response_data["detail"]
    
    @patch('src.web.api.webhooks.redis_service')
    def test_webhook_redis_storage_error(self, mock_redis_service, client, sample_tradingview_signal):
        """Test webhook when Redis storage fails"""
        mock_redis_service.store_tradingview_signal.side_effect = Exception("Redis error")
        
        response = client.post("/webhooks/tradingview", json=sample_tradingview_signal)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_webhook_with_custom_indicators(self, client):
        """Test webhook with custom TradingView indicators"""
        signal_with_indicators = {
            "symbol": "ETHUSDT",
            "action": "sell",
            "price": 3000.0,
            "strategy": "custom_strategy",
            "indicators": {
                "rsi": 75.5,
                "macd": -0.2,
                "bollinger_upper": 3100.0,
                "bollinger_lower": 2900.0,
                "volume": 1000000
            },
            "alert_name": "ETH Sell Signal",
            "interval": "1h"
        }
        
        with patch('src.web.api.webhooks.redis_service') as mock_redis:
            mock_redis.store_tradingview_signal.return_value = "signal_456"
            
            response = client.post("/webhooks/tradingview", json=signal_with_indicators)
            
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["status"] == "received"
    
    def test_webhook_test_endpoint_get(self, client):
        """Test GET request to webhook test endpoint"""
        response = client.get("/webhooks/test")
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["status"] == "online"
        assert "timestamp" in response_data
    
    def test_webhook_test_endpoint_post(self, client):
        """Test POST request to webhook test endpoint"""
        test_data = {"test": "data", "timestamp": "2023-12-01T12:00:00Z"}
        
        response = client.post("/webhooks/test", json=test_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["status"] == "received"
        assert response_data["data"] == test_data
        assert "timestamp" in response_data

class TestSignalProcessing:
    """Test signal processing logic"""
    
    @pytest_asyncio.async_test
    async def test_process_tradingview_signal_success(self, sample_signal_data):
        """Test successful signal processing"""
        from src.web.api.webhooks import process_tradingview_signal
        
        with patch('src.web.api.webhooks.order_matching') as mock_matching:
            mock_matching.process_signal_matching = AsyncMock()
            
            # Should not raise exception
            await process_tradingview_signal(sample_signal_data, "signal_123")
            
            mock_matching.process_signal_matching.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_process_tradingview_signal_matching_unavailable(self, sample_signal_data):
        """Test signal processing when order matching is unavailable"""
        from src.web.api.webhooks import process_tradingview_signal
        
        with patch('src.web.api.webhooks.order_matching', None):
            # Should handle gracefully without raising exception
            await process_tradingview_signal(sample_signal_data, "signal_123")
    
    @pytest_asyncio.async_test
    async def test_process_tradingview_signal_matching_error(self, sample_signal_data):
        """Test signal processing when order matching fails"""
        from src.web.api.webhooks import process_tradingview_signal
        
        with patch('src.web.api.webhooks.order_matching') as mock_matching:
            mock_matching.process_signal_matching.side_effect = Exception("Matching error")
            
            # Should handle errors gracefully
            await process_tradingview_signal(sample_signal_data, "signal_123")

class TestWebhookSecurity:
    """Test webhook security features"""
    
    def test_webhook_signature_verification_disabled(self, client, sample_tradingview_signal):
        """Test webhook without signature verification (default)"""
        # Should work without any signature headers
        response = client.post("/webhooks/tradingview", json=sample_tradingview_signal)
        
        # Should not fail due to missing signature
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
    
    @patch('src.web.api.webhooks.verify_webhook_signature')
    def test_webhook_signature_verification_enabled(self, mock_verify, client, sample_tradingview_signal):
        """Test webhook with signature verification enabled"""
        mock_verify.return_value = True
        
        headers = {"X-TradingView-Signature": "valid_signature"}
        
        response = client.post("/webhooks/tradingview", 
                             json=sample_tradingview_signal, 
                             headers=headers)
        
        # Should process normally with valid signature
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
    
    @patch('src.web.api.webhooks.verify_webhook_signature')
    def test_webhook_invalid_signature(self, mock_verify, client, sample_tradingview_signal):
        """Test webhook with invalid signature"""
        mock_verify.return_value = False
        
        headers = {"X-TradingView-Signature": "invalid_signature"}
        
        response = client.post("/webhooks/tradingview", 
                             json=sample_tradingview_signal, 
                             headers=headers)
        
        # Should reject with invalid signature
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestWebhookValidation:
    """Test webhook input validation"""
    
    def test_webhook_empty_payload(self, client):
        """Test webhook with empty payload"""
        response = client.post("/webhooks/tradingview", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_webhook_malformed_json(self, client):
        """Test webhook with malformed JSON"""
        response = client.post("/webhooks/tradingview", 
                             data="invalid json", 
                             headers={"Content-Type": "application/json"})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_webhook_very_large_payload(self, client):
        """Test webhook with very large payload"""
        large_signal = {
            "symbol": "BTCUSDT",
            "action": "buy",
            "price": 45000.0,
            "large_data": "x" * 100000  # 100KB of data
        }
        
        response = client.post("/webhooks/tradingview", json=large_signal)
        
        # Should either process or reject gracefully (not crash)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ] 