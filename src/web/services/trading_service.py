"""
Trading Service
Integrates with existing trading infrastructure for order execution
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...trading.exchange_client import ExchangeClient
from ...config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class TradingService:
    """Trading service for order execution"""
    
    def __init__(self, config: Any):
        self.config = config
        self.exchange_client = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize trading service"""
        try:
            # Initialize exchange client using existing infrastructure
            self.exchange_client = ExchangeClient(self.config)
            await self.exchange_client.initialize()
            
            self.initialized = True
            logger.info("✅ Trading service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize trading service: {e}")
            raise
    
    async def close(self):
        """Close trading service"""
        if self.exchange_client:
            await self.exchange_client.close()
        self.initialized = False
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for symbol"""
        try:
            if not self.initialized:
                logger.error("Trading service not initialized")
                return None
            
            price_data = await self.exchange_client.get_price(symbol)
            return float(price_data) if price_data else None
            
        except Exception as e:
            logger.error(f"❌ Error getting price for {symbol}: {e}")
            return None
    
    async def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute trade order"""
        try:
            if not self.initialized:
                return {
                    "success": False,
                    "error": "Trading service not initialized"
                }
            
            logger.info(f"🔄 Executing trade: {symbol} {side} {quantity} {order_type}")
            
            # Prepare order parameters
            order_params = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "type": order_type
            }
            
            if price:
                order_params["price"] = price
            if stop_price:
                order_params["stop_price"] = stop_price
            
            # Execute order using existing exchange client
            result = await self.exchange_client.place_order(**order_params)
            
            if result.get("success"):
                return {
                    "success": True,
                    "trade_id": result.get("order_id"),
                    "executed_price": result.get("price"),
                    "executed_quantity": result.get("quantity"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
            
        except Exception as e:
            logger.error(f"❌ Error executing trade: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        try:
            if not self.initialized:
                return {"error": "Trading service not initialized"}
            
            return await self.exchange_client.get_balance()
            
        except Exception as e:
            logger.error(f"❌ Error getting balance: {e}")
            return {"error": str(e)}
    
    async def get_open_positions(self) -> Dict[str, Any]:
        """Get open trading positions"""
        try:
            if not self.initialized:
                return {"error": "Trading service not initialized"}
            
            return await self.exchange_client.get_positions()
            
        except Exception as e:
            logger.error(f"❌ Error getting positions: {e}")
            return {"error": str(e)}
    
    async def validate_order(self, symbol: str, side: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Validate order parameters before execution"""
        try:
            # Get symbol info
            symbol_info = await self.exchange_client.get_symbol_info(symbol)
            if not symbol_info:
                return {"valid": False, "error": f"Invalid symbol: {symbol}"}
            
            # Check minimum quantity
            min_qty = symbol_info.get("min_quantity", 0)
            if quantity < min_qty:
                return {"valid": False, "error": f"Quantity below minimum: {min_qty}"}
            
            # Check minimum notional value
            min_notional = symbol_info.get("min_notional", 0)
            if price and (quantity * price) < min_notional:
                return {"valid": False, "error": f"Order value below minimum: {min_notional}"}
            
            # Check account balance
            balance = await self.get_account_balance()
            if balance.get("error"):
                return {"valid": False, "error": "Could not verify balance"}
            
            return {"valid": True}
            
        except Exception as e:
            logger.error(f"❌ Error validating order: {e}")
            return {"valid": False, "error": str(e)} 