import pandas as pd
import numpy as np
import logging

logger = logging.getLogger('indicators')

class Indicator:
    """Base class for technical indicators"""
    
    def __init__(self, name):
        self.name = name
        logger.info(f"Initialized {self.name} indicator")
        
    def calculate(self, data):
        """Calculate the indicator values
        
        Args:
            data (pandas.DataFrame or pandas.Series): Price data
            
        Returns:
            pandas.DataFrame or pandas.Series: Calculated indicator values
        """
        raise NotImplementedError("Subclasses must implement calculate()")
    
    def get_signal(self, data):
        """Generate trading signals based on the indicator
        
        Args:
            data (pandas.DataFrame or pandas.Series): Price data
            
        Returns:
            pandas.Series: Series with signal values (1 for buy, -1 for sell, 0 for hold)
        """
        raise NotImplementedError("Subclasses must implement get_signal()")

class EMAIndicator(Indicator):
    """Exponential Moving Average indicator"""
    
    def __init__(self, period=20):
        super().__init__(f"EMA-{period}")
        self.period = period
        logger.info(f"Initialized {self.name} with period={period}")
    
    def calculate(self, data):
        """Calculate EMA values
        
        Args:
            data (pandas.DataFrame or pandas.Series): Price data with 'close' column
            
        Returns:
            pandas.Series: EMA values
        """
        if isinstance(data, pd.DataFrame):
            if 'close' not in data.columns:
                logger.error("DataFrame must contain 'close' column")
                return None
            prices = data['close']
        else:
            prices = data
            
        if len(prices) < self.period:
            logger.warning(f"Not enough data for {self.name}. Need at least {self.period} data points.")
            return None
            
        return prices.ewm(span=self.period, adjust=False).mean()
    
    def get_signal(self, data, fast_period=12, slow_period=26):
        """Generate signals based on EMA crossover
        
        Args:
            data (pandas.DataFrame): Price data with 'close' column
            fast_period (int): Period for fast EMA
            slow_period (int): Period for slow EMA
            
        Returns:
            pandas.DataFrame: DataFrame with 'fast_ema', 'slow_ema', and 'signal' columns
        """
        if isinstance(data, pd.Series):
            prices = data
        else:
            if 'close' not in data.columns:
                logger.error("DataFrame must contain 'close' column")
                return None
            prices = data['close']
            
        if len(prices) < max(fast_period, slow_period):
            logger.warning(f"Not enough data for EMA crossover. Need at least {max(fast_period, slow_period)} data points.")
            return None
        
        # Calculate fast and slow EMAs
        fast_ema = prices.ewm(span=fast_period, adjust=False).mean()
        slow_ema = prices.ewm(span=slow_period, adjust=False).mean()
        
        # Create result DataFrame
        result = pd.DataFrame(index=prices.index)
        result['fast_ema'] = fast_ema
        result['slow_ema'] = slow_ema
        
        # Generate signals
        result['signal'] = 0.0
        result['signal'] = np.where(result['fast_ema'] > result['slow_ema'], 1.0, 0.0)
        result['position'] = result['signal'].diff()
        
        return result

