# import os
# import logging
# from binance.client import Client
# from binance.exceptions import BinanceAPIException
# import pandas as pd
# from datetime import datetime
# import matplotlib.pyplot as plt
# import io
# from src.trading.strategies.legacy_strategies import get_strategy
# from src.trading.indicators.legacy_indicators import IndicatorFactory
# import ccxt
# import numpy as np

# logger = logging.getLogger('trading')

# class TradingBot:
#     def __init__(self):
#         api_key = os.getenv('BINANCE_API_KEY')
#         api_secret = os.getenv('BINANCE_API_SECRET')
        
#         # Log API key status (safely)
#         if api_key:
#             masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****'
#             logger.info(f"API Key loaded: {masked_key}")
#         else:
#             logger.error("Binance API Key not found in environment variables")
        
#         if api_secret:
#             logger.info("API Secret loaded (value hidden)")
#         else:
#             logger.error("Binance API Secret not found in environment variables")
        
#         # Initialize with demo mode if no API credentials
#         self.demo_mode = False
#         if not api_key or not api_secret:
#             logger.warning("No Binance API credentials found. Running in demo mode.")
#             self.demo_mode = True
#             self.client = Client("", "")  # Use empty strings for demo mode
#             self.ccxt_client = None
#         else:
#             self.client = Client(api_key, api_secret)
#             # Initialize CCXT for multi-exchange support
#             try:
#                 self.ccxt_client = ccxt.binance({
#                     'apiKey': api_key,
#                     'secret': api_secret,
#                     'enableRateLimit': True,  # Enable rate limiting
#                 })
#                 logger.info("CCXT client initialized for Binance")
#             except Exception as e:
#                 logger.error(f"Failed to initialize CCXT client: {e}")
#                 self.ccxt_client = None
            
#         self.active_strategies = {}
#         self.signals = []  # Store signals
        
#         # Risk management settings
#         self.max_risk_per_trade = 0.02  # 2% risk per trade
#         self.max_daily_loss = 0.05  # 5% max daily loss
#         self.trailing_stop_percent = 0.015  # 1.5% trailing stop
#         self.daily_loss_counter = 0.0  # Track daily loss
#         self.last_reset_day = datetime.now().day
        
#         # Price cache to prevent duplicate API calls
#         self.price_cache = {}
#         self.price_cache_ttl = 5  # Cache prices for 5 seconds
        
#         logger.info("Trading bot initialized")
    
#     def reset_daily_loss(self):
#         """Reset daily loss counter if it's a new day"""
#         current_day = datetime.now().day
#         if current_day != self.last_reset_day:
#             self.daily_loss_counter = 0.0
#             self.last_reset_day = current_day
#             logger.info("Daily loss counter reset")
    
#     def update_risk_parameters(self, max_risk_per_trade=None, max_daily_loss=None, trailing_stop_percent=None):
#         """Update risk management parameters"""
#         if max_risk_per_trade is not None:
#             self.max_risk_per_trade = max_risk_per_trade
#             logger.info(f"Max risk per trade updated to {max_risk_per_trade * 100}%")
        
#         if max_daily_loss is not None:
#             self.max_daily_loss = max_daily_loss
#             logger.info(f"Max daily loss updated to {max_daily_loss * 100}%")
        
#         if trailing_stop_percent is not None:
#             self.trailing_stop_percent = trailing_stop_percent
#             logger.info(f"Trailing stop percent updated to {trailing_stop_percent * 100}%")
            
#     def get_account_balance(self, exchange='binance'):
#         """Get account balance for all assets with non-zero balance"""
#         self.reset_daily_loss()
        
#         if self.demo_mode:
#             logger.warning("Demo mode: Returning mock balance")
#             return [
#                 {"asset": "BTC", "free": "0.1", "locked": "0.0"},
#                 {"asset": "ETH", "free": "2.5", "locked": "0.0"},
#                 {"asset": "USDT", "free": "1000.0", "locked": "0.0"}
#             ]
        
#         try:
#             if exchange.lower() == 'binance' and self.client:
#                 account_info = self.client.get_account()
#                 balances = account_info['balances']
#                 non_zero = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
#                 return non_zero
#             elif self.ccxt_client:
#                 # Use CCXT for other exchanges or as fallback
#                 self.ccxt_client.load_markets()
#                 balance = self.ccxt_client.fetch_balance()
                
