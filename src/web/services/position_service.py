from typing import Dict, Any, List, Optional
import logging
from src.trading.core.legacy_trading import TradeExecutor
from src.web.middleware import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

class PositionService:
    """Service for handling position-related business logic"""
    
    def __init__(self, trade_executor: TradeExecutor):
        self.trade_executor = trade_executor
    
    async def get_positions(self) -> Dict[str, Any]:
        """
        Get all active positions
        
        Returns:
            Dict with list of positions
            
        Raises:
            ValidationError: If position retrieval fails
        """
        try:
            positions = self.trade_executor.get_active_positions()
            return {
                "status": "success",
                "positions": positions
            }
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise ValidationError(
                f"Error getting positions: {str(e)}",
                {"error": str(e)}
            )
    
    async def update_position(
        self,
        symbol: str,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Update take profit or stop loss for a position
        
        Args:
            symbol: Trading symbol
            take_profit: New take profit price
            stop_loss: New stop loss price
            
        Returns:
            Dict with update result
            
        Raises:
            NotFoundError: If position not found
        """
        try:
            await self.trade_executor.update_position(
                symbol=symbol,
                take_profit=take_profit,
                stop_loss=stop_loss
            )
            return {
                "status": "success",
                "message": f"Updated position for {symbol}"
            }
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            raise NotFoundError(
                f"Error updating position: {str(e)}",
                {"symbol": symbol, "error": str(e)}
            )
    
    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """
        Close a position
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dict with close result
            
        Raises:
            NotFoundError: If position not found
        """
        try:
            await self.trade_executor.close_position(symbol)
            return {
                "status": "success",
                "message": f"Closed position for {symbol}"
            }
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            raise NotFoundError(
                f"Error closing position: {str(e)}",
                {"symbol": symbol, "error": str(e)}
            ) 