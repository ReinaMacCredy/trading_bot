"""
Enhanced Exchange Client for Discord Trading Bot
Supports multiple exchanges via CCXT with professional error handling
"""

import ccxt
import asyncio
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
import time
from datetime import datetime, timedelta
from src.config.config_loader import get_config
from src.trading.core.order_history import OrderHistory
import os

logger = logging.getLogger(__name__)

@dataclass
class OrderResult:
    """Container for order execution results"""
    success: bool
    order_id: Optional[str] = None
    symbol: str = ""
    side: str = ""
    amount: float = 0.0
    price: float = 0.0
    cost: float = 0.0
    fee: Optional[Dict] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

@dataclass
class BalanceInfo:
    """Container for account balance information"""
    total: Dict[str, float]
    free: Dict[str, float]
    used: Dict[str, float]
    timestamp: datetime

class ExchangeClient:
    """
    Professional exchange client supporting multiple exchanges via CCXT
    Includes rate limiting, retry logic, and comprehensive error handling
    """
    
    def __init__(self, exchange_name: str = None, sandbox: bool = True, config=None, order_history: Optional[OrderHistory] = None):
        self.config = config or get_config()
        self.exchange_name = exchange_name or self.config.exchange.name
        self.sandbox = sandbox or self.config.exchange.sandbox
        self.exchange = None
        self.order_history = order_history or OrderHistory()
        self._last_request_time = {}
        self._rate_limit_delay = 1.0  # Minimum delay between requests
        
        self._initialize_exchange()
    
    def _initialize_exchange(self):
        """Initialize the exchange connection"""
        try:
            exchange_class = getattr(ccxt, self.exchange_name.lower())
            
            # Exchange configuration
            exchange_config = {
                'enableRateLimit': self.config.exchange.rate_limit,
                'timeout': self.config.exchange.timeout,
                'sandbox': self.sandbox,
            }
            
            # Add API credentials if available
            api_key = os.getenv(f'{self.exchange_name.upper()}_API_KEY')
            secret = os.getenv(f'{self.exchange_name.upper()}_SECRET')
            
            if api_key and secret:
                exchange_config['apiKey'] = api_key
                exchange_config['secret'] = secret
                logger.info(f"Exchange credentials loaded for {self.exchange_name}")
            else:
                logger.warning(f"No API credentials found for {self.exchange_name}")
            
            # Binance specific configuration
            if self.exchange_name.lower() == 'binance':
                if self.sandbox:
                    exchange_config['urls'] = {
                        'api': {
                            'public': 'https://testnet.binance.vision/api',
                            'private': 'https://testnet.binance.vision/api',
                        }
                    }
            
            self.exchange = exchange_class(exchange_config)
            logger.info(f"Exchange {self.exchange_name} initialized (sandbox: {self.sandbox})")
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange {self.exchange_name}: {e}")
            raise
    
    async def _rate_limit_check(self, endpoint: str = 'default'):
        """Check and enforce rate limiting"""
        now = time.time()
        last_request = self._last_request_time.get(endpoint, 0)
        
        time_since_last = now - last_request
        if time_since_last < self._rate_limit_delay:
            sleep_time = self._rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self._last_request_time[endpoint] = time.time()
    
    async def _retry_request(self, func, *args, max_retries: int = None, **kwargs):
        """Execute request with retry logic"""
        max_retries = max_retries or self.config.exchange.retry_attempts
        retry_delay = self.config.exchange.retry_delay / 1000  # Convert to seconds
        
        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except ccxt.NetworkError as e:
                if attempt < max_retries:
                    logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    logger.error(f"Network error after {max_retries + 1} attempts: {e}")
                    raise
            except ccxt.RateLimitExceeded as e:
                if attempt < max_retries:
                    logger.warning(f"Rate limit exceeded on attempt {attempt + 1}: {e}")
                    await asyncio.sleep(retry_delay * (3 ** attempt))  # Longer backoff for rate limits
                    continue
                else:
                    logger.error(f"Rate limit exceeded after {max_retries + 1} attempts: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
    
    async def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Fetch current ticker information for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Ticker information dictionary or None if error
        """
        try:
            await self._rate_limit_check('ticker')
            
            async def _fetch():
                return self.exchange.fetch_ticker(symbol)
            
            ticker = await self._retry_request(_fetch)
            logger.debug(f"Fetched ticker for {symbol}: {ticker['last']}")
            return ticker
            
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100, since: int = None) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a symbol
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (1m, 5m, 1h, 1d, etc.)
            limit: Number of candles to fetch
            since: Start timestamp (optional)
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            await self._rate_limit_check('ohlcv')
            
            async def _fetch():
                return self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            
            ohlcv_data = await self._retry_request(_fetch)
            
            if not ohlcv_data:
                logger.warning(f"No OHLCV data returned for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.debug(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return None
    
    async def fetch_multiple_tickers(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch tickers for multiple symbols
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            Dictionary mapping symbols to ticker data
        """
        try:
            await self._rate_limit_check('multiple_tickers')
            
            async def _fetch():
                return self.exchange.fetch_tickers(symbols)
            
            tickers = await self._retry_request(_fetch)
            logger.debug(f"Fetched tickers for {len(symbols)} symbols")
            return tickers
            
        except Exception as e:
            logger.error(f"Error fetching multiple tickers: {e}")
            return {}
    
    async def fetch_balance(self) -> Optional[BalanceInfo]:
        """
        Fetch account balance
        
        Returns:
            BalanceInfo object or None if error
        """
        try:
            if not self.exchange.apiKey:
                logger.warning("No API key available for balance fetch")
                return None
            
            await self._rate_limit_check('balance')
            
            async def _fetch():
                return self.exchange.fetch_balance()
            
            balance_data = await self._retry_request(_fetch)
            
            return BalanceInfo(
                total=balance_data.get('total', {}),
                free=balance_data.get('free', {}),
                used=balance_data.get('used', {}),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None
    
    async def place_market_order(self, symbol: str, side: str, amount: float) -> OrderResult:
        """
        Place a market order
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount
            
        Returns:
            OrderResult with execution details
        """
        try:
            if not self.exchange.apiKey:
                return OrderResult(
                    success=False,
                    error_message="No API key configured for trading"
                )
            
            await self._rate_limit_check('order')
            
            async def _place_order():
                return self.exchange.create_market_order(symbol, side, amount)
            
            order = await self._retry_request(_place_order)

            result = OrderResult(
                success=True,
                order_id=order.get('id'),
                symbol=symbol,
                side=side,
                amount=amount,
                price=order.get('average', 0),
                cost=order.get('cost', 0),
                fee=order.get('fee'),
                metadata=order
            )

            self.order_history.add_order(
                order_id=result.order_id or '',
                symbol=symbol,
                side=side,
                amount=amount,
                price=result.price,
                status='placed',
                order_type='market'
            )

            return result
            
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return OrderResult(
                success=False,
                symbol=symbol,
                side=side,
                amount=amount,
                error_message=str(e)
            )
    
    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> OrderResult:
        """
        Place a limit order
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount
            price: Limit price
            
        Returns:
            OrderResult with execution details
        """
        try:
            if not self.exchange.apiKey:
                return OrderResult(
                    success=False,
                    error_message="No API key configured for trading"
                )
            
            await self._rate_limit_check('order')
            
            async def _place_order():
                return self.exchange.create_limit_order(symbol, side, amount, price)
            
            order = await self._retry_request(_place_order)

            result = OrderResult(
                success=True,
                order_id=order.get('id'),
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                cost=order.get('cost', amount * price),
                fee=order.get('fee'),
                metadata=order
            )

            self.order_history.add_order(
                order_id=result.order_id or '',
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                status='placed',
                order_type='limit'
            )

            return result
            
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return OrderResult(
                success=False,
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                error_message=str(e)
            )
    
    async def place_oco_order(self, symbol: str, side: str, amount: float, price: float, stop_price: float, stop_limit_price: float = None) -> OrderResult:
        """
        Place an OCO (One-Cancels-Other) order for advanced risk management
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount
            price: Take profit price
            stop_price: Stop loss trigger price
            stop_limit_price: Stop limit price (optional)
            
        Returns:
            OrderResult with execution details
        """
        try:
            if not self.exchange.apiKey:
                return OrderResult(
                    success=False,
                    error_message="No API key configured for trading"
                )
            
            # Check if exchange supports OCO orders
            if not hasattr(self.exchange, 'create_oco_order'):
                # Fallback: Place separate orders
                logger.warning(f"Exchange {self.exchange_name} doesn't support OCO orders, placing separate orders")
                
                # Place limit order first
                limit_result = await self.place_limit_order(symbol, side, amount, price)
                if not limit_result.success:
                    return limit_result
                
                # Place stop loss order
                stop_side = 'sell' if side == 'buy' else 'buy'
                stop_result = await self.place_stop_order(symbol, stop_side, amount, stop_price, stop_limit_price)
                
                return OrderResult(
                    success=True,
                    order_id=f"{limit_result.order_id}|{stop_result.order_id}",
                    symbol=symbol,
                    side=side,
                    amount=amount,
                    price=price,
                    metadata={
                        'limit_order': limit_result.metadata,
                        'stop_order': stop_result.metadata,
                        'oco_type': 'manual'
                    }
                )
            
            await self._rate_limit_check('oco_order')
            
            async def _place_oco():
                return self.exchange.create_oco_order(
                    symbol, side, amount, price, stop_price, stop_limit_price
                )
            
            order = await self._retry_request(_place_oco)

            result = OrderResult(
                success=True,
                order_id=order.get('id'),
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                metadata=order
            )

            self.order_history.add_order(
                order_id=result.order_id or '',
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                status='placed',
                order_type='oco'
            )

            return result
            
        except Exception as e:
            logger.error(f"Error placing OCO order: {e}")
            return OrderResult(
                success=False,
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                error_message=str(e)
            )
    
    async def place_stop_order(self, symbol: str, side: str, amount: float, stop_price: float, limit_price: float = None) -> OrderResult:
        """
        Place a stop loss order
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount
            stop_price: Stop trigger price
            limit_price: Limit price for stop-limit orders (optional)
            
        Returns:
            OrderResult with execution details
        """
        try:
            if not self.exchange.apiKey:
                return OrderResult(
                    success=False,
                    error_message="No API key configured for trading"
                )
            
            await self._rate_limit_check('stop_order')
            
            async def _place_stop():
                if limit_price:
                    return self.exchange.create_stop_limit_order(symbol, side, amount, stop_price, limit_price)
                else:
                    return self.exchange.create_stop_market_order(symbol, side, amount, stop_price)
            
            order = await self._retry_request(_place_stop)

            result = OrderResult(
                success=True,
                order_id=order.get('id'),
                symbol=symbol,
                side=side,
                amount=amount,
                price=stop_price,
                metadata=order
            )

            self.order_history.add_order(
                order_id=result.order_id or '',
                symbol=symbol,
                side=side,
                amount=amount,
                price=stop_price,
                status='placed',
                order_type='stop'
            )

            return result
            
        except Exception as e:
            logger.error(f"Error placing stop order: {e}")
            return OrderResult(
                success=False,
                symbol=symbol,
                side=side,
                amount=amount,
                price=stop_price,
                error_message=str(e)
            )
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an open order
        
        Args:
            order_id: Order ID to cancel
            symbol: Trading pair symbol
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.exchange.apiKey:
                logger.warning("No API key available for order cancellation")
                return False
            
            await self._rate_limit_check('cancel_order')
            
            async def _cancel():
                return self.exchange.cancel_order(order_id, symbol)
            
            result = await self._retry_request(_cancel)
            logger.info(f"Order {order_id} cancelled successfully")

            self.order_history.add_order(
                order_id=order_id,
                symbol=symbol,
                side='',
                amount=0,
                price=0,
                status='cancelled',
                order_type='cancel'
            )

            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def fetch_open_orders(self, symbol: str = None) -> List[Dict]:
        """
        Fetch open orders
        
        Args:
            symbol: Trading pair symbol (optional, fetches all if None)
            
        Returns:
            List of open orders
        """
        try:
            if not self.exchange.apiKey:
                logger.warning("No API key available for fetching orders")
                return []
            
            await self._rate_limit_check('open_orders')
            
            async def _fetch():
                return self.exchange.fetch_open_orders(symbol)
            
            orders = await self._retry_request(_fetch)
            logger.debug(f"Fetched {len(orders)} open orders")
            return orders
            
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    def get_order_history(self):
        """Return all recorded order history"""
        return self.order_history.get_all_orders()
    
    async def get_trading_fees(self, symbol: str = None) -> Dict:
        """
        Get trading fees for a symbol
        
        Args:
            symbol: Trading pair symbol (optional)
            
        Returns:
            Trading fees information
        """
        try:
            await self._rate_limit_check('trading_fees')
            
            if symbol:
                return self.exchange.calculate_fee(symbol, 'market', 'buy', 1, 1)
            else:
                return self.exchange.fees
                
        except Exception as e:
            logger.error(f"Error fetching trading fees: {e}")
            return {}
    
    def is_sandbox(self) -> bool:
        """Check if running in sandbox mode"""
        return self.sandbox
    
    def get_exchange_name(self) -> str:
        """Get exchange name"""
        return self.exchange_name
    
    async def test_connection(self) -> bool:
        """Test exchange connection"""
        try:
            # Try to fetch a ticker for a common pair
            ticker = await self.fetch_ticker('BTC/USDT')
            return ticker is not None
        except Exception as e:
            logger.error(f"Exchange connection test failed: {e}")
            return False 