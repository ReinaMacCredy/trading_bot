import os
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import io
from strategies import get_strategy

logger = logging.getLogger('trading')

class TradingBot:
    def __init__(self):
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not api_key or not api_secret:
            logger.error("Binance API credentials not found in environment variables")
            raise ValueError("Binance API credentials not configured")
            
        self.client = Client(api_key, api_secret)
        self.active_strategies = {}
        logger.info("Trading bot initialized")
        
    def get_account_balance(self):
        """Get account balance for all assets with non-zero balance"""
        try:
            account_info = self.client.get_account()
            balances = account_info['balances']
            non_zero = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
            return non_zero
        except BinanceAPIException as e:
            logger.error(f"Error getting account balance: {e}")
            return None
    
    def get_price(self, symbol):
        """Get current price for a symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return ticker['price']
        except BinanceAPIException as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_market_data(self, symbol, interval, limit=100):
        """Get historical market data"""
        try:
            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            data = []
            for k in klines:
                data.append([
                    datetime.fromtimestamp(k[0]/1000),  # Open time
                    float(k[1]),  # Open
                    float(k[2]),  # High
                    float(k[3]),  # Low
                    float(k[4]),  # Close
                    float(k[5])   # Volume
                ])
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return df
        except BinanceAPIException as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def generate_chart(self, symbol, interval, limit=100):
        """Generate a price chart for a symbol"""
        df = self.get_market_data(symbol, interval, limit)
        if df is None:
            return None
        
        plt.figure(figsize=(10, 5))
        plt.plot(df['timestamp'], df['close'])
        plt.title(f"{symbol} Price Chart ({interval})")
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        
        return buf
    
    def place_order(self, symbol, side, quantity):
        """Place a market order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            return order
        except BinanceAPIException as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def add_strategy(self, strategy_name, symbol, interval, **params):
        """Add a trading strategy to monitor"""
        try:
            strategy = get_strategy(strategy_name, **params)
            key = f"{strategy_name}_{symbol}_{interval}"
            self.active_strategies[key] = {
                "strategy": strategy,
                "symbol": symbol,
                "interval": interval
            }
            logger.info(f"Added strategy {strategy_name} for {symbol} ({interval})")
            return True
        except Exception as e:
            logger.error(f"Error adding strategy: {e}")
            return False
    
    def remove_strategy(self, strategy_name, symbol, interval):
        """Remove a trading strategy"""
        key = f"{strategy_name}_{symbol}_{interval}"
        if key in self.active_strategies:
            del self.active_strategies[key]
            logger.info(f"Removed strategy {strategy_name} for {symbol} ({interval})")
            return True
        return False
    
    def list_strategies(self):
        """List all active strategies"""
        result = []
        for key, data in self.active_strategies.items():
            result.append({
                "name": data["strategy"].name,
                "symbol": data["symbol"],
                "interval": data["interval"]
            })
        return result
    
    def analyze_symbol(self, strategy_name, symbol, interval, limit=100):
        """Analyze a symbol using a specific strategy"""
        try:
            # Get market data
            df = self.get_market_data(symbol, interval, limit)
            if df is None:
                return None
            
            # Get strategy
            strategy = get_strategy(strategy_name)
            
            # Analyze data
            signals = strategy.analyze(df)
            if signals is None:
                return None
            
            # Check for buy/sell signals
            last_signal = signals['signal'].iloc[-1]
            last_price = signals['close'].iloc[-1]
            
            result = {
                "strategy": strategy_name,
                "symbol": symbol,
                "current_price": last_price,
                "signal": "HOLD"
            }
            
            if last_signal == 1.0:
                result["signal"] = "BUY"
            elif last_signal == -1.0:
                result["signal"] = "SELL"
            
            # Add strategy-specific indicators
            if strategy_name.lower() == 'ma_crossover':
                result["short_ma"] = signals['short_ma'].iloc[-1]
                result["long_ma"] = signals['long_ma'].iloc[-1]
            elif strategy_name.lower() == 'rsi':
                result["rsi"] = signals['rsi'].iloc[-1]
            elif strategy_name.lower() == 'bollinger_bands':
                result["sma"] = signals['sma'].iloc[-1]
                result["upper_band"] = signals['upper_band'].iloc[-1]
                result["lower_band"] = signals['lower_band'].iloc[-1]
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing symbol: {e}")
            return None
    
    def generate_strategy_chart(self, strategy_name, symbol, interval, limit=100):
        """Generate a chart with strategy indicators"""
        try:
            # Get market data
            df = self.get_market_data(symbol, interval, limit)
            if df is None:
                return None
            
            # Get strategy
            strategy = get_strategy(strategy_name)
            
            # Analyze data
            signals = strategy.analyze(df)
            if signals is None:
                return None
            
            # Create chart
            plt.figure(figsize=(12, 8))
            
            # Plot price
            plt.subplot(2, 1, 1)
            plt.plot(signals['timestamp'], signals['close'], label='Price')
            
            # Add strategy-specific indicators
            if strategy_name.lower() == 'ma_crossover':
                plt.plot(signals['timestamp'], signals['short_ma'], label=f'Short MA ({strategy.short_window})')
                plt.plot(signals['timestamp'], signals['long_ma'], label=f'Long MA ({strategy.long_window})')
            elif strategy_name.lower() == 'bollinger_bands':
                plt.plot(signals['timestamp'], signals['sma'], label=f'SMA ({strategy.window})')
                plt.plot(signals['timestamp'], signals['upper_band'], label='Upper Band')
                plt.plot(signals['timestamp'], signals['lower_band'], label='Lower Band')
            
            plt.title(f"{symbol} Price with {strategy.name} ({interval})")
            plt.xlabel('Time')
            plt.ylabel('Price')
            plt.legend()
            plt.xticks(rotation=45)
            
            # Add additional plots for specific strategies
            if strategy_name.lower() == 'rsi':
                plt.subplot(2, 1, 2)
                plt.plot(signals['timestamp'], signals['rsi'], label='RSI')
                plt.axhline(y=strategy.oversold, color='g', linestyle='-', label=f'Oversold ({strategy.oversold})')
                plt.axhline(y=strategy.overbought, color='r', linestyle='-', label=f'Overbought ({strategy.overbought})')
                plt.title(f"RSI ({strategy.window})")
                plt.xlabel('Time')
                plt.ylabel('RSI')
                plt.legend()
                plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            
            return buf
        except Exception as e:
            logger.error(f"Error generating strategy chart: {e}")
            return None 