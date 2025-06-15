from typing import Dict, Any, List, Optional
import logging
from src.trading.clients.mt5_client import MT5Client
from src.web.middlewares import ValidationError, NotFoundError
from src.web.models.state_responses import SuccessResponse

logger = logging.getLogger(__name__)

class PositionService:
    """Service for handling position-related business logic"""
    
    def __init__(self, mt5_client: MT5Client):
        self.mt5_client = mt5_client
    
    async def get_positions(self) -> Dict[str, Any]:
        """
        Get all active positions
        
        Returns:
            Dict with list of positions
            
        Raises:
            ValidationError: If position retrieval fails
        """
        try:
            positions = await self.mt5_client.fetch_positions()
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
        stop_loss: Optional[float] = None,
        comment: Optional[str] = None
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
            await self.mt5_client.modify_position(int(symbol), take_profit, stop_loss, comment)
            return SuccessResponse(
                status="success",
                message=f"Updated position for {symbol}"
            )
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
            await self.mt5_client.close_position(int(symbol))
            return SuccessResponse(
                status="success",
                message=f"Closed position for {symbol}"
            )
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            raise NotFoundError(
                f"Error closing position: {str(e)}",
                {"symbol": symbol, "error": str(e)}
            ) 
        
__all__ = ["PositionService"]