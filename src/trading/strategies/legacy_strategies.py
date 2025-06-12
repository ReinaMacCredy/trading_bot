import pandas as pd
import numpy as np
import logging
import pandas_ta as ta

logger = logging.getLogger('strategies')

class TradingStrategy:
    """Base class for trading strategies"""
    def __init__(self, name):
        self.name = name
        
    def analyze(self, data):
        """Analyze market data and generate signals"""
        raise NotImplementedError("Subclasses must implement analyze()")

class MovingAverageCrossover(TradingStrategy):
    """Simple moving average crossover strategy"""
    def __init__(self, short_window=20, long_window=50):
        super().__init__("MA Crossover")
        self.short_window = short_window
        self.long_window = long_window
        logger.info(f"Initialized {self.name} strategy with short_window={short_window}, long_window={long_window}")
        
    def analyze(self, data):
        """
        Generate trading signals based on moving average crossovers
        
        Returns:
            DataFrame with columns:
            - 'short_ma': Short-term moving average
            - 'long_ma': Long-term moving average
            - 'signal': 1 (buy), -1 (sell), or 0 (hold)
        """
        if len(data) < self.long_window:
            logger.warning(f"Not enough data for {self.name} strategy. Need at least {self.long_window} data points.")
            return None
            
        # Create a copy of the data
        signals = data.copy()
        
        # Calculate moving averages
        signals['short_ma'] = signals['close'].rolling(window=self.short_window, min_periods=1).mean()
        signals['long_ma'] = signals['close'].rolling(window=self.long_window, min_periods=1).mean()
        
        # Generate signals
        signals['signal'] = 0.0
        signals['signal'][self.short_window:] = np.where(
            signals['short_ma'][self.short_window:] > signals['long_ma'][self.short_window:], 1.0, 0.0)
        
        # Generate trading orders
        signals['position'] = signals['signal'].diff()
        
        return signals

class RSIStrategy(TradingStrategy):
    """Relative Strength Index (RSI) strategy"""
    def __init__(self, window=14, oversold=30, overbought=70):
        super().__init__("RSI")
        self.window = window
        self.oversold = oversold
        self.overbought = overbought
        logger.info(f"Initialized {self.name} strategy with window={window}, oversold={oversold}, overbought={overbought}")
        
    def calculate_rsi(self, data):
        """Calculate RSI indicator"""
        return ta.rsi(data, length=self.window)
        
    def analyze(self, data):
        """
        Generate trading signals based on RSI
        
        Returns:
            DataFrame with columns:
            - 'rsi': RSI values
            - 'signal': 1 (buy), -1 (sell), or 0 (hold)
        """
        if len(data) < self.window:
            logger.warning(f"Not enough data for {self.name} strategy. Need at least {self.window} data points.")
            return None
            
        # Create a copy of the data
        signals = data.copy()
        
        # Calculate RSI
        signals['rsi'] = self.calculate_rsi(signals['close'])
        
        # Generate signals
        signals['signal'] = 0.0
        signals['signal'] = np.where(signals['rsi'] < self.oversold, 1.0, 0.0)  # Buy when oversold
        signals['signal'] = np.where(signals['rsi'] > self.overbought, -1.0, signals['signal'])  # Sell when overbought
        
        return signals

class BollingerBandsStrategy(TradingStrategy):
    """Bollinger Bands strategy"""
    def __init__(self, window=20, num_std=2):
        super().__init__("Bollinger Bands")
        self.window = window
        self.num_std = num_std
        logger.info(f"Initialized {self.name} strategy with window={window}, num_std={num_std}")
        
    def analyze(self, data):
        """
        Generate trading signals based on Bollinger Bands
        
        Returns:
            DataFrame with columns:
            - 'sma': Simple moving average
            - 'upper_band': Upper Bollinger Band
            - 'lower_band': Lower Bollinger Band
            - 'signal': 1 (buy), -1 (sell), or 0 (hold)
        """
        if len(data) < self.window:
            logger.warning(f"Not enough data for {self.name} strategy. Need at least {self.window} data points.")
            return None
            
        # Create a copy of the data
        signals = data.copy()
        
        # Calculate Bollinger Bands
        bbands = ta.bbands(signals['close'], length=self.window, std=self.num_std)
        signals['sma'] = bbands['BBM_' + str(self.window) + '_' + str(self.num_std) + '.0']
        signals['upper_band'] = bbands['BBU_' + str(self.window) + '_' + str(self.num_std) + '.0']
        signals['lower_band'] = bbands['BBL_' + str(self.window) + '_' + str(self.num_std) + '.0']
        
        # Generate signals
        signals['signal'] = 0.0
        signals['signal'] = np.where(signals['close'] < signals['lower_band'], 1.0, 0.0)  # Buy when price below lower band
        signals['signal'] = np.where(signals['close'] > signals['upper_band'], -1.0, signals['signal'])  # Sell when price above upper band
        
        return signals

