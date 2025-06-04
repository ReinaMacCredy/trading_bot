"""
Multi-Exchange Manager for Discord Trading Bot
Handles multiple exchanges including Binance, MEXC, and MT5
"""

import logging
import asyncio
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from .exchange_client import ExchangeClient, OrderResult
from .mt5_client import MT5Client, MT5OrderResult, MT5TickerInfo
from src.config.config_loader import get_config

logger = logging.getLogger(__name__)

@dataclass
class ExchangeInfo:
    """Exchange information container"""
    name: str
    client: Union[ExchangeClient, MT5Client]
    type: str  # 'crypto' or 'forex'
    enabled: bool
    connected: bool
    last_error: Optional[str] = None

@dataclass
class UnifiedTicker:
    """Unified ticker format for all exchanges"""
    symbol: str
    exchange: str
    bid: float
    ask: float
    last: float
    volume: float
    change_24h: Optional[float] = None
    timestamp: datetime = None

@dataclass
class UnifiedOrderResult:
    """Unified order result format for all exchanges"""
    success: bool
    exchange: str
    order_id: Optional[str] = None
    symbol: str = ""
    side: str = ""
    amount: float = 0.0
    price: float = 0.0
    cost: float = 0.0
    timestamp: datetime = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

class MultiExchangeManager:
    """
    Professional multi-exchange manager supporting crypto and forex markets
    Handles Binance, MEXC (crypto) and MT5 (forex/CFD) simultaneously
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.exchanges: Dict[str, ExchangeInfo] = {}
        self.default_crypto_exchange = 'binance'
        self.default_forex_exchange = 'mt5'
        
        # Initialize exchanges
        self._initialize_exchanges()
    
    def _initialize_exchanges(self):
        """Initialize all configured exchanges"""
        logger.info("Initializing multi-exchange manager...")
        
        # Initialize crypto exchanges (Binance, MEXC)
        crypto_exchanges = ['binance', 'mexc']
        for exchange_name in crypto_exchanges:
            try:
                client = ExchangeClient(
                    exchange_name=exchange_name,
                    sandbox=self.config.exchange.sandbox,
                    config=self.config
                )
                
                self.exchanges[exchange_name] = ExchangeInfo(
                    name=exchange_name,
                    client=client,
                    type='crypto',
                    enabled=True,
                    connected=False  # Will be tested later
                )
                
                logger.info(f"Initialized {exchange_name} crypto exchange")
                
            except Exception as e:
                logger.error(f"Failed to initialize {exchange_name}: {e}")
                self.exchanges[exchange_name] = ExchangeInfo(
                    name=exchange_name,
                    client=None,
                    type='crypto',
                    enabled=False,
                    connected=False,
                    last_error=str(e)
                )
        
        # Initialize MT5 forex exchange
        try:
            if hasattr(self.config.exchanges, 'mt5') and self.config.exchanges.mt5.enabled:
                mt5_client = MT5Client(config=self.config)
                
                self.exchanges['mt5'] = ExchangeInfo(
                    name='mt5',
                    client=mt5_client,
                    type='forex',
                    enabled=mt5_client.enabled,
                    connected=mt5_client.is_connected()
                )
                
                logger.info(f"Initialized MT5 forex exchange (connected: {mt5_client.is_connected()})")
            else:
                logger.info("MT5 disabled in configuration")
                self.exchanges['mt5'] = ExchangeInfo(
                    name='mt5',
                    client=None,
                    type='forex',
                    enabled=False,
                    connected=False,
                    last_error="Disabled in configuration"
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize MT5: {e}")
            self.exchanges['mt5'] = ExchangeInfo(
                name='mt5',
                client=None,
                type='forex',
                enabled=False,
                connected=False,
                last_error=str(e)
            )
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all exchanges"""
        results = {}
        
        for name, exchange_info in self.exchanges.items():
            if not exchange_info.enabled or exchange_info.client is None:
                results[name] = False
                continue
                
            try:
                if isinstance(exchange_info.client, MT5Client):
                    connected = await exchange_info.client.test_connection()
                else:
                    connected = await exchange_info.client.test_connection()
                
                exchange_info.connected = connected
                results[name] = connected
                
                logger.info(f"{name} connection test: {'✓' if connected else '✗'}")
                
            except Exception as e:
                logger.error(f"Connection test failed for {name}: {e}")
                exchange_info.last_error = str(e)
                exchange_info.connected = False
                results[name] = False
        
        return results
    
    def get_available_exchanges(self, exchange_type: str = None) -> List[str]:
        """
        Get list of available exchanges
        
        Args:
            exchange_type: 'crypto', 'forex', or None for all
            
        Returns:
            List of available exchange names
        """
        available = []
        
        for name, exchange_info in self.exchanges.items():
            if not exchange_info.enabled or not exchange_info.connected:
                continue
                
            if exchange_type is None or exchange_info.type == exchange_type:
                available.append(name)
        
        return available
    
    def get_exchange_client(self, exchange_name: str) -> Optional[Union[ExchangeClient, MT5Client]]:
        """Get exchange client by name"""
        exchange_info = self.exchanges.get(exchange_name)
        if exchange_info and exchange_info.enabled and exchange_info.connected:
            return exchange_info.client
        return None
    
    def get_best_exchange_for_symbol(self, symbol: str) -> Optional[str]:
        """
        Determine the best exchange for a given symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Best exchange name or None
        """
        # Crypto symbols (contain USDT, BTC, ETH, etc.)
        crypto_indicators = ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD', 'USDC']
        if any(indicator in symbol.upper() for indicator in crypto_indicators):
            # Prefer Binance for crypto, fallback to MEXC
            for exchange in ['binance', 'mexc']:
                if exchange in self.exchanges and self.exchanges[exchange].connected:
                    return exchange
        
        # Forex symbols (like EURUSD, GBPUSD, etc.)
        forex_indicators = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'NZD']
        if any(symbol.upper().startswith(fx) or symbol.upper().endswith(fx) for fx in forex_indicators):
            if 'mt5' in self.exchanges and self.exchanges['mt5'].connected:
                return 'mt5'
        
        # Default to first available exchange
        available = self.get_available_exchanges()
        return available[0] if available else None
    
    async def fetch_ticker(self, symbol: str, exchange: str = None) -> Optional[UnifiedTicker]:
        """
        Fetch ticker from specified exchange or auto-select best exchange
        
        Args:
            symbol: Trading symbol
            exchange: Specific exchange name (optional)
            
        Returns:
            UnifiedTicker object or None
        """
        if exchange is None:
            exchange = self.get_best_exchange_for_symbol(symbol)
        
        if exchange is None:
            logger.error(f"No available exchange for symbol {symbol}")
            return None
        
        client = self.get_exchange_client(exchange)
        if client is None:
            logger.error(f"Exchange {exchange} not available")
            return None
        
        try:
            if isinstance(client, MT5Client):
                ticker_info = await client.fetch_ticker(symbol)
                if ticker_info:
                    return UnifiedTicker(
                        symbol=symbol,
                        exchange=exchange,
                        bid=ticker_info.bid,
                        ask=ticker_info.ask,
                        last=ticker_info.last,
                        volume=ticker_info.volume,
                        timestamp=ticker_info.time
                    )
            else:
                ticker_data = await client.fetch_ticker(symbol)
                if ticker_data:
                    return UnifiedTicker(
                        symbol=symbol,
                        exchange=exchange,
                        bid=ticker_data.get('bid', 0),
                        ask=ticker_data.get('ask', 0),
                        last=ticker_data.get('last', 0),
                        volume=ticker_data.get('baseVolume', 0),
                        change_24h=ticker_data.get('percentage'),
                        timestamp=datetime.fromtimestamp(ticker_data.get('timestamp', 0) / 1000) if ticker_data.get('timestamp') else datetime.now()
                    )
        
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol} from {exchange}: {e}")
        
        return None
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100, 
                         exchange: str = None) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from specified exchange or auto-select best exchange
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1h, 4h, 1d, etc.)
            limit: Number of candles
            exchange: Specific exchange name (optional)
            
        Returns:
            DataFrame with OHLCV data or None
        """
        if exchange is None:
            exchange = self.get_best_exchange_for_symbol(symbol)
        
        if exchange is None:
            logger.error(f"No available exchange for symbol {symbol}")
            return None
        
        client = self.get_exchange_client(exchange)
        if client is None:
            logger.error(f"Exchange {exchange} not available")
            return None
        
        try:
            if isinstance(client, MT5Client):
                # Convert common timeframes to MT5 format
                mt5_timeframes = {
                    '1m': 'M1', '5m': 'M5', '15m': 'M15', '30m': 'M30',
                    '1h': 'H1', '4h': 'H4', '1d': 'D1', '1w': 'W1'
                }
                mt5_tf = mt5_timeframes.get(timeframe, 'H1')
                return await client.fetch_ohlcv(symbol, mt5_tf, limit)
            else:
                return await client.fetch_ohlcv(symbol, timeframe, limit)
        
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol} from {exchange}: {e}")
        
        return None
    
    async def place_market_order(self, symbol: str, side: str, amount: float, 
                               exchange: str = None) -> Optional[UnifiedOrderResult]:
        """
        Place market order on specified exchange or auto-select best exchange
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            amount: Order amount
            exchange: Specific exchange name (optional)
            
        Returns:
            UnifiedOrderResult or None
        """
        if exchange is None:
            exchange = self.get_best_exchange_for_symbol(symbol)
        
        if exchange is None:
            logger.error(f"No available exchange for symbol {symbol}")
            return None
        
        client = self.get_exchange_client(exchange)
        if client is None:
            logger.error(f"Exchange {exchange} not available")
            return None
        
        try:
            if isinstance(client, MT5Client):
                result = await client.place_market_order(symbol, side, amount)
                return UnifiedOrderResult(
                    success=result.success,
                    exchange=exchange,
                    order_id=str(result.order_id) if result.order_id else None,
                    symbol=result.symbol,
                    side=result.side,
                    amount=result.volume,
                    price=result.price,
                    cost=result.volume * result.price,
                    timestamp=datetime.now(),
                    error_message=result.error_message,
                    metadata=result.metadata
                )
            else:
                result = await client.place_market_order(symbol, side, amount)
                return UnifiedOrderResult(
                    success=result.success,
                    exchange=exchange,
                    order_id=result.order_id,
                    symbol=result.symbol,
                    side=result.side,
                    amount=result.amount,
                    price=result.price,
                    cost=result.cost,
                    timestamp=datetime.now(),
                    error_message=result.error_message,
                    metadata=result.metadata
                )
        
        except Exception as e:
            logger.error(f"Error placing market order for {symbol} on {exchange}: {e}")
            return UnifiedOrderResult(
                success=False,
                exchange=exchange,
                symbol=symbol,
                side=side,
                amount=amount,
                error_message=str(e)
            )
    
    async def get_account_balance(self, exchange: str = None) -> Dict[str, Any]:
        """
        Get account balance from specified exchange or all exchanges
        
        Args:
            exchange: Specific exchange name (optional, gets all if None)
            
        Returns:
            Dictionary with balance information
        """
        if exchange:
            client = self.get_exchange_client(exchange)
            if client is None:
                return {}
            
            try:
                if isinstance(client, MT5Client):
                    balance = await client.fetch_balance()
                    return {exchange: balance} if balance else {}
                else:
                    balance = await client.fetch_balance()
                    return {exchange: {
                        'total': balance.total,
                        'free': balance.free,
                        'used': balance.used,
                        'timestamp': balance.timestamp
                    }} if balance else {}
            except Exception as e:
                logger.error(f"Error fetching balance from {exchange}: {e}")
                return {}
        
        # Get balances from all exchanges
        all_balances = {}
        for name, exchange_info in self.exchanges.items():
            if exchange_info.enabled and exchange_info.connected and exchange_info.client:
                try:
                    if isinstance(exchange_info.client, MT5Client):
                        balance = await exchange_info.client.fetch_balance()
                        if balance:
                            all_balances[name] = balance
                    else:
                        balance = await exchange_info.client.fetch_balance()
                        if balance:
                            all_balances[name] = {
                                'total': balance.total,
                                'free': balance.free,
                                'used': balance.used,
                                'timestamp': balance.timestamp
                            }
                except Exception as e:
                    logger.error(f"Error fetching balance from {name}: {e}")
        
        return all_balances
    
    def get_exchange_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all exchanges"""
        status = {}
        
        for name, exchange_info in self.exchanges.items():
            status[name] = {
                'enabled': exchange_info.enabled,
                'connected': exchange_info.connected,
                'type': exchange_info.type,
                'last_error': exchange_info.last_error
            }
        
        return status
    
    async def shutdown_all(self):
        """Shutdown all exchange connections"""
        for name, exchange_info in self.exchanges.items():
            if exchange_info.client and isinstance(exchange_info.client, MT5Client):
                try:
                    exchange_info.client.shutdown()
                    logger.info(f"Shutdown {name} connection")
                except Exception as e:
                    logger.error(f"Error shutting down {name}: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        # Note: This needs to be called explicitly in async context
        # asyncio.create_task(self.shutdown_all()) 