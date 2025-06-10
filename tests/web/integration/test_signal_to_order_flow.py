"""
Integration Tests for Signal-to-Order Flow
Tests complete workflow from TradingView webhook to order execution
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from fastapi import status

from tests.web.conftest import TestDataGenerator

class TestSignalToOrderIntegration:
    """Integration tests for signal processing and order matching"""
    
    @pytest_asyncio.async_test
    async def test_complete_signal_to_execution_flow(self, redis_service, mock_trading_service, 
                                                   order_matching_service, client):
        """Test complete flow from signal to order execution"""
        
        # Step 1: Create a pending order that matches the incoming signal
        order_data = TestDataGenerator.generate_order_data({
            "user_id": "test_user",
            "symbol": "BTCUSDT",
            "side": "buy",
            "order_type": "limit",
            "quantity": 0.1,
            "price": 44000.0,
            "trigger_condition": "signal_match",
            "strategy_match": "test_strategy",
            "signal_source": "tradingview"
        })
        
        order_id = await redis_service.add_order(order_data)
        
        # Step 2: Send TradingView signal that should match the order
        signal_data = {
            "symbol": "BTCUSDT",
            "action": "buy",
            "price": 45000.0,
            "strategy": "test_strategy",
            "timeframe": "1h"
        }
        
        # Mock the trading service to return successful execution
        mock_trading_service.execute_trade.return_value = {
            "success": True,
            "trade_id": "trade_123",
            "executed_price": 45000.0,
            "executed_quantity": 0.1
        }
        
        # Step 3: Process the signal (this would normally be triggered by webhook)
        signal_id = await redis_service.store_tradingview_signal(signal_data)
        
        # Step 4: Trigger order matching
        matching_criteria = {
            "symbol": "BTCUSDT",
            "signal_action": "buy",
            "strategy": "test_strategy"
        }
        
        await order_matching_service.process_signal_matching(signal_data, matching_criteria)
        
        # Step 5: Verify order was executed
        updated_order = await redis_service.get_order(order_id)
        assert updated_order["status"] == "executed"
        assert updated_order["executed_price"] == 45000.0
        
        # Verify trading service was called
        mock_trading_service.execute_trade.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_webhook_to_order_matching_integration(self, client, redis_service, 
                                                       mock_trading_service):
        """Test integration from webhook receipt to order matching"""
        
        # Create pending order first
        order_data = TestDataGenerator.generate_order_data({
            "symbol": "ETHUSDT",
            "side": "sell",
            "order_type": "market",
            "quantity": 1.0,
            "signal_source": "tradingview"
        })
        
        await redis_service.add_order(order_data)
        
        # Send webhook signal
        webhook_payload = {
            "symbol": "ETHUSDT",
            "action": "sell",
            "price": 3000.0,
            "strategy": "momentum",
            "timeframe": "15m"
        }
        
        with patch('src.web.api.webhooks.redis_service', redis_service):
            with patch('src.web.main.order_matching') as mock_matching:
                mock_matching.process_signal_matching = AsyncMock()
                
                response = client.post("/webhooks/tradingview", json=webhook_payload)
                
                assert response.status_code == status.HTTP_200_OK
                
                # Give time for background processing
                await asyncio.sleep(0.1)
                
                # Verify signal was stored
                recent_signals = await redis_service.get_recent_signals(limit=5)
                assert len(recent_signals) > 0
                assert any(s["symbol"] == "ETHUSDT" for s in recent_signals)
    
    @pytest_asyncio.async_test
    async def test_multiple_orders_single_signal(self, redis_service, mock_trading_service,
                                               order_matching_service):
        """Test single signal matching multiple orders"""
        
        # Create multiple matching orders
        order_ids = []
        for i in range(3):
            order_data = TestDataGenerator.generate_order_data({
                "user_id": f"user_{i}",
                "symbol": "BTCUSDT",
                "side": "buy",
                "order_type": "market",
                "quantity": 0.1 * (i + 1),
                "signal_source": "tradingview"
            })
            order_id = await redis_service.add_order(order_data)
            order_ids.append(order_id)
        
        # Send signal that matches all orders
        signal_data = {
            "symbol": "BTCUSDT",
            "action": "buy",
            "price": 45000.0,
            "source": "tradingview"
        }
        
        # Mock successful execution for all orders
        mock_trading_service.execute_trade.return_value = {
            "success": True,
            "trade_id": "trade_multi",
            "executed_price": 45000.0,
            "executed_quantity": 0.1
        }
        
        # Process signal matching
        await order_matching_service.process_signal_matching(signal_data, {"symbol": "BTCUSDT"})
        
        # Verify all orders were processed
        assert mock_trading_service.execute_trade.call_count == 3
        
        # Verify all orders are executed
        for order_id in order_ids:
            order = await redis_service.get_order(order_id)
            assert order["status"] == "executed"
    
    @pytest_asyncio.async_test
    async def test_order_with_take_profit_stop_loss_creation(self, redis_service, 
                                                           mock_trading_service,
                                                           order_matching_service):
        """Test order execution creates TP/SL exit orders"""
        
        # Create order with TP/SL
        order_data = TestDataGenerator.generate_order_data({
            "symbol": "BTCUSDT",
            "side": "buy",
            "order_type": "market",
            "quantity": 0.1,
            "take_profit": 46000.0,
            "stop_loss": 43000.0
        })
        
        order_id = await redis_service.add_order(order_data)
        
        # Mock successful execution
        mock_trading_service.execute_trade.return_value = {
            "success": True,
            "trade_id": "trade_tp_sl",
            "executed_price": 45000.0,
            "executed_quantity": 0.1
        }
        
        # Execute the order
        order = await redis_service.get_order(order_id)
        await order_matching_service.execute_order(order)
        
        # Give time for exit orders to be created
        await asyncio.sleep(0.1)
        
        # Verify TP and SL orders were created
        pending_orders = await redis_service.get_pending_orders(limit=10)
        
        tp_orders = [o for o in pending_orders if o.get("order_category") == "take_profit"]
        sl_orders = [o for o in pending_orders if o.get("order_category") == "stop_loss"]
        
        assert len(tp_orders) == 1
        assert len(sl_orders) == 1
        
        # Verify TP order details
        tp_order = tp_orders[0]
        assert tp_order["side"] == "sell"  # Opposite of original buy
        assert float(tp_order["price"]) == 46000.0
        assert tp_order["parent_order_id"] == order_id
        
        # Verify SL order details
        sl_order = sl_orders[0]
        assert sl_order["side"] == "sell"  # Opposite of original buy
        assert float(sl_order["stop_price"]) == 43000.0
        assert sl_order["parent_order_id"] == order_id

class TestOrderMatchingLogic:
    """Integration tests for order matching logic"""
    
    @pytest_asyncio.async_test
    async def test_signal_symbol_matching(self, order_matching_service, redis_service):
        """Test orders only match signals with same symbol"""
        
        # Create BTC order
        btc_order = TestDataGenerator.generate_order_data({
            "symbol": "BTCUSDT",
            "side": "buy"
        })
        await redis_service.add_order(btc_order)
        
        # Create ETH order
        eth_order = TestDataGenerator.generate_order_data({
            "symbol": "ETHUSDT", 
            "side": "buy"
        })
        await redis_service.add_order(eth_order)
        
        # Send BTC signal
        btc_signal = {"symbol": "BTCUSDT", "action": "buy", "source": "tradingview"}
        
        # Should only match BTC order
        matching_orders = await redis_service.find_matching_orders({"symbol": "BTCUSDT"})
        assert len(matching_orders) == 1
        assert matching_orders[0]["symbol"] == "BTCUSDT"
    
    @pytest_asyncio.async_test
    async def test_signal_side_matching(self, order_matching_service, redis_service):
        """Test orders only match signals with compatible sides"""
        
        # Create buy order
        buy_order = TestDataGenerator.generate_order_data({
            "symbol": "BTCUSDT",
            "side": "buy"
        })
        await redis_service.add_order(buy_order)
        
        # Create sell order
        sell_order = TestDataGenerator.generate_order_data({
            "symbol": "BTCUSDT",
            "side": "sell"
        })
        await redis_service.add_order(sell_order)
        
        # Test buy signal matches buy order
        buy_signal = {"symbol": "BTCUSDT", "action": "buy"}
        assert await order_matching_service.signal_matches_order(buy_signal, buy_order)
        assert not await order_matching_service.signal_matches_order(buy_signal, sell_order)
        
        # Test sell signal matches sell order
        sell_signal = {"symbol": "BTCUSDT", "action": "sell"}
        assert await order_matching_service.signal_matches_order(sell_signal, sell_order)
        assert not await order_matching_service.signal_matches_order(sell_signal, buy_order)
    
    @pytest_asyncio.async_test
    async def test_strategy_specific_matching(self, order_matching_service, redis_service):
        """Test orders with strategy requirements only match specific signals"""
        
        # Create strategy-specific order
        strategy_order = TestDataGenerator.generate_order_data({
            "symbol": "BTCUSDT",
            "side": "buy",
            "strategy_match": "MACD_RSI"
        })
        await redis_service.add_order(strategy_order)
        
        # Create general order (no strategy requirement)
        general_order = TestDataGenerator.generate_order_data({
            "symbol": "BTCUSDT",
            "side": "buy"
        })
        await redis_service.add_order(general_order)
        
        # Test signal with matching strategy
        matching_signal = {"symbol": "BTCUSDT", "action": "buy", "strategy": "MACD_RSI"}
        assert await order_matching_service.signal_matches_order(matching_signal, strategy_order)
        assert await order_matching_service.signal_matches_order(matching_signal, general_order)
        
        # Test signal with different strategy
        non_matching_signal = {"symbol": "BTCUSDT", "action": "buy", "strategy": "EMA_Cross"}
        assert not await order_matching_service.signal_matches_order(non_matching_signal, strategy_order)
        assert await order_matching_service.signal_matches_order(non_matching_signal, general_order)

class TestErrorHandlingIntegration:
    """Integration tests for error handling scenarios"""
    
    @pytest_asyncio.async_test
    async def test_trading_service_failure_handling(self, redis_service, mock_trading_service,
                                                   order_matching_service):
        """Test handling when trading service fails during execution"""
        
        # Create order
        order_data = TestDataGenerator.generate_order_data({
            "symbol": "BTCUSDT",
            "side": "buy",
            "order_type": "market",
            "quantity": 0.1
        })
        order_id = await redis_service.add_order(order_data)
        
        # Mock trading failure
        mock_trading_service.execute_trade.return_value = {
            "success": False,
            "error": "Insufficient balance"
        }
        
        # Execute order
        order = await redis_service.get_order(order_id)
        await order_matching_service.execute_order(order)
        
        # Verify order is marked as failed
        updated_order = await redis_service.get_order(order_id)
        assert updated_order["status"] == "failed"
        assert "Insufficient balance" in updated_order.get("error_message", "")
    
    @pytest_asyncio.async_test
    async def test_redis_connection_failure_handling(self, mock_trading_service, 
                                                    order_matching_service):
        """Test handling when Redis connection fails"""
        
        # Create order matching service with failing Redis
        failing_redis = AsyncMock()
        failing_redis.get_pending_orders.side_effect = Exception("Redis connection failed")
        
        failing_service = type(order_matching_service)(failing_redis, mock_trading_service)
        
        # Should handle Redis failure gracefully
        await failing_service.process_pending_orders()
        
        # Should not crash and continue operation
        assert not failing_service.matching_loop_running
    
    @pytest_asyncio.async_test
    async def test_partial_order_execution_failure(self, redis_service, mock_trading_service,
                                                  order_matching_service):
        """Test handling partial execution failures"""
        
        # Create order
        order_data = TestDataGenerator.generate_order_data({
            "symbol": "BTCUSDT",
            "side": "buy",
            "order_type": "market",
            "quantity": 1.0
        })
        order_id = await redis_service.add_order(order_data)
        
        # Mock partial execution
        mock_trading_service.execute_trade.return_value = {
            "success": True,
            "trade_id": "partial_trade",
            "executed_price": 45000.0,
            "executed_quantity": 0.5,  # Only half executed
            "remaining_quantity": 0.5
        }
        
        # Execute order
        order = await redis_service.get_order(order_id)
        await order_matching_service.execute_order(order)
        
        # Verify order status and partial execution details
        updated_order = await redis_service.get_order(order_id)
        assert updated_order["status"] == "executed"
        assert updated_order["executed_quantity"] == 0.5

class TestConcurrencyIntegration:
    """Integration tests for concurrent operations"""
    
    @pytest_asyncio.async_test
    async def test_concurrent_signal_processing(self, redis_service, mock_trading_service,
                                              order_matching_service):
        """Test processing multiple signals concurrently"""
        
        # Create multiple orders
        order_ids = []
        for i in range(5):
            order_data = TestDataGenerator.generate_order_data({
                "user_id": f"user_{i}",
                "symbol": "BTCUSDT",
                "side": "buy",
                "order_type": "market",
                "quantity": 0.1
            })
            order_id = await redis_service.add_order(order_data)
            order_ids.append(order_id)
        
        # Mock successful execution
        mock_trading_service.execute_trade.return_value = {
            "success": True,
            "trade_id": "concurrent_trade",
            "executed_price": 45000.0,
            "executed_quantity": 0.1
        }
        
        # Process multiple signals concurrently
        signals = [
            {"symbol": "BTCUSDT", "action": "buy", "price": 45000.0 + i}
            for i in range(3)
        ]
        
        tasks = [
            order_matching_service.process_signal_matching(signal, {"symbol": "BTCUSDT"})
            for signal in signals
        ]
        
        await asyncio.gather(*tasks)
        
        # Verify all orders were processed (some may have been processed by multiple signals)
        executed_count = 0
        for order_id in order_ids:
            order = await redis_service.get_order(order_id)
            if order["status"] == "executed":
                executed_count += 1
        
        assert executed_count > 0  # At least some orders should be executed
    
    @pytest_asyncio.async_test
    async def test_order_queue_stress_test(self, redis_service, mock_trading_service,
                                         order_matching_service):
        """Test order queue under stress with many orders"""
        
        # Create many orders
        order_count = 20
        order_ids = []
        
        for i in range(order_count):
            order_data = TestDataGenerator.generate_order_data({
                "user_id": f"stress_user_{i}",
                "symbol": "BTCUSDT",
                "side": "buy" if i % 2 == 0 else "sell",
                "order_type": "limit",
                "quantity": 0.01,
                "price": 45000 + (i * 10)
            })
            order_id = await redis_service.add_order(order_data)
            order_ids.append(order_id)
        
        # Verify all orders are in pending queue
        pending_orders = await redis_service.get_pending_orders(limit=50)
        assert len(pending_orders) >= order_count
        
        # Process orders in batches
        mock_trading_service.get_current_price.return_value = 45100.0
        
        # Simulate order matching loop processing
        for _ in range(5):  # Multiple processing cycles
            await order_matching_service.process_pending_orders()
            await asyncio.sleep(0.01)  # Small delay between cycles
        
        # Verify queue statistics are reasonable
        stats = await redis_service.get_queue_stats()
        total_orders = (stats["pending_orders"] + stats["matched_orders"] + 
                       stats["executed_orders"] + stats["failed_orders"])
        assert total_orders >= order_count 