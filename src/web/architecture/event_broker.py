from typing import Dict, List, Callable, Any, Optional
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """Container for trading signals"""
    source: str  # e.g., "tradingview_1h", "tradingview_4h", "price_check"
    action: str  # "buy" or "sell"
    timestamp: datetime
    data: Dict[str, Any]  # Additional signal data
    timeframe: Optional[str] = None  # For TradingView signals

class EventBroker:
    """Manages event emitters and consumers for trading signals"""
    
    def __init__(self):
        self.emitters: Dict[str, asyncio.Future] = {}
        self.consumers: Dict[str, List[Callable]] = {}
        self.signal_history: List[Signal] = []
        self.timeout = 5  # Default timeout in seconds
        
    async def register_emitter(self, emitter_id: str) -> asyncio.Future:
        """Register a new emitter and return its future"""
        if emitter_id in self.emitters:
            logger.warning(f"Emitter {emitter_id} already registered, overwriting")
        
        self.emitters[emitter_id] = asyncio.Future()
        return self.emitters[emitter_id]
    
    def register_consumer(self, consumer_id: str, callback: Callable):
        """Register a consumer callback"""
        if consumer_id not in self.consumers:
            self.consumers[consumer_id] = []
        self.consumers[consumer_id].append(callback)
    
    async def emit_signal(self, emitter_id: str, signal: Signal):
        """Emit a signal from an emitter"""
        if emitter_id not in self.emitters:
            logger.error(f"Emitter {emitter_id} not registered")
            return
            
        future = self.emitters[emitter_id]
        if not future.done():
            future.set_result(signal)
            self.signal_history.append(signal)
            
            # Notify consumers
            for consumer_id, callbacks in self.consumers.items():
                for callback in callbacks:
                    try:
                        await callback(signal)
                    except Exception as e:
                        logger.error(f"Error in consumer {consumer_id}: {e}")
    
    async def wait_for_signals(self, required_emitters: List[str], timeout: Optional[int] = None) -> Dict[str, Signal]:
        """Wait for signals from multiple emitters"""
        timeout = timeout or self.timeout
        signals = {}
        
        try:
            # Create futures for all required emitters
            futures = []
            for emitter_id in required_emitters:
                if emitter_id not in self.emitters:
                    future = await self.register_emitter(emitter_id)
                else:
                    future = self.emitters[emitter_id]
                futures.append(future)
            
            # Wait for all signals with timeout
            done, pending = await asyncio.wait(
                futures,
                timeout=timeout,
                return_when=asyncio.ALL_COMPLETED
            )
            
            # Process completed signals
            for future in done:
                signal = future.result()
                signals[signal.source] = signal
            
            # Cancel any pending futures
            for future in pending:
                future.cancel()
                
            return signals
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for signals from {required_emitters}")
            return signals
        except Exception as e:
            logger.error(f"Error waiting for signals: {e}")
            return signals
    
    def reset_emitter(self, emitter_id: str):
        """Reset an emitter's future"""
        if emitter_id in self.emitters:
            self.emitters[emitter_id] = asyncio.Future()
    
    def get_signal_history(self, limit: int = 100) -> List[Signal]:
        """Get recent signal history"""
        return self.signal_history[-limit:] 