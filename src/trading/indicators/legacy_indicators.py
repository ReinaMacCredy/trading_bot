import pandas as pd
import numpy as np
import logging
import pandas_ta as ta

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
            
        # Using pandas_ta for more reliable EMA calculation
        return ta.ema(prices, length=self.period)
    
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
        
        # Calculate fast and slow EMAs using pandas_ta
        fast_ema = ta.ema(prices, length=fast_period)
        slow_ema = ta.ema(prices, length=slow_period)
        
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
        
        # Use pandas_ta for more reliable RSI calculation
        return ta.rsi(prices, length=self.period)
    
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
        
        # Use pandas_ta for more reliable MACD calculation
        macd = ta.macd(prices, fast=self.fast_period, slow=self.slow_period, signal=self.signal_period)
        
        # Create result DataFrame
        result = pd.DataFrame(index=prices.index)
        result['macd'] = macd['MACD_' + str(self.fast_period) + '_' + str(self.slow_period) + '_' + str(self.signal_period)]
        result['signal_line'] = macd['MACDs_' + str(self.fast_period) + '_' + str(self.slow_period) + '_' + str(self.signal_period)]
        result['histogram'] = macd['MACDh_' + str(self.fast_period) + '_' + str(self.slow_period) + '_' + str(self.signal_period)]
        
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
        
        # Buy when MACD line crosses above signal line
        macd_data['signal'] = np.where(
            (macd_data['macd'] > macd_data['signal_line']) & 
            (macd_data['macd'].shift(1) <= macd_data['signal_line'].shift(1)),
            1.0, 0.0)
        
        # Sell when MACD line crosses below signal line
        macd_data['signal'] = np.where(
            (macd_data['macd'] < macd_data['signal_line']) & 
            (macd_data['macd'].shift(1) >= macd_data['signal_line'].shift(1)),
            -1.0, macd_data['signal'])
        
        return macd_data

