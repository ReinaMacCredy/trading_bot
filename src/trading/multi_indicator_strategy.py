import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class MultiIndicatorStrategy:
    """
    Advanced trading strategy that combines multiple technical indicators 
    to generate more accurate signals with fewer false positives.
    
    Strategy combines:
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - EMA (Exponential Moving Average)
    - Volume analysis
    - ATR (Average True Range) for volatility
    """
    
    def __init__(self, 
                rsi_period: int = 14, 
                macd_fast: int = 12, 
                macd_slow: int = 26, 
                macd_signal: int = 9, 
                ema_periods: List[int] = None,
                atr_period: int = 14,
                volume_period: int = 20):
        """
        Initialize the strategy with parameters.
        
        Args:
            rsi_period: Period for RSI calculation
            macd_fast: Fast period for MACD calculation
            macd_slow: Slow period for MACD calculation
            macd_signal: Signal period for MACD calculation
            ema_periods: List of periods for EMA calculations
            atr_period: Period for ATR calculation
            volume_period: Period for volume average calculation
        """
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.ema_periods = ema_periods or [9, 21, 50]
        self.atr_period = atr_period
        self.volume_period = volume_period
        
    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate all technical indicators used by the strategy.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with all calculated indicators
        """
        indicators = {}
        
        # Ensure we have the required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"DataFrame missing required column: {col}")
        
        try:
            # Calculate RSI
            delta = df['close'].diff()
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            avg_gain = gain.rolling(window=self.rsi_period).mean()
            avg_loss = abs(loss.rolling(window=self.rsi_period).mean())
            rs = avg_gain / avg_loss
            indicators['rsi'] = 100 - (100 / (1 + rs))
            
            # Calculate MACD
            ema_fast = df['close'].ewm(span=self.macd_fast).mean()
            ema_slow = df['close'].ewm(span=self.macd_slow).mean()
            indicators['macd_line'] = ema_fast - ema_slow
            indicators['signal_line'] = indicators['macd_line'].ewm(span=self.macd_signal).mean()
            indicators['macd_histogram'] = indicators['macd_line'] - indicators['signal_line']
            
            # Calculate EMAs
            for period in self.ema_periods:
                indicators[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            
            # Calculate ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            indicators['atr'] = true_range.rolling(window=self.atr_period).mean()
            
            # Calculate volume indicators
            indicators['volume_avg'] = df['volume'].rolling(window=self.volume_period).mean()
            indicators['volume_ratio'] = df['volume'] / indicators['volume_avg']
            
            # Calculate price rate of change
            indicators['price_roc'] = df['close'].pct_change(5) * 100
            
            # Calculate higher timeframe trend (simulated by using longer EMAs)
            indicators['trend'] = indicators['ema_50'] > indicators['ema_50'].shift(5)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            raise
        
    def generate_signal(self, df: pd.DataFrame) -> str:
        """
        Generate trading signal based on calculated indicators.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Signal string: 'BUY', 'SELL', or 'HOLD'
        """
        if len(df) < 50:  # Not enough data
            return 'HOLD'
            
        try:
            # Calculate indicators
            indicators = self.calculate_indicators(df)
            
            # Get the latest values for each indicator
            latest_idx = df.index[-1]
            
            # Extract latest values
            rsi = indicators['rsi'].iloc[-1]
            macd_line = indicators['macd_line'].iloc[-1]
            signal_line = indicators['signal_line'].iloc[-1]
            macd_histogram = indicators['macd_histogram'].iloc[-1]
            price = df['close'].iloc[-1]
            volume_ratio = indicators['volume_ratio'].iloc[-1]
            atr = indicators['atr'].iloc[-1]
            price_roc = indicators['price_roc'].iloc[-1]
            
            # Current price relation to EMAs
            ema_9 = indicators['ema_9'].iloc[-1]
            ema_21 = indicators['ema_21'].iloc[-1]
            ema_50 = indicators['ema_50'].iloc[-1]
            
            # Buy conditions
            buy_conditions = [
                rsi > 50,  # RSI bullish momentum
                rsi < 70,  # Not overbought
                macd_line > signal_line,  # MACD bullish crossover
                macd_histogram > 0,  # MACD histogram positive
                price > ema_50,  # Price above EMA trend
                volume_ratio > 1.0,  # Above average volume
                price_roc > 0  # Price rising
            ]
            
            # Sell conditions
            sell_conditions = [
                rsi < 50,  # RSI bearish momentum
                rsi > 30,  # Not oversold
                macd_line < signal_line,  # MACD bearish crossover
                macd_histogram < 0,  # MACD histogram negative
                price < ema_50,  # Price below EMA trend
                volume_ratio > 1.0,  # Above average volume
                price_roc < 0  # Price falling
            ]
            
            # Consensus logic - need at least 5/7 conditions
            if sum(buy_conditions) >= 5:
                return 'BUY'
            elif sum(sell_conditions) >= 5:
                return 'SELL'
            else:
                return 'HOLD'
                
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return 'HOLD'
    
    def get_signal_with_details(self, df: pd.DataFrame) -> Dict[str, Union[str, float]]:
        """
        Generate a detailed signal with all relevant information.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with signal details
        """
        if len(df) < 50:  # Not enough data
            return {'signal': 'HOLD', 'reason': 'Insufficient data'}
            
        try:
            # Calculate indicators
            indicators = self.calculate_indicators(df)
            
            # Get the latest values for each indicator
            latest_idx = df.index[-1] if not df.empty else None
            
            # Extract latest values
            rsi = indicators['rsi'].iloc[-1]
            macd_line = indicators['macd_line'].iloc[-1]
            signal_line = indicators['signal_line'].iloc[-1]
            macd_histogram = indicators['macd_histogram'].iloc[-1]
            price = df['close'].iloc[-1]
            volume_ratio = indicators['volume_ratio'].iloc[-1]
            atr = indicators['atr'].iloc[-1]
            
            # Current price relation to EMAs
            ema_9 = indicators['ema_9'].iloc[-1]
            ema_21 = indicators['ema_21'].iloc[-1]
            ema_50 = indicators['ema_50'].iloc[-1]
            
            # Calculate entry price - current price
            entry_price = price
            
            # Calculate stop loss and take profit based on ATR
            sl_multiplier = 1.5  # Default SL multiplier, can be optimized
            tp_ratio = 2.0  # Default TP:SL ratio, can be optimized
            
            stop_loss = entry_price - (atr * sl_multiplier)
            take_profit = entry_price + (atr * sl_multiplier * tp_ratio)
            
            # Calculate risk/reward ratio
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
            rr_ratio = reward / risk if risk > 0 else 0
            
            # Determine signal
            signal = self.generate_signal(df)
            
            # Build signal details
            details = {
                'signal': signal,
                'price': price,
                'rsi': rsi,
                'macd': macd_histogram,
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward': rr_ratio,
                'atr': atr,
                'volume_ratio': volume_ratio,
                'ema_trend': price > ema_50,
                'timestamp': latest_idx
            }
            
            # Add signal reason
            if signal == 'BUY':
                details['reason'] = "Bullish momentum with confirmation"
            elif signal == 'SELL':
                details['reason'] = "Bearish momentum with confirmation"
            else:
                details['reason'] = "Mixed signals, no clear direction"
                
            return details
            
        except Exception as e:
            logger.error(f"Error generating detailed signal: {e}")
            return {'signal': 'HOLD', 'reason': f'Error: {str(e)}'}
    
    def calculate_position_size(self, 
                               account_balance: float, 
                               risk_percent: float, 
                               entry_price: float, 
                               stop_loss: float) -> float:
        """
        Calculate position size based on account balance and risk.
        
        Args:
            account_balance: Total account balance
            risk_percent: Percentage of account to risk (0-100)
            entry_price: Entry price for the trade
            stop_loss: Stop loss price for the trade
            
        Returns:
            Position size in base currency
        """
        # Convert risk percentage to decimal
        risk_decimal = risk_percent / 100
        
        # Calculate risk amount
        risk_amount = account_balance * risk_decimal
        
        # Calculate price risk (difference between entry and stop loss)
        price_risk = abs(entry_price - stop_loss)
        
        # Calculate position size
        if price_risk > 0 and entry_price > 0:
            # Position size = risk amount / price risk
            position_size = risk_amount / price_risk
            
            # Convert to position size in base currency
            position_value = position_size * entry_price
            
            return position_value
        else:
            return 0.0

    def backtest(self, df: pd.DataFrame, 
                initial_balance: float = 10000, 
                risk_percent: float = 2.0) -> Dict[str, Union[float, List[Dict]]]:
        """
        Backtest the strategy on historical data.
        
        Args:
            df: DataFrame with OHLCV data
            initial_balance: Initial balance for backtesting
            risk_percent: Percentage of account to risk per trade
            
        Returns:
            Dictionary with backtest results
        """
        if len(df) < 50:
            return {
                'final_balance': initial_balance,
                'total_return_pct': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'trades': []
            }
            
        try:
            # Calculate indicators
            indicators = self.calculate_indicators(df)
            
            # Initialize backtest variables
            balance = initial_balance
            position = 0  # 0 = no position, 1 = long position
            entry_price = 0.0
            stop_loss = 0.0
            take_profit = 0.0
            trades = []
            daily_returns = []
            
            # Use a window to simulate trading
            for i in range(50, len(df)):
                current_date = df.index[i]
                price = df['close'].iloc[i]
                
                # Check if we have a position and need to exit
                if position == 1:
                    # Check for stop loss hit
                    if df['low'].iloc[i] <= stop_loss:
                        # Exit at stop loss
                        exit_price = stop_loss
                        profit_loss = (exit_price / entry_price - 1) * position_value
                        balance += position_value + profit_loss
                        
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'position_value': position_value,
                            'profit_loss': profit_loss,
                            'exit_type': 'stop_loss'
                        })
                        
                        position = 0
                        
                    # Check for take profit hit
                    elif df['high'].iloc[i] >= take_profit:
                        # Exit at take profit
                        exit_price = take_profit
                        profit_loss = (exit_price / entry_price - 1) * position_value
                        balance += position_value + profit_loss
                        
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': current_date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'position_value': position_value,
                            'profit_loss': profit_loss,
                            'exit_type': 'take_profit'
                        })
                        
                        position = 0
                
                # Check for entry signals if no position
                if position == 0:
                    # Get slice of data up to current point
                    data_slice = df.iloc[:i+1]
                    
                    # Generate signal
                    signal = self.generate_signal(data_slice)
                    
                    if signal == 'BUY':
                        entry_price = price
                        entry_date = current_date
                        
                        # Calculate stop loss and take profit
                        atr = indicators['atr'].iloc[i]
                        stop_loss = entry_price - (atr * 1.5)
                        take_profit = entry_price + (atr * 1.5 * 2.0)
                        
                        # Calculate position size
                        position_value = self.calculate_position_size(
                            balance, risk_percent, entry_price, stop_loss)
                        
                        # Enter position
                        balance -= position_value
                        position = 1
            
            # Close any open position at the end
            if position == 1:
                exit_price = df['close'].iloc[-1]
                profit_loss = (exit_price / entry_price - 1) * position_value
                balance += position_value + profit_loss
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': df.index[-1],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'position_value': position_value,
                    'profit_loss': profit_loss,
                    'exit_type': 'end_of_data'
                })
            
            # Calculate performance metrics
            total_return = balance - initial_balance
            total_return_pct = (balance / initial_balance - 1) * 100
            
            # Win rate
            winning_trades = [t for t in trades if t['profit_loss'] > 0]
            win_rate = len(winning_trades) / len(trades) if trades else 0
            
            # Calculate Sharpe ratio (simplified)
            if trades:
                returns = [t['profit_loss'] / t['position_value'] for t in trades]
                sharpe_ratio = np.mean(returns) / (np.std(returns) if np.std(returns) > 0 else 1) * np.sqrt(252)
            else:
                sharpe_ratio = 0
                
            # Calculate max drawdown
            # This is simplified - ideally would track equity curve
            if trades:
                cumulative_returns = np.cumsum([t['profit_loss'] for t in trades])
                max_dd = 0
                peak = cumulative_returns[0]
                
                for ret in cumulative_returns:
                    if ret > peak:
                        peak = ret
                    dd = (peak - ret) / peak if peak > 0 else 0
                    max_dd = max(max_dd, dd)
            else:
                max_dd = 0
                
            return {
                'final_balance': balance,
                'total_return': total_return,
                'total_return_pct': total_return_pct,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_dd * 100,  # Convert to percentage
                'win_rate': win_rate * 100,  # Convert to percentage
                'trades': trades,
                'num_trades': len(trades)
            }
                
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return {
                'final_balance': initial_balance,
                'total_return_pct': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'trades': []
            } 