class MACDRSIStrategy(TradingStrategy):
    """Combined MACD and RSI strategy with dual timeframe confirmation"""
    
    def __init__(self, rsi_period=14, fast_period=12, slow_period=26, signal_period=9, 
                 oversold=30, overbought=70, use_higher_timeframe=True):
        super().__init__("MACD+RSI Dual Timeframe")
        self.rsi_period = rsi_period
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.oversold = oversold
        self.overbought = overbought
        self.use_higher_timeframe = use_higher_timeframe
        logger.info(f"Initialized {self.name} strategy with RSI period={rsi_period}, MACD parameters={fast_period}-{slow_period}-{signal_period}")
    
    def calculate_indicators(self, data):
        """Calculate MACD and RSI values for a dataframe
        
        Args:
            data (DataFrame): Price data with 'close' column
            
        Returns:
            DataFrame: DataFrame with indicator values added
        """
        if 'close' not in data.columns:
            logger.error("DataFrame must contain 'close' column")
            return None
            
        if len(data) < max(self.slow_period + self.signal_period, self.rsi_period):
            logger.warning(f"Not enough data for {self.name}. Need at least {max(self.slow_period + self.signal_period, self.rsi_period)} data points.")
            return None
            
        result = data.copy()
        
        # Calculate RSI using pandas-ta
        result['rsi'] = ta.rsi(result['close'], length=self.rsi_period)
        
        # Calculate MACD using pandas-ta
        macd = ta.macd(result['close'], fast=self.fast_period, slow=self.slow_period, signal=self.signal_period)
        
        # Add MACD columns to result
        result['macd'] = macd['MACD_' + str(self.fast_period) + '_' + str(self.slow_period) + '_' + str(self.signal_period)]
        result['signal_line'] = macd['MACDs_' + str(self.fast_period) + '_' + str(self.slow_period) + '_' + str(self.signal_period)]
        result['histogram'] = macd['MACDh_' + str(self.fast_period) + '_' + str(self.slow_period) + '_' + str(self.signal_period)]
        
        return result
    
    def analyze(self, data, higher_tf_data=None):
        """
        Generate trading signals based on MACD and RSI with dual timeframe confirmation
        
        Args:
            data (DataFrame): Main timeframe price data
            higher_tf_data (DataFrame): Optional higher timeframe data for confirmation
            
        Returns:
            DataFrame with indicator values and signals
        """
        # Calculate indicators for current timeframe
        result = self.calculate_indicators(data)
        if result is None:
            return None
            
        # Generate base signals
        result['signal'] = 0.0
        
        # Buy conditions:
        # 1. RSI is oversold or close to it
        # 2. MACD line crosses above signal line
        buy_condition = (
            (result['rsi'] < self.oversold + 5) &
            (result['macd'] > result['signal_line']) &
            (result['macd'].shift(1) <= result['signal_line'].shift(1))
        )
        
        # Sell conditions:
        # 1. RSI is overbought or close to it
        # 2. MACD line crosses below signal line
        sell_condition = (
            (result['rsi'] > self.overbought - 5) &
            (result['macd'] < result['signal_line']) &
            (result['macd'].shift(1) >= result['signal_line'].shift(1))
        )
        
        # Apply signals
        result['signal'] = np.where(buy_condition, 1.0, result['signal'])
        result['signal'] = np.where(sell_condition, -1.0, result['signal'])
        
        # Apply higher timeframe confirmation if provided and enabled
        if self.use_higher_timeframe and higher_tf_data is not None:
            higher_tf_result = self.calculate_indicators(higher_tf_data)
            
            if higher_tf_result is not None:
                # Get the trend from higher timeframe
                higher_tf_trend = higher_tf_result['macd'].iloc[-1] > higher_tf_result['signal_line'].iloc[-1]
                result['higher_tf_bullish'] = higher_tf_trend
                
                # Filter signals based on higher timeframe trend
                # Only keep buy signals if higher timeframe is bullish
                # Only keep sell signals if higher timeframe is bearish
                for i in range(len(result)):
                    if result['signal'].iloc[i] == 1.0 and not higher_tf_trend:
                        result.at[result.index[i], 'signal'] = 0.0
                    elif result['signal'].iloc[i] == -1.0 and higher_tf_trend:
                        result.at[result.index[i], 'signal'] = 0.0
        
        return result

class SCStrategySignal(TradingStrategy):
    """Strategic Crypto (SC) signal strategy as shown in the example"""
    def __init__(self, version="SC01", author="Reina"):
        super().__init__(f"{version} trading signals")
        self.version = version
        self.author = author
        logger.info(f"Initialized {self.name} strategy")
    
    def generate_signal(self, symbol, strategy_code, entry_price, tp_price, sl_price, 
                       ratio="0.0%", status="takeprofit", imminent=1):
        """Generate a trading signal with the given parameters"""
        logger.info(f"Generating {self.name} signal for {symbol}")
        return {
            'symbol': symbol,
            'strategy_code': strategy_code,
            'entry_price': entry_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'ratio': ratio,
            'status': status,
            'imminent': imminent,
            'author': self.author,
            'timestamp': pd.Timestamp.now()
        }
    
    def analyze(self, data):
        """This strategy doesn't analyze data; it only generates signals from manual input"""
        logger.warning(f"{self.name} doesn't analyze data. Use generate_signal() instead.")
        return None

def get_strategy(strategy_name, **kwargs):
    """Factory function to get a strategy instance"""
    strategies = {
        'ma_crossover': MovingAverageCrossover,
        'rsi': RSIStrategy,
        'bollinger_bands': BollingerBandsStrategy,
        'macd_rsi': MACDRSIStrategy,
        'sc_signal': SCStrategySignal
    }
    
    if strategy_name not in strategies:
        logger.error(f"Strategy '{strategy_name}' not found")
        return None
    
    return strategies[strategy_name](**kwargs) 