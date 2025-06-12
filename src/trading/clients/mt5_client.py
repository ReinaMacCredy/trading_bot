"""
Custom MetaTrader 5 (MT5) Client Implementation
Provides MT5 integration for the Discord Trading Bot

Note: This requires MetaTrader5 Python package and MT5 terminal installed
Installation: pip install MetaTrader5
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import os

logger = logging.getLogger(__name__)

# MT5 package imports (optional dependency)
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    logger.info("MetaTrader5 package is available")
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 package not installed. Install with: pip install MetaTrader5")

@dataclass
class MT5OrderResult:
    """Container for MT5 order execution results"""
    success: bool
    order_id: Optional[int] = None
    ticket: Optional[int] = None
    symbol: str = ""
    side: str = ""
    volume: float = 0.0
    price: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    comment: str = ""
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

@dataclass
class MT5TickerInfo:
    """Container for MT5 ticker information"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    time: datetime
    spread: float
    
class MT5Client:
    """
    Professional MetaTrader 5 client implementation
    Provides forex and CFD trading capabilities
    """
    
    def __init__(self, config=None):
        self.config = config
        self.connected = False
        self.account_info = None
        self.symbols_info = {}
        
        # MT5 configuration from config
        if config and hasattr(config, 'exchanges') and hasattr(config.exchanges, 'mt5'):
            self.server = getattr(config.exchanges.mt5, 'server', 'MetaQuotes-Demo')
            self.path = getattr(config.exchanges.mt5, 'path', None)
            self.timeout = getattr(config.exchanges.mt5, 'timeout', 60)
            self.enabled = getattr(config.exchanges.mt5, 'enabled', False)
        else:
            self.server = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
            self.path = os.getenv('MT5_PATH', None)
            self.timeout = int(os.getenv('MT5_TIMEOUT', '60'))
            self.enabled = os.getenv('MT5_ENABLED', 'false').lower() == 'true'
        
        # Credentials from environment variables
        self.login = os.getenv('MT5_LOGIN')
        self.password = os.getenv('MT5_PASSWORD')
        
        if not MT5_AVAILABLE:
            logger.error("MT5 client cannot be initialized: MetaTrader5 package not available")
            return
            
        if not self.enabled:
            logger.info("MT5 client disabled in configuration")
            return
            
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize MT5 connection"""
        if not MT5_AVAILABLE:
            logger.error("Cannot initialize MT5: package not available")
            return False
            
        try:
            # Initialize MT5
            if not mt5.initialize(path=self.path, server=self.server, login=int(self.login) if self.login else None, password=self.password, timeout=self.timeout):
                error_code = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error_code}")
                return False
            
            # Get account info
            self.account_info = mt5.account_info()
            if self.account_info is None:
                logger.error("Failed to get MT5 account info")
                return False
                
            self.connected = True
            logger.info(f"MT5 connected successfully to account {self.account_info.login} on server {self.account_info.server}")
            
            # Load symbols info
            self._load_symbols_info()
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MT5 connection: {e}")
            return False
    
    def _load_symbols_info(self):
        """Load available symbols information"""
        try:
            symbols = mt5.symbols_get()
            if symbols:
                for symbol in symbols:
                    self.symbols_info[symbol.name] = {
                        'name': symbol.name,
                        'digits': symbol.digits,
                        'trade_calc_mode': symbol.trade_calc_mode,
                        'trade_mode': symbol.trade_mode,
                        'min_volume': symbol.volume_min,
                        'max_volume': symbol.volume_max,
                        'volume_step': symbol.volume_step,
                        'spread': symbol.spread,
                        'contract_size': symbol.trade_contract_size
                    }
                logger.info(f"Loaded {len(self.symbols_info)} MT5 symbols")
            else:
                logger.warning("No MT5 symbols loaded")
        except Exception as e:
            logger.error(f"Error loading MT5 symbols: {e}")
    
    def is_connected(self) -> bool:
        """Check if MT5 is connected"""
        return self.connected and MT5_AVAILABLE
    
    async def fetch_ticker(self, symbol: str) -> Optional[MT5TickerInfo]:
        """
        Fetch current ticker information for a symbol
        
        Args:
            symbol: MT5 symbol (e.g., 'EURUSD', 'GBPUSD')
            
        Returns:
            MT5TickerInfo object or None if error
        """
        if not self.is_connected():
            logger.error("MT5 not connected")
            return None
            
        try:
            # Get symbol tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Failed to get tick for {symbol}")
                return None
            
            return MT5TickerInfo(
                symbol=symbol,
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume,
                time=datetime.fromtimestamp(tick.time),
                spread=(tick.ask - tick.bid)
            )
            
        except Exception as e:
            logger.error(f"Error fetching MT5 ticker for {symbol}: {e}")
            return None
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = 'H1', limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a symbol
        
        Args:
            symbol: MT5 symbol
            timeframe: MT5 timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
            limit: Number of bars to fetch
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        if not self.is_connected():
            logger.error("MT5 not connected")
            return None
            
        try:
            # Map timeframe string to MT5 constant
            timeframe_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1,
                'W1': mt5.TIMEFRAME_W1,
                'MN1': mt5.TIMEFRAME_MN1
            }
            
            tf = timeframe_map.get(timeframe.upper(), mt5.TIMEFRAME_H1)
            
            # Get rates
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, limit)
            if rates is None or len(rates) == 0:
                logger.error(f"No OHLCV data returned for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.rename(columns={
                'time': 'timestamp',
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume'
            }, inplace=True)
            df.set_index('timestamp', inplace=True)
            
            logger.debug(f"Fetched {len(df)} bars for {symbol} ({timeframe})")
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error fetching MT5 OHLCV for {symbol}: {e}")
            return None
    
    async def fetch_balance(self) -> Optional[Dict]:
        """
        Fetch account balance information
        
        Returns:
            Account balance dictionary or None if error
        """
        if not self.is_connected():
            logger.error("MT5 not connected")
            return None
            
        try:
            account = mt5.account_info()
            if account is None:
                logger.error("Failed to get MT5 account info")
                return None
            
            return {
                'balance': account.balance,
                'equity': account.equity,
                'margin': account.margin,
                'free_margin': account.margin_free,
                'margin_level': account.margin_level,
                'profit': account.profit,
                'currency': account.currency,
                'leverage': account.leverage,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error fetching MT5 balance: {e}")
            return None
    
    async def place_market_order(self, symbol: str, side: str, volume: float, 
                               sl: float = 0.0, tp: float = 0.0, comment: str = "Discord Bot") -> MT5OrderResult:
        """
        Place a market order
        
        Args:
            symbol: MT5 symbol
            side: 'buy' or 'sell'
            volume: Order volume (lots)
            sl: Stop loss price (optional)
            tp: Take profit price (optional)
            comment: Order comment
            
        Returns:
            MT5OrderResult with execution details
        """
        if not self.is_connected():
            return MT5OrderResult(
                success=False,
                error_message="MT5 not connected"
            )
            
        try:
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return MT5OrderResult(
                    success=False,
                    symbol=symbol,
                    side=side,
                    volume=volume,
                    error_message=f"Failed to get price for {symbol}"
                )
            
            # Determine order type and price
            if side.lower() == 'buy':
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            if result is None:
                error = mt5.last_error()
                return MT5OrderResult(
                    success=False,
                    symbol=symbol,
                    side=side,
                    volume=volume,
                    error_code=error[0] if error else None,
                    error_message=error[1] if error else "Unknown error"
                )
            
            # Check result
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return MT5OrderResult(
                    success=True,
                    order_id=result.order,
                    ticket=result.deal,
                    symbol=symbol,
                    side=side,
                    volume=result.volume,
                    price=result.price,
                    sl=sl,
                    tp=tp,
                    comment=comment,
                    metadata=dict(result._asdict())
                )
            else:
                return MT5OrderResult(
                    success=False,
                    symbol=symbol,
                    side=side,
                    volume=volume,
                    error_code=result.retcode,
                    error_message=result.comment,
                    metadata=dict(result._asdict())
                )
                
        except Exception as e:
            logger.error(f"Error placing MT5 market order: {e}")
            return MT5OrderResult(
                success=False,
                symbol=symbol,
                side=side,
                volume=volume,
                error_message=str(e)
            )
    
    async def place_pending_order(self, symbol: str, side: str, volume: float, price: float,
                                sl: float = 0.0, tp: float = 0.0, comment: str = "Discord Bot") -> MT5OrderResult:
        """
        Place a pending order (limit/stop)
        
        Args:
            symbol: MT5 symbol
            side: 'buy_limit', 'sell_limit', 'buy_stop', 'sell_stop'
            volume: Order volume (lots)
            price: Order price
            sl: Stop loss price (optional)
            tp: Take profit price (optional)
            comment: Order comment
            
        Returns:
            MT5OrderResult with execution details
        """
        if not self.is_connected():
            return MT5OrderResult(
                success=False,
                error_message="MT5 not connected"
            )
            
        try:
            # Map order types
            order_type_map = {
                'buy_limit': mt5.ORDER_TYPE_BUY_LIMIT,
                'sell_limit': mt5.ORDER_TYPE_SELL_LIMIT,
                'buy_stop': mt5.ORDER_TYPE_BUY_STOP,
                'sell_stop': mt5.ORDER_TYPE_SELL_STOP
            }
            
            order_type = order_type_map.get(side.lower())
            if order_type is None:
                return MT5OrderResult(
                    success=False,
                    symbol=symbol,
                    side=side,
                    volume=volume,
                    price=price,
                    error_message=f"Invalid order type: {side}"
                )
            
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
            }
            
            # Send order
            result = mt5.order_send(request)
            if result is None:
                error = mt5.last_error()
                return MT5OrderResult(
                    success=False,
                    symbol=symbol,
                    side=side,
                    volume=volume,
                    price=price,
                    error_code=error[0] if error else None,
                    error_message=error[1] if error else "Unknown error"
                )
            
            # Check result
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return MT5OrderResult(
                    success=True,
                    order_id=result.order,
                    symbol=symbol,
                    side=side,
                    volume=result.volume,
                    price=price,
                    sl=sl,
                    tp=tp,
                    comment=comment,
                    metadata=dict(result._asdict())
                )
            else:
                return MT5OrderResult(
                    success=False,
                    symbol=symbol,
                    side=side,
                    volume=volume,
                    price=price,
                    error_code=result.retcode,
                    error_message=result.comment,
                    metadata=dict(result._asdict())
                )
                
        except Exception as e:
            logger.error(f"Error placing MT5 pending order: {e}")
            return MT5OrderResult(
                success=False,
                symbol=symbol,
                side=side,
                volume=volume,
                price=price,
                error_message=str(e)
            )
    
    async def fetch_open_orders(self, symbol: str = None) -> List[Dict]:
        """
        Fetch open orders
        
        Args:
            symbol: MT5 symbol (optional, fetches all if None)
            
        Returns:
            List of open orders
        """
        if not self.is_connected():
            logger.error("MT5 not connected")
            return []
            
        try:
            orders = mt5.orders_get(symbol=symbol)
            if orders is None:
                return []
            
            order_list = []
            for order in orders:
                order_list.append({
                    'ticket': order.ticket,
                    'symbol': order.symbol,
                    'type': order.type,
                    'volume': order.volume_current,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'time_setup': datetime.fromtimestamp(order.time_setup),
                    'comment': order.comment
                })
            
            return order_list
            
        except Exception as e:
            logger.error(f"Error fetching MT5 open orders: {e}")
            return []
    
    async def fetch_positions(self, symbol: str = None) -> List[Dict]:
        """
        Fetch open positions
        
        Args:
            symbol: MT5 symbol (optional, fetches all if None)
            
        Returns:
            List of open positions
        """
        if not self.is_connected():
            logger.error("MT5 not connected")
            return []
            
        try:
            positions = mt5.positions_get(symbol=symbol)
            if positions is None:
                return []
            
            position_list = []
            for position in positions:
                position_list.append({
                    'ticket': position.ticket,
                    'symbol': position.symbol,
                    'type': position.type,
                    'volume': position.volume,
                    'price_open': position.price_open,
                    'sl': position.sl,
                    'tp': position.tp,
                    'profit': position.profit,
                    'time': datetime.fromtimestamp(position.time),
                    'comment': position.comment
                })
            
            return position_list
            
        except Exception as e:
            logger.error(f"Error fetching MT5 positions: {e}")
            return []
    
    async def close_position(self, ticket: int, volume: float = None) -> MT5OrderResult:
        """
        Close an open position
        
        Args:
            ticket: Position ticket
            volume: Volume to close (None for full position)
            
        Returns:
            MT5OrderResult with execution details
        """
        if not self.is_connected():
            return MT5OrderResult(
                success=False,
                error_message="MT5 not connected"
            )
            
        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return MT5OrderResult(
                    success=False,
                    error_message=f"Position {ticket} not found"
                )
            
            position = position[0]
            close_volume = volume or position.volume
            
            # Get current price
            tick = mt5.symbol_info_tick(position.symbol)
            if tick is None:
                return MT5OrderResult(
                    success=False,
                    error_message=f"Failed to get price for {position.symbol}"
                )
            
            # Determine close order type and price
            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": close_volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "comment": f"Close position {ticket}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            result = mt5.order_send(request)
            if result is None:
                error = mt5.last_error()
                return MT5OrderResult(
                    success=False,
                    error_code=error[0] if error else None,
                    error_message=error[1] if error else "Unknown error"
                )
            
            # Check result
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return MT5OrderResult(
                    success=True,
                    order_id=result.order,
                    ticket=result.deal,
                    symbol=position.symbol,
                    volume=result.volume,
                    price=result.price,
                    metadata=dict(result._asdict())
                )
            else:
                return MT5OrderResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=result.comment,
                    metadata=dict(result._asdict())
                )
                
        except Exception as e:
            logger.error(f"Error closing MT5 position {ticket}: {e}")
            return MT5OrderResult(
                success=False,
                error_message=str(e)
            )
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information"""
        return self.symbols_info.get(symbol)
    
    def list_symbols(self) -> List[str]:
        """List available symbols"""
        return list(self.symbols_info.keys())
    
    async def test_connection(self) -> bool:
        """Test MT5 connection"""
        try:
            if not self.is_connected():
                return False
            
            # Try to get account info
            account = mt5.account_info()
            return account is not None
            
        except Exception as e:
            logger.error(f"MT5 connection test failed: {e}")
            return False
    
    def shutdown(self):
        """Shutdown MT5 connection"""
        try:
            if MT5_AVAILABLE and self.connected:
                mt5.shutdown()
                self.connected = False
                logger.info("MT5 connection closed")
        except Exception as e:
            logger.error(f"Error shutting down MT5: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.shutdown() 