class BollingerBandsIndicator(Indicator):
    """Bollinger Bands indicator"""
    
    def __init__(self, period=20, num_std=2):
        super().__init__(f"BB-{period}-{num_std}")
        self.period = period
        self.num_std = num_std
        logger.info(f"Initialized {self.name} with period={period}, num_std={num_std}")
    
    def calculate(self, data):
        """Calculate Bollinger Bands values
        
        Args:
            data (pandas.DataFrame or pandas.Series): Price data with 'close' column
            
        Returns:
            pandas.DataFrame: DataFrame with 'middle_band', 'upper_band', and 'lower_band' columns
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
        
        # Use pandas_ta for more reliable Bollinger Bands calculation
        bbands = ta.bbands(prices, length=self.period, std=self.num_std)
        
        # Create result DataFrame
        result = pd.DataFrame(index=prices.index)
        result['middle_band'] = bbands['BBM_' + str(self.period) + '_' + str(self.num_std) + '.0']
        result['upper_band'] = bbands['BBU_' + str(self.period) + '_' + str(self.num_std) + '.0']
        result['lower_band'] = bbands['BBL_' + str(self.period) + '_' + str(self.num_std) + '.0']
        
        return result
    
    def get_signal(self, data):
        """Generate signals based on Bollinger Bands values
        
        Args:
            data (pandas.DataFrame or pandas.Series): Price data with 'close' column
            
        Returns:
            pandas.DataFrame: DataFrame with 'middle_band', 'upper_band', 'lower_band', and 'signal' columns
        """
        if isinstance(data, pd.Series):
            prices = data
        else:
            if 'close' not in data.columns:
                logger.error("DataFrame must contain 'close' column")
                return None
            prices = data['close']
            
        bb_data = self.calculate(prices)
        if bb_data is None:
            return None
        
        # Create result DataFrame with price data
        result = bb_data.copy()
        result['close'] = prices
        
        # Generate signals
        result['signal'] = 0.0
        result['signal'] = np.where(result['close'] < result['lower_band'], 1.0, 0.0)  # Buy when price below lower band
        result['signal'] = np.where(result['close'] > result['upper_band'], -1.0, result['signal'])  # Sell when price above upper band
        
        return result

class DualMACD_RSI_Strategy(Indicator):
    """Combined MACD and RSI strategy with dual timeframe confirmation"""
    
    def __init__(self, rsi_period=14, fast_period=12, slow_period=26, signal_period=9, oversold=30, overbought=70):
        super().__init__(f"DualMACD_RSI-{fast_period}-{slow_period}-{rsi_period}")
        self.rsi_period = rsi_period
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.oversold = oversold
        self.overbought = overbought
        logger.info(f"Initialized {self.name} with RSI period={rsi_period}, MACD parameters={fast_period}-{slow_period}-{signal_period}")
    
    def calculate(self, data):
        """Calculate MACD and RSI values for a dataframe
        
        Args:
            data (pandas.DataFrame): Price data with 'close' column
            
        Returns:
            pandas.DataFrame: DataFrame with indicator values added
        """
        if isinstance(data, pd.DataFrame):
            if 'close' not in data.columns:
                logger.error("DataFrame must contain 'close' column")
                return None
            prices = data['close']
        else:
            prices = data
            data = pd.DataFrame({'close': prices})
            
        if len(prices) < max(self.slow_period + self.signal_period, self.rsi_period):
            logger.warning(f"Not enough data for {self.name}. Need at least {max(self.slow_period + self.signal_period, self.rsi_period)} data points.")
            return None
        
        # Create result DataFrame
        result = data.copy()
        
        # Calculate RSI
        result['rsi'] = ta.rsi(prices, length=self.rsi_period)
        
        # Calculate MACD
        macd = ta.macd(prices, fast=self.fast_period, slow=self.slow_period, signal=self.signal_period)
        
        # Add MACD columns to result
        result['macd'] = macd['MACD_' + str(self.fast_period) + '_' + str(self.slow_period) + '_' + str(self.signal_period)]
        result['signal_line'] = macd['MACDs_' + str(self.fast_period) + '_' + str(self.slow_period) + '_' + str(self.signal_period)]
        result['histogram'] = macd['MACDh_' + str(self.fast_period) + '_' + str(self.slow_period) + '_' + str(self.signal_period)]
        
        return result
    
    def get_signal(self, data, higher_tf_data=None):
        """Generate signals based on MACD and RSI with dual timeframe confirmation
        
        Args:
            data (pandas.DataFrame): Main timeframe price data
            higher_tf_data (pandas.DataFrame): Optional higher timeframe data for confirmation
            
        Returns:
            pandas.DataFrame: DataFrame with indicator values and signals
        """
        if isinstance(data, pd.Series):
            prices = data
            data = pd.DataFrame({'close': prices})
        else:
            if 'close' not in data.columns:
                logger.error("DataFrame must contain 'close' column")
                return None
        
        # Calculate indicators for current timeframe
        result = self.calculate(data)
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
        
        # Apply higher timeframe confirmation if provided
        if higher_tf_data is not None:
            if isinstance(higher_tf_data, pd.Series):
                higher_tf_data = pd.DataFrame({'close': higher_tf_data})
            elif 'close' not in higher_tf_data.columns:
                logger.error("Higher timeframe DataFrame must contain 'close' column")
                return result  # Return without higher timeframe confirmation
            
            higher_tf_result = self.calculate(higher_tf_data)
            
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

class IndicatorFactory:
    """Factory class to create indicator instances"""
    
    @staticmethod
    def get_indicator(indicator_name, **params):
        """Get an indicator instance based on name and parameters
        
        Args:
            indicator_name (str): Name of the indicator to create
            **params: Parameters to pass to the indicator constructor
            
        Returns:
            Indicator: An instance of the requested indicator
        """
        indicators = {
            'ema': EMAIndicator,
            'rsi': RSIIndicator,
            'macd': MACDIndicator,
            'bollinger_bands': BollingerBandsIndicator,
            'dual_macd_rsi': DualMACD_RSI_Strategy
        }
        
        if indicator_name not in indicators:
            logger.error(f"Indicator '{indicator_name}' not found")
            return None
        
        return indicators[indicator_name](**params) 