#                 # Format to match Binance API structure
#                 formatted_balances = []
#                 for currency, data in balance.items():
#                     if currency not in ['info', 'free', 'used', 'total'] and (data['free'] > 0 or data['used'] > 0):
#                         formatted_balances.append({
#                             'asset': currency,
#                             'free': str(data['free']),
#                             'locked': str(data['used'])
#                         })
#                 return formatted_balances
#             else:
#                 logger.error(f"Exchange {exchange} not supported or client not initialized")
#                 return None
#         except BinanceAPIException as e:
#             logger.error(f"Error getting account balance: {e}")
#             logger.error(f"Error code: {e.code}, Error message: {e.message}")
#             return None
#         except Exception as e:
#             logger.error(f"Unexpected error getting account balance: {str(e)}")
#             import traceback
#             logger.error(traceback.format_exc())
#             return None
    
#     def get_price(self, symbol, exchange='binance'):
#         """Get current price for a symbol"""
#         logger.info(f"get_price called for {symbol} on {exchange}")
        
#         # Check cache first to prevent duplicate API calls
#         cache_key = f"{symbol}_{exchange}"
#         now = datetime.now()
        
#         if cache_key in self.price_cache:
#             cached_price, cached_time = self.price_cache[cache_key]
#             if (now - cached_time).total_seconds() < self.price_cache_ttl:
#                 logger.info(f"Returning cached price for {symbol}: {cached_price}")
#                 return cached_price
        
#         try:
#             price = None
#             if exchange.lower() == 'binance' and self.client:
#                 ticker = self.client.get_symbol_ticker(symbol=symbol)
#                 price = ticker['price']
#                 logger.info(f"Price fetched for {symbol}: {price}")
#             elif self.ccxt_client:
#                 # Use CCXT for other exchanges or as fallback
#                 ticker = self.ccxt_client.fetch_ticker(symbol)
#                 price = str(ticker['last'])
#                 logger.info(f"Price fetched via CCXT for {symbol}: {price}")
#             else:
#                 logger.error(f"Exchange {exchange} not supported or client not initialized")
#                 return None
            
#             # Cache the price
#             if price:
#                 self.price_cache[cache_key] = (price, now)
#                 logger.debug(f"Cached price for {symbol}: {price}")
            
#             return price
            
#         except BinanceAPIException as e:
#             logger.error(f"Error getting price for {symbol}: {e}")
#             return None
#         except Exception as e:
#             logger.error(f"Error getting price for {symbol} via CCXT: {str(e)}")
#             return None
    
#     def get_market_data(self, symbol, interval, limit=100, exchange='binance'):
#         """Get historical market data"""
#         try:
#             if exchange.lower() == 'binance' and self.client:
#                 klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
#                 data = []
#                 for k in klines:
#                     data.append([
#                         datetime.fromtimestamp(k[0]/1000),  # Open time
#                         float(k[1]),  # Open
#                         float(k[2]),  # High
#                         float(k[3]),  # Low
#                         float(k[4]),  # Close
#                         float(k[5])   # Volume
#                     ])
#                 df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
#                 return df
#             elif self.ccxt_client:
#                 # Map interval to CCXT timeframe format
#                 timeframe_map = {
#                     '1m': '1m',
#                     '3m': '3m',
#                     '5m': '5m',
#                     '15m': '15m',
#                     '30m': '30m',
#                     '1h': '1h',
#                     '2h': '2h',
#                     '4h': '4h',
#                     '6h': '6h',
#                     '8h': '8h',
#                     '12h': '12h',
#                     '1d': '1d',
#                     '3d': '3d',
#                     '1w': '1w',
#                     '1M': '1M'
#                 }
                
#                 timeframe = timeframe_map.get(interval, '1h')
                
#                 # Fetch OHLCV data
#                 ohlcv = self.ccxt_client.fetch_ohlcv(symbol, timeframe, limit=limit)
                
#                 data = []
#                 for candle in ohlcv:
#                     data.append([
#                         datetime.fromtimestamp(candle[0]/1000),  # Timestamp
#                         float(candle[1]),  # Open
#                         float(candle[2]),  # High
#                         float(candle[3]),  # Low
#                         float(candle[4]),  # Close
#                         float(candle[5])   # Volume
#                     ])
                    
#                 df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
#                 return df
#             else:
#                 logger.error(f"Exchange {exchange} not supported or client not initialized")
#                 return None
#         except BinanceAPIException as e:
#             logger.error(f"Error getting market data for {symbol}: {e}")
#             return None
#         except Exception as e:
#             logger.error(f"Error getting market data for {symbol} via CCXT: {str(e)}")
#             import traceback
#             logger.error(traceback.format_exc())
#             return None 