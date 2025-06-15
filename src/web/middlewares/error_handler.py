from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging
from typing import Union, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TradingBotError(Exception):
    """Base exception for trading bot errors"""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(TradingBotError):
    """Raised when input validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)

class AuthenticationError(TradingBotError):
    """Raised when authentication fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, details)

class NotFoundError(TradingBotError):
    """Raised when a resource is not found"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, details)

async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global error handler middleware"""
    if isinstance(exc, TradingBotError):
        logger.error(f"TradingBotError: {exc.message}", extra=exc.details)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.message,
                "details": exc.details
            }
        )
    
    # Handle unexpected errors
    logger.exception("Unexpected error occurred")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "details": {"error": str(exc)}
        }
    ) 