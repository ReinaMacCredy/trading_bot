"""
Enhanced Trading Strategies for Discord Trading Bot
Implements professional trading strategies with multi-timeframe analysis
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from .indicators import TechnicalIndicators, IndicatorResult
from .exchange_client import ExchangeClient
from src.config.config_loader import get_config

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Container for trading signal information"""
    symbol: str
    signal: str  # BUY, SELL, HOLD
    confidence: float  # 0.0 to 1.0
    entry_price: float
    take_profit: float
    stop_loss: float
    quantity: float
    timestamp: datetime
    timeframe: str
    strategy_name: str
    indicators_used: List[str]
    metadata: Optional[Dict] = None

@dataclass
class BacktestResult:
    """Container for backtest results"""
    total_return: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    avg_trade: float
    metadata: Dict

class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies
    """
    
    def __init__(self, config=None, exchange_client=None):
        self.config = config or get_config()
        self.exchange_client = exchange_client
        self.indicators = TechnicalIndicators(config)
        self.name = self.__class__.__name__
        
    @abstractmethod
    def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """
        Analyze market data and generate trading signal
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            TradingSignal object
        """
        pass
    
    @abstractmethod
    def get_required_periods(self) -> int:
        """
        Get minimum number of periods required for analysis
        
        Returns:
            Minimum periods needed
        """
        pass
    
    def calculate_position_size(self, account_balance: float, entry_price: float, stop_loss: float) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            account_balance: Current account balance
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            
        Returns:
            Position size in base currency
        """
        risk_amount = account_balance * (self.config.trading.risk_percentage / 100)
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 0
            
        position_size = risk_amount / price_diff
        return position_size
    
    def calculate_take_profit_stop_loss(self, df: pd.DataFrame, signal: str, entry_price: float) -> Tuple[float, float]:
        """
        Calculate take profit and stop loss levels using ATR
        
        Args:
            df: DataFrame with OHLCV data
            signal: BUY or SELL signal
            entry_price: Entry price
            
        Returns:
            Tuple of (take_profit, stop_loss)
        """
        atr_result = self.indicators.calculate_atr(df)
        atr_value = atr_result.metadata['current_value'] if atr_result.metadata else entry_price * 0.02
        
        if signal == 'BUY':
            stop_loss = entry_price - (atr_value * self.config.trading.stop_loss_multiplier)
            take_profit = entry_price + (atr_value * self.config.trading.take_profit_multiplier)
        else:  # SELL
            stop_loss = entry_price + (atr_value * self.config.trading.stop_loss_multiplier)
            take_profit = entry_price - (atr_value * self.config.trading.take_profit_multiplier)
            
        return take_profit, stop_loss

