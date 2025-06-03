"""
Enhanced Technical Indicators for Discord Trading Bot
Implements professional-grade technical analysis indicators using pandas-ta
"""

import pandas as pd
import pandas_ta as ta
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from src.config.config_loader import get_config

logger = logging.getLogger(__name__)

@dataclass
class IndicatorResult:
    """Container for indicator calculation results"""
    name: str
    value: Union[float, pd.Series]
    signal: Optional[str] = None
    strength: Optional[float] = None
    metadata: Optional[Dict] = None

class TechnicalIndicators:
    """
    Professional technical analysis indicators using pandas-ta
    Supports multiple timeframes and advanced calculations
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.indicator_config = self.config.indicators
        
    def calculate_rsi(self, df: pd.DataFrame, period: int = None) -> IndicatorResult:
        """
        Calculate RSI with signal generation
        
        Args:
            df: DataFrame with OHLCV data
            period: RSI period (default from config)
            
        Returns:
            IndicatorResult with RSI values and signals
        """
        try:
            period = period or self.indicator_config.rsi_period
            rsi = ta.rsi(df['close'], length=period)
            
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50
            
            # Generate signals
            signal = None
            strength = 0.5
            
            if current_rsi <= self.indicator_config.rsi_oversold:
                signal = 'BUY'
                strength = (self.indicator_config.rsi_oversold - current_rsi) / self.indicator_config.rsi_oversold
            elif current_rsi >= self.indicator_config.rsi_overbought:
                signal = 'SELL'
                strength = (current_rsi - self.indicator_config.rsi_overbought) / (100 - self.indicator_config.rsi_overbought)
            else:
                signal = 'NEUTRAL'
                
            return IndicatorResult(
                name='RSI',
                value=rsi,
                signal=signal,
                strength=min(max(strength, 0), 1),
                metadata={
                    'period': period,
                    'current_value': current_rsi,
                    'overbought_level': self.indicator_config.rsi_overbought,
                    'oversold_level': self.indicator_config.rsi_oversold
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return IndicatorResult(name='RSI', value=pd.Series(), signal='ERROR')
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = None, slow: int = None, signal: int = None) -> IndicatorResult:
        """
        Calculate MACD with signal generation
        
        Args:
            df: DataFrame with OHLCV data
            fast: Fast EMA period
            slow: Slow EMA period  
            signal: Signal line period
            
        Returns:
            IndicatorResult with MACD values and signals
        """
        try:
            fast = fast or self.indicator_config.macd_fast
            slow = slow or self.indicator_config.macd_slow
            signal_period = signal or self.indicator_config.macd_signal
            
            macd_data = ta.macd(df['close'], fast=fast, slow=slow, signal=signal_period)
            
            if macd_data is None or macd_data.empty:
                return IndicatorResult(name='MACD', value=pd.DataFrame(), signal='ERROR')
            
            macd_line = macd_data[f'MACD_{fast}_{slow}_{signal_period}']
            signal_line = macd_data[f'MACDs_{fast}_{slow}_{signal_period}']
            histogram = macd_data[f'MACDh_{fast}_{slow}_{signal_period}']
            
            # Generate signals based on crossovers
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_hist = histogram.iloc[-1]
            prev_hist = histogram.iloc[-2] if len(histogram) > 1 else 0
            
            # Signal generation
            signal_type = 'NEUTRAL'
            strength = 0.5
            
            if current_macd > current_signal and current_hist > 0:
                if prev_hist <= 0:  # Bullish crossover
                    signal_type = 'BUY'
                    strength = 0.8
                else:
                    signal_type = 'BUY'
                    strength = 0.6
            elif current_macd < current_signal and current_hist < 0:
                if prev_hist >= 0:  # Bearish crossover
                    signal_type = 'SELL'
                    strength = 0.8
                else:
                    signal_type = 'SELL'
                    strength = 0.6
                    
            return IndicatorResult(
                name='MACD',
                value=macd_data,
                signal=signal_type,
                strength=strength,
                metadata={
                    'fast_period': fast,
                    'slow_period': slow,
                    'signal_period': signal_period,
                    'current_macd': current_macd,
                    'current_signal': current_signal,
                    'current_histogram': current_hist
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return IndicatorResult(name='MACD', value=pd.DataFrame(), signal='ERROR')
    
    def calculate_ema(self, df: pd.DataFrame, periods: List[int] = None) -> Dict[str, IndicatorResult]:
        """
        Calculate multiple EMAs with trend signals
        
        Args:
            df: DataFrame with OHLCV data
            periods: List of EMA periods
            
        Returns:
            Dictionary of IndicatorResults for each EMA
        """
        try:
            periods = periods or self.indicator_config.ema_periods
            emas = {}
            
            for period in periods:
                ema = ta.ema(df['close'], length=period)
                current_price = df['close'].iloc[-1]
                current_ema = ema.iloc[-1]
                
                # Determine trend
                signal_type = 'BUY' if current_price > current_ema else 'SELL'
                strength = abs(current_price - current_ema) / current_ema
                
                emas[f'EMA_{period}'] = IndicatorResult(
                    name=f'EMA_{period}',
                    value=ema,
                    signal=signal_type,
                    strength=min(strength, 1.0),
                    metadata={
                        'period': period,
                        'current_value': current_ema,
                        'current_price': current_price
                    }
                )
                
            return emas
            
        except Exception as e:
            logger.error(f"Error calculating EMAs: {e}")
            return {}
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = None, std_dev: float = None) -> IndicatorResult:
        """
        Calculate Bollinger Bands with position signals
        
        Args:
            df: DataFrame with OHLCV data
            period: Period for moving average
            std_dev: Standard deviation multiplier
            
        Returns:
            IndicatorResult with Bollinger Bands data
        """
        try:
            period = period or self.indicator_config.bb_period
            std_dev = std_dev or self.indicator_config.bb_std_dev
            
            bb = ta.bbands(df['close'], length=period, std=std_dev)
            
            if bb is None or bb.empty:
                return IndicatorResult(name='BB', value=pd.DataFrame(), signal='ERROR')
            
            current_price = df['close'].iloc[-1]
            upper_band = bb[f'BBU_{period}_{std_dev}'].iloc[-1]
            middle_band = bb[f'BBM_{period}_{std_dev}'].iloc[-1]
            lower_band = bb[f'BBL_{period}_{std_dev}'].iloc[-1]
            
            # Generate signals based on band position
            signal_type = 'NEUTRAL'
            strength = 0.5
            
            band_width = upper_band - lower_band
            price_position = (current_price - lower_band) / band_width
            
            if price_position <= 0.2:  # Near lower band
                signal_type = 'BUY'
                strength = 0.8 - price_position * 2
            elif price_position >= 0.8:  # Near upper band
                signal_type = 'SELL'
                strength = (price_position - 0.8) * 5
                
            return IndicatorResult(
                name='BB',
                value=bb,
                signal=signal_type,
                strength=min(max(strength, 0), 1),
                metadata={
                    'period': period,
                    'std_dev': std_dev,
                    'upper_band': upper_band,
                    'middle_band': middle_band,
                    'lower_band': lower_band,
                    'price_position': price_position
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return IndicatorResult(name='BB', value=pd.DataFrame(), signal='ERROR')
    
    def calculate_atr(self, df: pd.DataFrame, period: int = None) -> IndicatorResult:
        """
        Calculate Average True Range for volatility measurement
        
        Args:
            df: DataFrame with OHLCV data
            period: ATR period
            
        Returns:
            IndicatorResult with ATR values
        """
        try:
            period = period or self.indicator_config.atr_period
            atr = ta.atr(df['high'], df['low'], df['close'], length=period)
            
            current_atr = atr.iloc[-1] if not atr.empty else 0
            current_price = df['close'].iloc[-1]
            
            # ATR as percentage of price for volatility assessment
            atr_percentage = (current_atr / current_price) * 100
            
            # Classify volatility
            if atr_percentage < 1:
                volatility = 'LOW'
            elif atr_percentage < 3:
                volatility = 'MEDIUM'
            else:
                volatility = 'HIGH'
                
            return IndicatorResult(
                name='ATR',
                value=atr,
                signal=volatility,
                strength=min(atr_percentage / 5, 1.0),  # Normalize to 0-1
                metadata={
                    'period': period,
                    'current_value': current_atr,
                    'atr_percentage': atr_percentage,
                    'volatility_level': volatility
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return IndicatorResult(name='ATR', value=pd.Series(), signal='ERROR')
    
    def calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> IndicatorResult:
        """
        Calculate Stochastic Oscillator
        
        Args:
            df: DataFrame with OHLCV data
            k_period: %K period
            d_period: %D period
            
        Returns:
            IndicatorResult with Stochastic values and signals
        """
        try:
            stoch = ta.stoch(df['high'], df['low'], df['close'], k=k_period, d=d_period)
            
            if stoch is None or stoch.empty:
                return IndicatorResult(name='STOCH', value=pd.DataFrame(), signal='ERROR')
            
            k_values = stoch[f'STOCHk_{k_period}_{d_period}_{d_period}']
            d_values = stoch[f'STOCHd_{k_period}_{d_period}_{d_period}']
            
            current_k = k_values.iloc[-1]
            current_d = d_values.iloc[-1]
            
            # Generate signals
            signal_type = 'NEUTRAL'
            strength = 0.5
            
            if current_k < 20 and current_d < 20:
                signal_type = 'BUY'
                strength = (20 - min(current_k, current_d)) / 20
            elif current_k > 80 and current_d > 80:
                signal_type = 'SELL'
                strength = (min(current_k, current_d) - 80) / 20
                
            return IndicatorResult(
                name='STOCH',
                value=stoch,
                signal=signal_type,
                strength=min(max(strength, 0), 1),
                metadata={
                    'k_period': k_period,
                    'd_period': d_period,
                    'current_k': current_k,
                    'current_d': current_d
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {e}")
            return IndicatorResult(name='STOCH', value=pd.DataFrame(), signal='ERROR')
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> IndicatorResult:
        """
        Calculate Average Directional Index for trend strength
        
        Args:
            df: DataFrame with OHLCV data
            period: ADX period
            
        Returns:
            IndicatorResult with ADX values and trend strength
        """
        try:
            adx_data = ta.adx(df['high'], df['low'], df['close'], length=period)
            
            if adx_data is None or adx_data.empty:
                return IndicatorResult(name='ADX', value=pd.DataFrame(), signal='ERROR')
            
            adx = adx_data[f'ADX_{period}']
            plus_di = adx_data[f'DMP_{period}']
            minus_di = adx_data[f'DMN_{period}']
            
            current_adx = adx.iloc[-1]
            current_plus_di = plus_di.iloc[-1]
            current_minus_di = minus_di.iloc[-1]
            
            # Determine trend strength and direction
            if current_adx > 25:
                if current_plus_di > current_minus_di:
                    signal_type = 'STRONG_UPTREND'
                else:
                    signal_type = 'STRONG_DOWNTREND'
                strength = min(current_adx / 50, 1.0)
            elif current_adx > 15:
                signal_type = 'WEAK_TREND'
                strength = current_adx / 25
            else:
                signal_type = 'NO_TREND'
                strength = 0.2
                
            return IndicatorResult(
                name='ADX',
                value=adx_data,
                signal=signal_type,
                strength=strength,
                metadata={
                    'period': period,
                    'current_adx': current_adx,
                    'plus_di': current_plus_di,
                    'minus_di': current_minus_di
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating ADX: {e}")
            return IndicatorResult(name='ADX', value=pd.DataFrame(), signal='ERROR')
    
    def calculate_volume_indicators(self, df: pd.DataFrame) -> Dict[str, IndicatorResult]:
        """
        Calculate volume-based indicators
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary of volume indicator results
        """
        try:
            volume_indicators = {}
            
            # Volume SMA
            vol_sma = ta.sma(df['volume'], length=20)
            current_vol = df['volume'].iloc[-1]
            avg_vol = vol_sma.iloc[-1]
            
            vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
            
            if vol_ratio > 1.5:
                vol_signal = 'HIGH_VOLUME'
                vol_strength = min((vol_ratio - 1) / 2, 1.0)
            elif vol_ratio < 0.5:
                vol_signal = 'LOW_VOLUME'
                vol_strength = (1 - vol_ratio) / 0.5
            else:
                vol_signal = 'NORMAL_VOLUME'
                vol_strength = 0.5
                
            volume_indicators['VOLUME'] = IndicatorResult(
                name='VOLUME',
                value=vol_sma,
                signal=vol_signal,
                strength=vol_strength,
                metadata={
                    'current_volume': current_vol,
                    'average_volume': avg_vol,
                    'volume_ratio': vol_ratio
                }
            )
            
            # On Balance Volume
            obv = ta.obv(df['close'], df['volume'])
            obv_ma = ta.sma(obv, length=10)
            
            if len(obv_ma) > 1:
                obv_trend = 'RISING' if obv_ma.iloc[-1] > obv_ma.iloc[-2] else 'FALLING'
            else:
                obv_trend = 'NEUTRAL'
                
            volume_indicators['OBV'] = IndicatorResult(
                name='OBV',
                value=obv,
                signal=obv_trend,
                strength=0.5,
                metadata={
                    'current_obv': obv.iloc[-1],
                    'obv_ma': obv_ma.iloc[-1]
                }
            )
            
            return volume_indicators
            
        except Exception as e:
            logger.error(f"Error calculating volume indicators: {e}")
            return {}
    
    def get_comprehensive_analysis(self, df: pd.DataFrame) -> Dict[str, IndicatorResult]:
        """
        Get comprehensive technical analysis for a given dataset
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary containing all calculated indicators
        """
        try:
            analysis = {}
            
            # Core indicators
            analysis['RSI'] = self.calculate_rsi(df)
            analysis['MACD'] = self.calculate_macd(df)
            analysis['BB'] = self.calculate_bollinger_bands(df)
            analysis['ATR'] = self.calculate_atr(df)
            analysis['STOCH'] = self.calculate_stochastic(df)
            analysis['ADX'] = self.calculate_adx(df)
            
            # EMA analysis
            ema_results = self.calculate_ema(df)
            analysis.update(ema_results)
            
            # Volume analysis
            volume_results = self.calculate_volume_indicators(df)
            analysis.update(volume_results)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {}
    
    def generate_composite_signal(self, analysis: Dict[str, IndicatorResult]) -> Tuple[str, float]:
        """
        Generate a composite signal from multiple indicators
        
        Args:
            analysis: Dictionary of indicator results
            
        Returns:
            Tuple of (signal, confidence)
        """
        try:
            buy_signals = 0
            sell_signals = 0
            total_weight = 0
            
            # Weight different indicators
            weights = {
                'RSI': 0.2,
                'MACD': 0.25,
                'BB': 0.15,
                'STOCH': 0.15,
                'EMA_21': 0.1,
                'EMA_50': 0.1,
                'VOLUME': 0.05
            }
            
            for indicator_name, weight in weights.items():
                if indicator_name in analysis:
                    result = analysis[indicator_name]
                    if result.signal == 'BUY':
                        buy_signals += weight * result.strength
                    elif result.signal == 'SELL':
                        sell_signals += weight * result.strength
                    total_weight += weight
            
            # Normalize signals
            if total_weight > 0:
                buy_signals /= total_weight
                sell_signals /= total_weight
            
            # Determine final signal
            signal_diff = buy_signals - sell_signals
            
            if signal_diff > 0.3:
                return 'BUY', min(signal_diff, 1.0)
            elif signal_diff < -0.3:
                return 'SELL', min(abs(signal_diff), 1.0)
            else:
                return 'NEUTRAL', abs(signal_diff)
                
        except Exception as e:
            logger.error(f"Error generating composite signal: {e}")
            return 'NEUTRAL', 0.0 