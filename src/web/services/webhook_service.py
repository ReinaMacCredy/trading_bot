# from typing import Dict, Any
# import logging
# from src.web.services.signal_processor import SignalProcessor
# from src.web.middlewares import ValidationError

# logger = logging.getLogger(__name__)

# class WebhookService:
#     """Service for handling webhook-related business logic"""
    
#     def __init__(self, signal_processor: SignalProcessor):
#         self.signal_processor = signal_processor
    
#     async def process_tradingview_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Process a webhook from TradingView
        
#         Args:
#             data: Webhook payload
            
#         Returns:
#             Dict with processing result
            
#         Raises:
#             ValidationError: If payload validation fails
#         """
#         # Validate required fields
#         required_fields = ["symbol", "timeframe", "action"]
#         missing_fields = [field for field in required_fields if field not in data]
#         if missing_fields:
#             raise ValidationError(
#                 f"Missing required fields: {missing_fields}",
#                 {"missing_fields": missing_fields}
#             )
            
#         # Validate action
#         if data["action"] not in ["buy", "sell"]:
#             raise ValidationError(
#                 "Invalid action. Must be 'buy' or 'sell'",
#                 {"action": data["action"]}
#             )
            
#         try:
#             # Register signal
#             await self.signal_processor.register_tradingview_signal(
#                 symbol=data["symbol"],
#                 timeframe=data["timeframe"],
#                 action=data["action"],
#                 data=data.get("data", {})
#             )
            
#             # Process signals for the symbol
#             await self.signal_processor.process_signals(data["symbol"])
            
#             return {
#                 "status": "success",
#                 "message": "Signal processed",
#                 "symbol": data["symbol"],
#                 "action": data["action"]
#             }
            
#         except Exception as e:
#             logger.error(f"Error processing TradingView webhook: {e}")
#             raise ValidationError(
#                 f"Error processing webhook: {str(e)}",
#                 {"error": str(e)}
#             ) 