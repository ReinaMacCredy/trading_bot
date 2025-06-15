"""
API configuration and documentation settings.
"""

from typing import Dict, Any

# API metadata
API_TITLE = "Trading Bot API"
API_DESCRIPTION = """
Trading Bot API for handling TradingView webhooks and managing trading operations.

## Features
* TradingView webhook integration
* Order management
* Position management
* Health monitoring

## Authentication
Currently, the API does not require authentication. In production, implement proper authentication.

## Rate Limiting
API calls are not currently rate-limited. In production, implement rate limiting.
"""
API_VERSION = "1.0.0"
API_TERMS_OF_SERVICE = "http://example.com/terms/"
API_CONTACT: Dict[str, Any] = {
    "name": "Trading Bot Support",
    "url": "http://example.com/contact/",
    "email": "support@example.com",
}
API_LICENSE_INFO: Dict[str, Any] = {
    "name": "MIT",
    "url": "https://opensource.org/licenses/MIT",
}

# API tags metadata
TAGS_METADATA = [
    {
        "name": "webhook",
        "description": "Operations with TradingView webhooks",
        "externalDocs": {
            "description": "TradingView Webhook Documentation",
            "url": "https://www.tradingview.com/support/solutions/43000529348",
        },
    },
    {
        "name": "orders",
        "description": "Manage trading orders",
    },
    {
        "name": "positions",
        "description": "Manage trading positions",
    },
    {
        "name": "health",
        "description": "Health check endpoints",
    },
] 