class MACDRSIStrategy(BaseStrategy):
    """
    MACD + RSI combined strategy with multi-timeframe confirmation
    """
    
    def __init__(self, config=None, exchange_client=None):
        super().__init__(config, exchange_client)
        self.name = "MACD_RSI_Strategy"
    
    def get_required_periods(self) -> int:
        return max(50, self.config.indicators.macd_slow + 10)
    
    def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """
        Analyze using MACD + RSI strategy
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            TradingSignal object
        """
        try:
            # Calculate indicators
            rsi_result = self.indicators.calculate_rsi(df)
            macd_result = self.indicators.calculate_macd(df)
            ema_results = self.indicators.calculate_ema(df)
            atr_result = self.indicators.calculate_atr(df)
            
            current_price = df['close'].iloc[-1]
            timestamp = datetime.now()
            
            # Initialize signal
            signal_type = 'HOLD'
            confidence = 0.0
            
            # Check if we have valid indicators
            if (rsi_result.signal == 'ERROR' or macd_result.signal == 'ERROR' or 
                not ema_results or 'EMA_21' not in ema_results):
                return TradingSignal(
                    symbol=symbol,
                    signal='HOLD',
                    confidence=0.0,
                    entry_price=current_price,
                    take_profit=current_price,
                    stop_loss=current_price,
                    quantity=0.0,
                    timestamp=timestamp,
                    timeframe=self.config.timeframes['analysis'],
                    strategy_name=self.name,
                    indicators_used=['RSI', 'MACD', 'EMA'],
                    metadata={'error': 'Indicator calculation failed'}
                )
            
            # Get indicator values
            rsi_value = rsi_result.metadata['current_value']
            macd_signal = macd_result.signal
            ema_21 = ema_results['EMA_21']
            ema_50 = ema_results.get('EMA_50')
            
            # Strategy logic
            buy_conditions = []
            sell_conditions = []
            
            # RSI conditions
            if rsi_value < 70 and rsi_value > 30:  # Not overbought/oversold
                if rsi_value > 50:
                    buy_conditions.append(('RSI_BULLISH', 0.3))
                else:
                    sell_conditions.append(('RSI_BEARISH', 0.3))
            elif rsi_value <= 30:  # Oversold
                buy_conditions.append(('RSI_OVERSOLD', 0.5))
            elif rsi_value >= 70:  # Overbought
                sell_conditions.append(('RSI_OVERBOUGHT', 0.5))
            
            # MACD conditions
            if macd_signal == 'BUY':
                buy_conditions.append(('MACD_BULLISH', 0.4))
            elif macd_signal == 'SELL':
                sell_conditions.append(('MACD_BEARISH', 0.4))
            
            # EMA trend conditions
            if current_price > ema_21.metadata['current_value']:
                buy_conditions.append(('EMA21_ABOVE', 0.2))
            else:
                sell_conditions.append(('EMA21_BELOW', 0.2))
            
            if ema_50 and current_price > ema_50.metadata['current_value']:
                buy_conditions.append(('EMA50_ABOVE', 0.3))
            elif ema_50:
                sell_conditions.append(('EMA50_BELOW', 0.3))
            
            # Calculate confidence scores
            buy_score = sum(weight for _, weight in buy_conditions)
            sell_score = sum(weight for _, weight in sell_conditions)
            
            # Determine signal
            if buy_score > sell_score and buy_score >= 0.8:
                signal_type = 'BUY'
                confidence = min(buy_score, 1.0)
            elif sell_score > buy_score and sell_score >= 0.8:
                signal_type = 'SELL'
                confidence = min(sell_score, 1.0)
            else:
                signal_type = 'HOLD'
                confidence = abs(buy_score - sell_score)
            
            # Calculate take profit and stop loss
            take_profit, stop_loss = self.calculate_take_profit_stop_loss(df, signal_type, current_price)
            
            # Calculate position size (placeholder for now)
            quantity = 0.1  # This should be calculated based on account balance
            
            return TradingSignal(
                symbol=symbol,
                signal=signal_type,
                confidence=confidence,
                entry_price=current_price,
                take_profit=take_profit,
                stop_loss=stop_loss,
                quantity=quantity,
                timestamp=timestamp,
                timeframe=self.config.timeframes['analysis'],
                strategy_name=self.name,
                indicators_used=['RSI', 'MACD', 'EMA'],
                metadata={
                    'rsi_value': rsi_value,
                    'macd_signal': macd_signal,
                    'buy_conditions': buy_conditions,
                    'sell_conditions': sell_conditions,
                    'buy_score': buy_score,
                    'sell_score': sell_score,
                    'atr_value': atr_result.metadata.get('current_value', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in MACD RSI strategy analysis: {e}")
            return TradingSignal(
                symbol=symbol,
                signal='HOLD',
                confidence=0.0,
                entry_price=current_price if 'current_price' in locals() else 0,
                take_profit=0,
                stop_loss=0,
                quantity=0,
                timestamp=datetime.now(),
                timeframe=self.config.timeframes['analysis'],
                strategy_name=self.name,
                indicators_used=[],
                metadata={'error': str(e)}
            )

class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands mean reversion strategy
    """
    
    def __init__(self, config=None, exchange_client=None):
        super().__init__(config, exchange_client)
        self.name = "Bollinger_Bands_Strategy"
    
    def get_required_periods(self) -> int:
        return self.config.indicators.bb_period + 20
    
    def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """
        Analyze using Bollinger Bands strategy
        """
        try:
            # Calculate indicators
            bb_result = self.indicators.calculate_bollinger_bands(df)
            rsi_result = self.indicators.calculate_rsi(df)
            volume_results = self.indicators.calculate_volume_indicators(df)
            
            current_price = df['close'].iloc[-1]
            timestamp = datetime.now()
            
            if bb_result.signal == 'ERROR':
                return TradingSignal(
                    symbol=symbol,
                    signal='HOLD',
                    confidence=0.0,
                    entry_price=current_price,
                    take_profit=current_price,
                    stop_loss=current_price,
                    quantity=0.0,
                    timestamp=timestamp,
                    timeframe=self.config.timeframes['analysis'],
                    strategy_name=self.name,
                    indicators_used=['BB'],
                    metadata={'error': 'Bollinger Bands calculation failed'}
                )
            
            # Get band values
            upper_band = bb_result.metadata['upper_band']
            middle_band = bb_result.metadata['middle_band']
            lower_band = bb_result.metadata['lower_band']
            price_position = bb_result.metadata['price_position']
            
            # Strategy logic
            signal_type = 'HOLD'
            confidence = 0.0
            
            # Mean reversion logic
            if price_position <= 0.1:  # Very close to lower band
                signal_type = 'BUY'
                confidence = 0.8
            elif price_position <= 0.2:  # Close to lower band
                signal_type = 'BUY'
                confidence = 0.6
            elif price_position >= 0.9:  # Very close to upper band
                signal_type = 'SELL'
                confidence = 0.8
            elif price_position >= 0.8:  # Close to upper band
                signal_type = 'SELL'
                confidence = 0.6
            
            # Volume confirmation
            if 'VOLUME' in volume_results:
                vol_signal = volume_results['VOLUME'].signal
                if vol_signal == 'HIGH_VOLUME':
                    confidence *= 1.2  # Increase confidence with high volume
                elif vol_signal == 'LOW_VOLUME':
                    confidence *= 0.8  # Decrease confidence with low volume
            
            # RSI filter
            if rsi_result.signal != 'ERROR':
                rsi_value = rsi_result.metadata['current_value']
                if signal_type == 'BUY' and rsi_value > 70:
                    confidence *= 0.5  # Reduce buy confidence if RSI overbought
                elif signal_type == 'SELL' and rsi_value < 30:
                    confidence *= 0.5  # Reduce sell confidence if RSI oversold
            
            confidence = min(confidence, 1.0)
            
            # Calculate take profit and stop loss
            if signal_type == 'BUY':
                take_profit = middle_band
                stop_loss = lower_band * 0.995  # Slightly below lower band
            elif signal_type == 'SELL':
                take_profit = middle_band
                stop_loss = upper_band * 1.005  # Slightly above upper band
            else:
                take_profit, stop_loss = self.calculate_take_profit_stop_loss(df, signal_type, current_price)
            
            return TradingSignal(
                symbol=symbol,
                signal=signal_type,
                confidence=confidence,
                entry_price=current_price,
                take_profit=take_profit,
                stop_loss=stop_loss,
                quantity=0.1,  # Placeholder
                timestamp=timestamp,
                timeframe=self.config.timeframes['analysis'],
                strategy_name=self.name,
                indicators_used=['BB', 'RSI', 'VOLUME'],
                metadata={
                    'upper_band': upper_band,
                    'middle_band': middle_band,
                    'lower_band': lower_band,
                    'price_position': price_position,
                    'rsi_value': rsi_result.metadata.get('current_value', 50) if rsi_result.metadata else 50
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Bollinger Bands strategy analysis: {e}")
            return TradingSignal(
                symbol=symbol,
                signal='HOLD',
                confidence=0.0,
                entry_price=current_price if 'current_price' in locals() else 0,
                take_profit=0,
                stop_loss=0,
                quantity=0,
                timestamp=datetime.now(),
                timeframe=self.config.timeframes['analysis'],
                strategy_name=self.name,
                indicators_used=[],
                metadata={'error': str(e)}
            )

class MultiTimeframeStrategy(BaseStrategy):
    """
    Multi-timeframe strategy combining different timeframe signals
    """
    
    def __init__(self, config=None, exchange_client=None):
        super().__init__(config, exchange_client)
        self.name = "Multi_Timeframe_Strategy"
        self.primary_strategy = MACDRSIStrategy(config, exchange_client)
        self.secondary_strategy = BollingerBandsStrategy(config, exchange_client)
    
    def get_required_periods(self) -> int:
        return max(self.primary_strategy.get_required_periods(), 
                  self.secondary_strategy.get_required_periods())
    
    async def get_higher_timeframe_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get higher timeframe data for confirmation
        """
        if not self.exchange_client:
            return None
            
        try:
            higher_tf = self.config.timeframes['higher_tf']
            df = await self.exchange_client.fetch_ohlcv(symbol, higher_tf, limit=100)
            return df
        except Exception as e:
            logger.error(f"Error fetching higher timeframe data: {e}")
            return None
    
    def analyze(self, df: pd.DataFrame, symbol: str) -> TradingSignal:
        """
        Analyze using multiple timeframes and strategies
        """
        try:
            # Primary timeframe analysis
            primary_signal = self.primary_strategy.analyze(df, symbol)
            secondary_signal = self.secondary_strategy.analyze(df, symbol)
            
            # Combine signals
            signals = [primary_signal, secondary_signal]
            
            # Count signal types
            buy_signals = sum(1 for s in signals if s.signal == 'BUY')
            sell_signals = sum(1 for s in signals if s.signal == 'SELL')
            
            # Calculate weighted confidence
            total_confidence = 0
            signal_weights = [0.6, 0.4]  # Primary strategy has more weight
            
            for signal, weight in zip(signals, signal_weights):
                if signal.signal == 'BUY':
                    total_confidence += signal.confidence * weight
                elif signal.signal == 'SELL':
                    total_confidence -= signal.confidence * weight
            
            # Determine final signal
            if total_confidence > 0.5 and buy_signals > sell_signals:
                final_signal = 'BUY'
                final_confidence = min(total_confidence, 1.0)
            elif total_confidence < -0.5 and sell_signals > buy_signals:
                final_signal = 'SELL'
                final_confidence = min(abs(total_confidence), 1.0)
            else:
                final_signal = 'HOLD'
                final_confidence = abs(total_confidence)
            
            # Use primary signal's price levels as base
            take_profit, stop_loss = self.calculate_take_profit_stop_loss(
                df, final_signal, primary_signal.entry_price
            )
            
            return TradingSignal(
                symbol=symbol,
                signal=final_signal,
                confidence=final_confidence,
                entry_price=primary_signal.entry_price,
                take_profit=take_profit,
                stop_loss=stop_loss,
                quantity=primary_signal.quantity,
                timestamp=datetime.now(),
                timeframe=self.config.timeframes['analysis'],
                strategy_name=self.name,
                indicators_used=['MACD', 'RSI', 'BB', 'VOLUME'],
                metadata={
                    'primary_signal': primary_signal.signal,
                    'secondary_signal': secondary_signal.signal,
                    'primary_confidence': primary_signal.confidence,
                    'secondary_confidence': secondary_signal.confidence,
                    'total_confidence': total_confidence,
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals
                }
            )
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe strategy analysis: {e}")
            current_price = df['close'].iloc[-1] if len(df) > 0 else 0
            return TradingSignal(
                symbol=symbol,
                signal='HOLD',
                confidence=0.0,
                entry_price=current_price,
                take_profit=current_price,
                stop_loss=current_price,
                quantity=0,
                timestamp=datetime.now(),
                timeframe=self.config.timeframes['analysis'],
                strategy_name=self.name,
                indicators_used=[],
                metadata={'error': str(e)}
            )

class StrategyManager:
    """
    Manager class for handling multiple trading strategies
    """
    
    def __init__(self, config=None, exchange_client=None):
        self.config = config or get_config()
        self.exchange_client = exchange_client
        self.strategies = {
            'macd_rsi': MACDRSIStrategy(config, exchange_client),
            'bollinger_bands': BollingerBandsStrategy(config, exchange_client),
            'multi_timeframe': MultiTimeframeStrategy(config, exchange_client),
        }
        self.default_strategy = 'macd_rsi'
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """Get strategy by name"""
        return self.strategies.get(strategy_name.lower())
    
    def list_strategies(self) -> List[str]:
        """List available strategy names"""
        return list(self.strategies.keys())
    
    def analyze_symbol(self, df: pd.DataFrame, symbol: str, strategy_name: str = None) -> TradingSignal:
        """
        Analyze symbol using specified strategy
        
        Args:
            df: OHLCV DataFrame
            symbol: Trading symbol
            strategy_name: Strategy to use (default: macd_rsi)
            
        Returns:
            TradingSignal object
        """
        strategy_name = strategy_name or self.default_strategy
        strategy = self.get_strategy(strategy_name)
        
        if not strategy:
            logger.error(f"Strategy '{strategy_name}' not found")
            return TradingSignal(
                symbol=symbol,
                signal='HOLD',
                confidence=0.0,
                entry_price=df['close'].iloc[-1] if len(df) > 0 else 0,
                take_profit=0,
                stop_loss=0,
                quantity=0,
                timestamp=datetime.now(),
                timeframe=self.config.timeframes['analysis'],
                strategy_name='unknown',
                indicators_used=[],
                metadata={'error': f"Strategy '{strategy_name}' not found"}
            )
        
        return strategy.analyze(df, symbol)
    
    def backtest_strategy(self, df: pd.DataFrame, symbol: str, strategy_name: str, 
                         initial_balance: float = 10000) -> BacktestResult:
        """
        Simple backtest implementation
        
        Args:
            df: Historical OHLCV data
            symbol: Trading symbol
            strategy_name: Strategy to test
            initial_balance: Starting balance
            
        Returns:
            BacktestResult object
        """
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return BacktestResult(
                total_return=0.0,
                win_rate=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                profit_factor=0.0,
                avg_trade=0.0,
                metadata={'error': f"Strategy '{strategy_name}' not found"}
            )
        
        try:
            # Simple backtest logic
            balance = initial_balance
            trades = []
            position = None
            required_periods = strategy.get_required_periods()
            
            for i in range(required_periods, len(df)):
                current_df = df.iloc[:i+1]
                signal = strategy.analyze(current_df, symbol)
                
                current_price = df['close'].iloc[i]
                
                # Enter position
                if position is None and signal.signal in ['BUY', 'SELL']:
                    position = {
                        'type': signal.signal,
                        'entry_price': current_price,
                        'stop_loss': signal.stop_loss,
                        'take_profit': signal.take_profit,
                        'quantity': signal.quantity,
                        'entry_time': i
                    }
                
                # Exit position
                elif position is not None:
                    exit_triggered = False
                    exit_price = current_price
                    exit_reason = 'time_exit'
                    
                    # Check stop loss
                    if position['type'] == 'BUY' and current_price <= position['stop_loss']:
                        exit_triggered = True
                        exit_price = position['stop_loss']
                        exit_reason = 'stop_loss'
                    elif position['type'] == 'SELL' and current_price >= position['stop_loss']:
                        exit_triggered = True
                        exit_price = position['stop_loss']
                        exit_reason = 'stop_loss'
                    
                    # Check take profit
                    elif position['type'] == 'BUY' and current_price >= position['take_profit']:
                        exit_triggered = True
                        exit_price = position['take_profit']
                        exit_reason = 'take_profit'
                    elif position['type'] == 'SELL' and current_price <= position['take_profit']:
                        exit_triggered = True
                        exit_price = position['take_profit']
                        exit_reason = 'take_profit'
                    
                    # Opposite signal
                    elif signal.signal != 'HOLD' and signal.signal != position['type']:
                        exit_triggered = True
                        exit_reason = 'opposite_signal'
                    
                    if exit_triggered:
                        # Calculate P&L
                        if position['type'] == 'BUY':
                            pnl = (exit_price - position['entry_price']) * position['quantity']
                        else:  # SELL
                            pnl = (position['entry_price'] - exit_price) * position['quantity']
                        
                        balance += pnl
                        
                        trades.append({
                            'entry_price': position['entry_price'],
                            'exit_price': exit_price,
                            'pnl': pnl,
                            'type': position['type'],
                            'exit_reason': exit_reason,
                            'duration': i - position['entry_time']
                        })
                        
                        position = None
            
            # Calculate backtest metrics
            if not trades:
                return BacktestResult(
                    total_return=0.0,
                    win_rate=0.0,
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    max_drawdown=0.0,
                    sharpe_ratio=0.0,
                    profit_factor=0.0,
                    avg_trade=0.0,
                    metadata={'message': 'No trades executed'}
                )
            
            total_return = (balance - initial_balance) / initial_balance * 100
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            losing_trades = len([t for t in trades if t['pnl'] < 0])
            win_rate = winning_trades / len(trades) * 100
            avg_trade = sum(t['pnl'] for t in trades) / len(trades)
            
            # Calculate max drawdown (simplified)
            peak = initial_balance
            max_dd = 0
            running_balance = initial_balance
            for trade in trades:
                running_balance += trade['pnl']
                if running_balance > peak:
                    peak = running_balance
                drawdown = (peak - running_balance) / peak * 100
                max_dd = max(max_dd, drawdown)
            
            # Calculate profit factor
            gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
            gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            return BacktestResult(
                total_return=total_return,
                win_rate=win_rate,
                total_trades=len(trades),
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                max_drawdown=max_dd,
                sharpe_ratio=0.0,  # Simplified - would need risk-free rate
                profit_factor=profit_factor,
                avg_trade=avg_trade,
                metadata={
                    'final_balance': balance,
                    'total_pnl': balance - initial_balance,
                    'trades': trades[-10:]  # Last 10 trades for review
                }
            )
            
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return BacktestResult(
                total_return=0.0,
                win_rate=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                profit_factor=0.0,
                avg_trade=0.0,
                metadata={'error': str(e)}
            ) 