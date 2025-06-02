import os
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import io
from strategies import get_strategy
from indicators import IndicatorFactory

logger = logging.getLogger('trading')

class TradingBot:
    def __init__(self):
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        # Log API key status (safely)
        if api_key:
            masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****'
            logger.info(f"API Key loaded: {masked_key}")
        else:
            logger.error("Binance API Key not found in environment variables")
        
        if api_secret:
            logger.info("API Secret loaded (value hidden)")
        else:
            logger.error("Binance API Secret not found in environment variables")
        
        # Initialize with demo mode if no API credentials
        self.demo_mode = False
        if not api_key or not api_secret:
            logger.warning("No Binance API credentials found. Running in demo mode.")
            self.demo_mode = True
            self.client = Client("", "")  # Use empty strings for demo mode
        else:
            self.client = Client(api_key, api_secret)
            
        self.active_strategies = {}
        self.signals = []  # Store signals
        logger.info("Trading bot initialized")
        
    def get_account_balance(self):
        """Get account balance for all assets with non-zero balance"""
        if self.demo_mode:
            logger.warning("Demo mode: Returning mock balance")
            return [
                {"asset": "BTC", "free": "0.1", "locked": "0.0"},
                {"asset": "ETH", "free": "2.5", "locked": "0.0"},
                {"asset": "USDT", "free": "1000.0", "locked": "0.0"}
            ]
            
        try:
            account_info = self.client.get_account()
            balances = account_info['balances']
            non_zero = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
            return non_zero
        except BinanceAPIException as e:
            logger.error(f"Error getting account balance: {e}")
            logger.error(f"Error code: {e.code}, Error message: {e.message}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting account balance: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
        if self.demo_mode:
            logger.warning(f"Demo mode: Simulating {side} order for {quantity} {symbol}")
            price = self.get_price(symbol)
            return {
                "symbol": symbol,
                "orderId": 12345,
                "price": price,
                "origQty": str(quantity),
                "side": side,
                "status": "FILLED",
                "type": "MARKET",
                "transactTime": int(datetime.now().timestamp() * 1000)
            }
            
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
    
    def get_strategy(self, strategy_name, **params):
        """Get a strategy instance with the specified parameters"""
        try:
            return get_strategy(strategy_name, **params)
        except Exception as e:
            logger.error(f"Error getting strategy {strategy_name}: {e}")
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
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            
            return buf
        except Exception as e:
            logger.error(f"Error generating strategy chart: {e}")
            return None
    
    def get_indicator(self, indicator_name, **params):
        """Get an indicator instance with the specified parameters"""
        try:
            return IndicatorFactory.get_indicator(indicator_name, **params)
        except Exception as e:
            logger.error(f"Error getting indicator {indicator_name}: {e}")
            return None
    
    def analyze_with_indicator(self, indicator_name, symbol, interval, limit=100, **params):
        """Analyze a symbol using a specific indicator
        
        Args:
            indicator_name (str): Name of the indicator (e.g., 'rsi', 'macd', 'ema')
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            interval (str): Candlestick interval (e.g., '1h', '4h', '1d')
            limit (int): Number of data points
            **params: Parameters for the indicator
            
        Returns:
            dict: Analysis results
        """
        try:
            # Get market data
            df = self.get_market_data(symbol, interval, limit)
            if df is None:
                return None
            
            # Get indicator
            indicator = self.get_indicator(indicator_name, **params)
            if indicator is None:
                return None
            
            # Calculate indicator values
            indicator_data = indicator.calculate(df)
            if indicator_data is None:
                return None
            
            # Get signals
            signals = indicator.get_signal(df)
            if signals is None:
                signals = {}
                last_signal = 0
            else:
                last_signal = signals['signal'].iloc[-1] if 'signal' in signals else 0
            
            # Prepare result
            result = {
                "indicator": indicator_name,
                "symbol": symbol,
                "current_price": df['close'].iloc[-1],
                "signal": "HOLD"
            }
            
            if last_signal == 1.0:
                result["signal"] = "BUY"
            elif last_signal == -1.0:
                result["signal"] = "SELL"
            
            # Add indicator-specific data
            if indicator_name.lower() == 'ema':
                result["ema"] = float(indicator_data.iloc[-1])
            elif indicator_name.lower() == 'rsi':
                result["rsi"] = float(indicator_data.iloc[-1])
                result["oversold"] = indicator.oversold
                result["overbought"] = indicator.overbought
            elif indicator_name.lower() == 'macd':
                result["macd"] = float(indicator_data['macd'].iloc[-1])
                result["signal_line"] = float(indicator_data['signal_line'].iloc[-1])
                result["histogram"] = float(indicator_data['histogram'].iloc[-1])
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing with indicator: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_indicator_chart(self, indicator_name, symbol, interval, limit=100, **params):
        """Generate a chart with indicator visualization
        
        Args:
            indicator_name (str): Name of the indicator
            symbol (str): Trading symbol
            interval (str): Candlestick interval
            limit (int): Number of data points
            **params: Parameters for the indicator
            
        Returns:
            BytesIO: Chart image buffer
        """
        try:
            # Get market data
            df = self.get_market_data(symbol, interval, limit)
            if df is None:
                return None
            
            # Get indicator
            indicator = self.get_indicator(indicator_name, **params)
            if indicator is None:
                return None
            
            # Calculate indicator values
            indicator_data = indicator.calculate(df)
            if indicator_data is None:
                return None
            
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]})
            
            # Plot price on first subplot
            ax1.plot(df['timestamp'], df['close'])
            ax1.set_title(f"{symbol} Price Chart ({interval})")
            ax1.set_ylabel('Price')
            ax1.grid(True)
            
            # Plot indicator on second subplot
            if indicator_name.lower() == 'ema':
                ax2.plot(df['timestamp'], indicator_data, label=f"EMA-{indicator.period}")
                ax2.set_title(f"EMA ({indicator.period})")
            elif indicator_name.lower() == 'rsi':
                ax2.plot(df['timestamp'], indicator_data, label=f"RSI-{indicator.period}")
                ax2.axhline(y=indicator.oversold, color='g', linestyle='-', label=f"Oversold ({indicator.oversold})")
                ax2.axhline(y=indicator.overbought, color='r', linestyle='-', label=f"Overbought ({indicator.overbought})")
                ax2.set_title(f"RSI ({indicator.period})")
                ax2.set_ylim(0, 100)
            elif indicator_name.lower() == 'macd':
                ax2.plot(df['timestamp'], indicator_data['macd'], label='MACD Line')
                ax2.plot(df['timestamp'], indicator_data['signal_line'], label='Signal Line')
                ax2.bar(df['timestamp'], indicator_data['histogram'], label='Histogram', alpha=0.5)
                ax2.set_title(f"MACD ({indicator.fast_period}, {indicator.slow_period}, {indicator.signal_period})")
            
            ax2.set_xlabel('Time')
            ax2.grid(True)
            ax2.legend()
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)
            
            return buf
        except Exception as e:
            logger.error(f"Error generating indicator chart: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def test_connection(self):
        """Test connection to Binance API"""
        try:
            server_time = self.client.get_server_time()
            logger.info(f"Binance server time: {server_time}")
            return True
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return False
    
    def store_signal(self, signal):
        """Store a trading signal"""
        # Add timestamp to signal for additional tracking
        from datetime import datetime
        signal['timestamp'] = datetime.now().isoformat()
        
        # Enhanced duplicate detection - log all checks for better debugging
        symbol = signal.get('symbol', 'UNKNOWN')
        strategy = signal.get('strategy_code', 'UNKNOWN')
        
        # Check 1: Check if this exact signal already exists (exact match on key fields)
        for idx, existing in enumerate(self.signals):
            if (existing['symbol'] == signal['symbol'] and 
                existing['strategy_code'] == signal['strategy_code'] and
                existing['entry_price'] == signal['entry_price'] and
                existing['tp_price'] == signal['tp_price'] and
                existing['sl_price'] == signal['sl_price']):
                logger.info(f"Duplicate exact match signal detected for {symbol}-{strategy} at index {idx}, not storing")
                return False
        
        # Check 2: Check for signals with close price values (within 0.1% difference)
        for idx, existing in enumerate(self.signals):
            if (existing['symbol'] == signal['symbol'] and 
                existing['strategy_code'] == signal['strategy_code']):
                # Calculate price difference percentage
                entry_diff_pct = abs(float(existing['entry_price']) - float(signal['entry_price'])) / float(signal['entry_price']) * 100
                if entry_diff_pct < 0.1:  # If prices are within 0.1% of each other
                    logger.info(f"Near-duplicate signal detected for {symbol}-{strategy} at index {idx}, price difference: {entry_diff_pct:.3f}%, not storing")
                    return False
        
        # Check 3: Check for recent signals with same symbol and strategy (within 120 seconds - extended window)
        current_time = datetime.now()
        for idx, existing in enumerate(self.signals):
            if 'timestamp' in existing:
                try:
                    existing_time = datetime.fromisoformat(existing['timestamp'])
                    time_diff = (current_time - existing_time).total_seconds()
                    if (time_diff < 120 and
                        existing['symbol'] == signal['symbol'] and 
                        existing['strategy_code'] == signal['strategy_code']):
                        logger.info(f"Recent signal for {symbol}-{strategy} exists at index {idx} (generated {time_diff:.1f}s ago), not storing duplicate")
                        return False
                except (ValueError, TypeError) as e:
                    # Handle invalid timestamp format
                    logger.warning(f"Error parsing timestamp for signal {idx}: {e}")
        
        # Store the new signal
        self.signals.append(signal)
        logger.info(f"Stored NEW signal for {symbol}-{strategy} (total signals: {len(self.signals)})")
        
        # Print summary of all signals for debugging
        signal_list = [f"{s.get('symbol', '')}-{s.get('strategy_code', '')}" for s in self.signals]
        logger.info(f"Current signals in storage: {signal_list}")
        
        return True
    
    def get_signals(self, symbol=None):
        """Get stored trading signals, optionally filtered by symbol"""
        if symbol:
            return [s for s in self.signals if s['symbol'] == symbol]
        return self.signals
        
    def calculate_tp_sl(self, symbol, strategy_code, risk_reward_ratio=2.0):
        """
        Calculate take profit and stop loss levels based on current market conditions
        
        Args:
            symbol: Trading symbol (e.g. 'BTCUSDT')
            strategy_code: Strategy code for reference
            risk_reward_ratio: Risk/reward ratio (default: 2.0)
            
        Returns:
            dict with entry_price, tp_price, sl_price, and ratio
        """
        try:
            # Get current price and recent market data
            current_price = float(self.get_price(symbol))
            df = self.get_market_data(symbol, interval='4h', limit=20)
            
            if df is None or current_price is None:
                logger.error(f"Failed to get data for {symbol}")
                return None
            
            # Calculate average true range (ATR) for volatility
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.mean()
            
            # Calculate stop loss and take profit based on ATR
            sl_distance = atr * 1.5  # 1.5 times ATR for stop loss
            tp_distance = sl_distance * risk_reward_ratio  # Risk/reward ratio for take profit
            
            # Round to appropriate number of decimal places based on price
            precision = 2
            if current_price < 1:
                precision = 6
            elif current_price < 10:
                precision = 4
            elif current_price < 100:
                precision = 3
                
            # Format prices
            entry_price = round(current_price, precision)
            tp_price = round(current_price + tp_distance, precision)
            sl_price = round(current_price - sl_distance, precision)
            
            # Calculate percentage risk (entry to stop loss)
            risk_percentage = (entry_price - sl_price) / entry_price * 100
            
            return {
                "symbol": symbol.replace("USDT", ""),
                "strategy_code": strategy_code,
                "entry_price": entry_price,
                "tp_price": tp_price,
                "sl_price": sl_price,
                "ratio": round(risk_percentage, 2),
                "current_price": current_price
            }
            
        except Exception as e:
            logger.error(f"Error calculating TP/SL for {symbol}: {e}")
            return None
            
    def generate_trading_signal(self, symbol, strategy_code="SC01", risk_reward_ratio=2.0, author="Reina"):
        """
        Generate a complete trading signal for a symbol based on current market conditions
        
        Args:
            symbol: Trading symbol (e.g. 'BTC')
            strategy_code: Strategy code (e.g. 'SC01', 'SC02')
            risk_reward_ratio: Risk/reward ratio (default: 2.0)
            author: Author name for the signal
            
        Returns:
            dict with complete signal data
        """
        # Ensure symbol format
        if not symbol.endswith("USDT"):
            symbol = f"{symbol}USDT"
            
        # Calculate entry, TP, and SL prices
        levels = self.calculate_tp_sl(symbol, strategy_code, risk_reward_ratio)
        if not levels:
            return None
            
        # Create the signal
        sc_strategy = self.get_strategy('sc_signal', version="SC01", author=author)
        if not sc_strategy:
            return None
            
        # Determine if conditions are favorable for entry
        # Based on simple trend analysis
        df = self.get_market_data(symbol, interval='1h', limit=24)
        if df is None:
            return None
            
        # Check if current price is near support or resistance
        close_prices = df['close'].values
        current = close_prices[-1]
        
        # Simple trend detection
        trend_up = close_prices[-1] > close_prices[-12]
        
        # Status determination
        status = "takeprofit" if trend_up else "pending"
        
        # Imminent entry check (if price is within 0.5% of entry)
        current_to_entry_pct = abs(levels["current_price"] - levels["entry_price"]) / levels["entry_price"] * 100
        imminent = 1 if current_to_entry_pct < 0.5 else 0
        
        # Generate complete signal
        return sc_strategy.generate_signal(
            symbol=levels["symbol"],
            strategy_code=strategy_code,
            entry_price=levels["entry_price"],
            tp_price=levels["tp_price"],
            sl_price=levels["sl_price"],
            ratio=levels["ratio"],
            status=status,
            imminent=imminent
        )