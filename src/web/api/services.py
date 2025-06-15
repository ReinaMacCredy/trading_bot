from typing import List, Dict, Any, Optional
from src.trading.clients.mt5_client import MT5Client
from src.trading.core.legacy_trading import TradeExecutor

class OrderService:
    def __init__(self, mt5_client: MT5Client):
        self.mt5_client = mt5_client

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order"""
        if order_data.get('type') == 'market':
            result = await self.mt5_client.place_market_order(
                symbol=order_data['symbol'],
                side=order_data['side'],
                volume=order_data['volume'],
                sl=order_data.get('stop_loss', 0.0),
                tp=order_data.get('take_profit', 0.0)
            )
        else:
            result = await self.mt5_client.place_pending_order(
                symbol=order_data['symbol'],
                side=order_data['side'],
                volume=order_data['volume'],
                price=order_data['price'],
                sl=order_data.get('stop_loss', 0.0),
                tp=order_data.get('take_profit', 0.0)
            )
        return result.__dict__

    async def get_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """Get all pending orders for a symbol"""
        return await self.mt5_client.fetch_open_orders(symbol)

    async def cancel_orders(self, symbol: str) -> None:
        """Cancel all pending orders for a symbol"""
        orders = await self.mt5_client.fetch_open_orders(symbol)
        for order in orders:
            await self.mt5_client.close_position(order['ticket'])

class PositionService:
    def __init__(self, mt5_client: MT5Client):
        self.mt5_client = mt5_client

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all active positions"""
        return await self.mt5_client.fetch_positions()

    async def update_position(
        self,
        symbol: str,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None
    ) -> None:
        """Update take profit or stop loss for a position"""
        positions = await self.mt5_client.fetch_positions(symbol)
        for position in positions:
            # Note: MT5 doesn't have a direct method to modify SL/TP
            # We need to close the position and open a new one
            await self.mt5_client.close_position(position['ticket'])
            await self.mt5_client.place_market_order(
                symbol=position['symbol'],
                side=position['type'],
                volume=position['volume'],
                sl=stop_loss or position['sl'],
                tp=take_profit or position['tp']
            )

    async def close_position(self, symbol: str) -> None:
        """Close a position"""
        positions = await self.mt5_client.fetch_positions(symbol)
        for position in positions:
            await self.mt5_client.close_position(position['ticket']) 