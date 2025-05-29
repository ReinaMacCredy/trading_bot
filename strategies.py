import pandas as pd
import numpy as np
import logging

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
        delta = data.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        
        ema_up = up.ewm(com=self.window-1, adjust=False).mean()
        ema_down = down.ewm(com=self.window-1, adjust=False).mean()
        
        rs = ema_up / ema_down
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
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
        signals['sma'] = signals['close'].rolling(window=self.window, min_periods=1).mean()
        signals['std'] = signals['close'].rolling(window=self.window, min_periods=1).std()
        signals['upper_band'] = signals['sma'] + (signals['std'] * self.num_std)
        signals['lower_band'] = signals['sma'] - (signals['std'] * self.num_std)
        
        # Generate signals
        signals['signal'] = 0.0
        signals['signal'] = np.where(signals['close'] < signals['lower_band'], 1.0, 0.0)  # Buy when price below lower band
        signals['signal'] = np.where(signals['close'] > signals['upper_band'], -1.0, signals['signal'])  # Sell when price above upper band
        
        return signals

def get_strategy(strategy_name, **kwargs):
    """Factory function to get a strategy instance by name"""
    strategies = {
        'ma_crossover': MovingAverageCrossover,
        'rsi': RSIStrategy,
        'bollinger_bands': BollingerBandsStrategy
    }
    
    strategy_class = strategies.get(strategy_name.lower())
    if not strategy_class:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available strategies: {', '.join(strategies.keys())}")
    
    return strategy_class(**kwargs) 