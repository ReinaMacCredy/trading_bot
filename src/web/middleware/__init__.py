"""
Middleware package for the trading bot web server.
Contains error handlers, authentication, and other middleware components.
"""

from .error_handler import (
    TradingBotError,
    ValidationError,
    AuthenticationError,
    NotFoundError,
    error_handler
)

__all__ = [
    'TradingBotError',
    'ValidationError',
    'AuthenticationError',
    'NotFoundError',
    'error_handler'
] 