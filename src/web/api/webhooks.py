"""
TradingView Webhook API Handler
Receives and processes TradingView webhook signals
"""
import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field
import hashlib
import hmac

from ..services.redis_service import RedisService

logger = logging.getLogger(__name__)

webhook_router = APIRouter()

class TradingViewSignal(BaseModel):
    """TradingView webhook signal model"""
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    action: str = Field(..., description="buy, sell, or close")
    price: float = Field(..., description="Current price")
    quantity: float = Field(default=0, description="Quantity to trade")
    strategy: str = Field(default="", description="Strategy name")
    timeframe: str = Field(default="", description="Chart timeframe")
    timestamp: str = Field(default="", description="Signal timestamp")
    
    # Optional TradingView fields
    open: float = Field(default=0, description="Open price")
    high: float = Field(default=0, description="High price") 
    low: float = Field(default=0, description="Low price")
    close: float = Field(default=0, description="Close price")
    volume: float = Field(default=0, description="Volume")
    
    # Custom indicators from TradingView
    indicators: Dict[str, Any] = Field(default_factory=dict, description="Custom indicators")
    
    # Alert metadata
    alert_name: str = Field(default="", description="TradingView alert name")
    interval: str = Field(default="", description="Chart interval")

class WebhookResponse(BaseModel):
    """Webhook response model"""
    status: str
    signal_id: str
    message: str
    timestamp: str

@webhook_router.post("/tradingview", response_model=WebhookResponse)
async def receive_tradingview_webhook(
    signal: TradingViewSignal,
    background_tasks: BackgroundTasks,
    request: Request
):
    """
    Receive TradingView webhook signal
    
    This endpoint receives trading signals from TradingView alerts and
    processes them for order matching and execution.
    """
    try:
        logger.info(f"📡 Received TradingView signal: {signal.symbol} {signal.action} @ {signal.price}")
        
        # Validate webhook (implement HMAC verification if needed)
        # webhook_secret = os.getenv("TRADINGVIEW_WEBHOOK_SECRET")
        # if webhook_secret:
        #     if not verify_webhook_signature(request, webhook_secret):
        #         raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Prepare signal data
        signal_data = signal.dict()
        signal_data["source"] = "tradingview"
        signal_data["raw_data"] = signal_data.copy()
        
        # Add timestamp if not provided
        if not signal_data["timestamp"]:
            signal_data["timestamp"] = datetime.now().isoformat()
        
        # Store signal in Redis
        from ..main import redis_service
        if not redis_service:
            raise HTTPException(status_code=500, detail="Redis service not available")
        
        signal_id = await redis_service.store_tradingview_signal(signal_data)
        
        # Process signal in background
        background_tasks.add_task(process_tradingview_signal, signal_data, signal_id)
        
        return WebhookResponse(
            status="received",
            signal_id=signal_id,
            message=f"TradingView signal processed: {signal.symbol} {signal.action}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing TradingView webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

async def process_tradingview_signal(signal_data: Dict[str, Any], signal_id: str):
    """Process TradingView signal for order matching"""
    try:
        logger.info(f"🔄 Processing TradingView signal {signal_id}")
        
        from ..main import order_matching
        if not order_matching:
            logger.error("Order matching service not available")
            return
        
        # Check for matching orders based on signal
        matching_criteria = {
            "symbol": signal_data["symbol"],
            "signal_action": signal_data["action"],
            "strategy": signal_data.get("strategy", ""),
        }
        
        # Trigger order matching process
        await order_matching.process_signal_matching(signal_data, matching_criteria)
        
        logger.info(f"✅ TradingView signal {signal_id} processed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error processing TradingView signal {signal_id}: {e}")

def verify_webhook_signature(request: Request, secret: str) -> bool:
    """Verify TradingView webhook signature (optional security)"""
    try:
        signature = request.headers.get("X-TradingView-Signature")
        if not signature:
            return False
        
        # Get request body
        body = request.body()
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False

@webhook_router.get("/test")
async def test_webhook():
    """Test webhook endpoint"""
    return {
        "status": "online",
        "endpoint": "TradingView Webhook Handler",
        "timestamp": datetime.now().isoformat()
    }

@webhook_router.post("/test")
async def test_webhook_post(data: Dict[str, Any]):
    """Test webhook with POST data"""
    logger.info(f"📧 Test webhook received: {data}")
    return {
        "status": "received",
        "data": data,
        "timestamp": datetime.now().isoformat()
    } 