class RSIIndicator(Indicator):
    """Relative Strength Index indicator"""
    
    def __init__(self, period=14, oversold=30, overbought=70):
        super().__init__(f"RSI-{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        logger.info(f"Initialized {self.name} with period={period}, oversold={oversold}, overbought={overbought}")
    
    def calculate(self, data):
        """Calculate RSI values
        
        Args:
            data (pandas.DataFrame or pandas.Series): Price data with 'close' column
            
        Returns:
            pandas.Series: RSI values
        """
        if isinstance(data, pd.DataFrame):
            if 'close' not in data.columns:
                logger.error("DataFrame must contain 'close' column")
                return None
            prices = data['close']
        else:
            prices = data
            
        if len(prices) < self.period:
            logger.warning(f"Not enough data for {self.name}. Need at least {self.period} data points.")
            return None
        
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.clip(lower=0)
        losses = -1 * delta.clip(upper=0)
        
        # Calculate average gains and losses
        avg_gains = gains.ewm(com=self.period-1, adjust=False).mean()
        avg_losses = losses.ewm(com=self.period-1, adjust=False).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def get_signal(self, data):
        """Generate signals based on RSI values
        
        Args:
            data (pandas.DataFrame or pandas.Series): Price data with 'close' column
            
        Returns:
            pandas.DataFrame: DataFrame with 'rsi' and 'signal' columns
        """
        if isinstance(data, pd.Series):
            prices = data
        else:
            if 'close' not in data.columns:
                logger.error("DataFrame must contain 'close' column")
                return None
            prices = data['close']
            
        rsi = self.calculate(prices)
        if rsi is None:
            return None
        
        # Create result DataFrame
        result = pd.DataFrame(index=prices.index)
        result['rsi'] = rsi
        
        # Generate signals
        result['signal'] = 0.0
        result['signal'] = np.where(result['rsi'] < self.oversold, 1.0, 0.0)  # Buy when oversold
        result['signal'] = np.where(result['rsi'] > self.overbought, -1.0, result['signal'])  # Sell when overbought
        
        return result

class MACDIndicator(Indicator):
    """Moving Average Convergence Divergence indicator"""
    
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        super().__init__(f"MACD-{fast_period}-{slow_period}-{signal_period}")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        logger.info(f"Initialized {self.name} with fast_period={fast_period}, slow_period={slow_period}, signal_period={signal_period}")
    
    def calculate(self, data):
        """Calculate MACD values
        
        Args:
            data (pandas.DataFrame or pandas.Series): Price data with 'close' column
            
        Returns:
            pandas.DataFrame: DataFrame with 'macd', 'signal_line', and 'histogram' columns
        """
        if isinstance(data, pd.DataFrame):
            if 'close' not in data.columns:
                logger.error("DataFrame must contain 'close' column")
                return None
            prices = data['close']
        else:
            prices = data
            
        if len(prices) < self.slow_period + self.signal_period:
            logger.warning(f"Not enough data for {self.name}. Need at least {self.slow_period + self.signal_period} data points.")
            return None
        
        # Calculate fast and slow EMAs
        fast_ema = prices.ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = prices.ewm(span=self.slow_period, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        # Create result DataFrame
        result = pd.DataFrame(index=prices.index)
        result['macd'] = macd_line
        result['signal_line'] = signal_line
        result['histogram'] = histogram
        
        return result
    
    def get_signal(self, data):
        """Generate signals based on MACD values
        
        Args:
            data (pandas.DataFrame or pandas.Series): Price data with 'close' column
            
        Returns:
            pandas.DataFrame: DataFrame with 'macd', 'signal_line', 'histogram', and 'signal' columns
        """
        if isinstance(data, pd.Series):
            prices = data
        else:
            if 'close' not in data.columns:
                logger.error("DataFrame must contain 'close' column")
                return None
            prices = data['close']
            
        macd_data = self.calculate(prices)
        if macd_data is None:
            return None
        
        # Generate signals
        macd_data['signal'] = 0.0
        
        # Buy signal: MACD line crosses above signal line
        macd_data['signal'] = np.where(
            (macd_data['macd'] > macd_data['signal_line']) & 
            (macd_data['macd'].shift(1) <= macd_data['signal_line'].shift(1)),
            1.0, 0.0
        )
        
        # Sell signal: MACD line crosses below signal line
        macd_data['signal'] = np.where(
            (macd_data['macd'] < macd_data['signal_line']) & 
            (macd_data['macd'].shift(1) >= macd_data['signal_line'].shift(1)),
            -1.0, macd_data['signal']
        )
        
        return macd_data

class IndicatorFactory:
    """Factory class for creating technical indicators"""
    
    @staticmethod
    def get_indicator(indicator_name, **params):
        """Create an indicator instance by name
        
        Args:
            indicator_name (str): Name of the indicator
            **params: Parameters for the indicator
            
        Returns:
            Indicator: Instance of the requested indicator
        """
        indicators = {
            'ema': EMAIndicator,
            'rsi': RSIIndicator,
            'macd': MACDIndicator
        }
        
        indicator_class = indicators.get(indicator_name.lower())
        if not indicator_class:
            raise ValueError(f"Unknown indicator: {indicator_name}. Available indicators: {', '.join(indicators.keys())}")
        
        return indicator_class(**params) 