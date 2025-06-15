from typing import Dict, Any
from datetime import datetime
import logging
from src.trading.clients.mt5_client import MT5Client
from src.web.middlewares import ValidationError

logger = logging.getLogger(__name__)

class HealthService:
    """Service for handling health check-related business logic"""
    
    def __init__(self, mt5_client: MT5Client):
        self.mt5_client = mt5_client
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check server health
        
        Returns:
            Dict with health check result
            
        Raises:
            ValidationError: If health check fails
        """
        try:
            mt5_connected = self.mt5_client.is_connected()
            return {
                "status": "success",
                "mt5_connected": mt5_connected,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            raise ValidationError(
                f"Error in health check: {str(e)}",
                {"error": str(e)}
            ) 