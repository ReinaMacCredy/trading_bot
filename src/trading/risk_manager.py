import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any

logger = logging.getLogger(__name__)

class DynamicRiskManager:
    """
    Dynamic risk management system that adjusts position sizing, stop losses,
    and risk parameters based on market volatility and account performance.
    """
    
    def __init__(self, 
                max_risk_per_trade: float = 0.02,  # 2% risk per trade
                max_daily_risk: float = 0.05,      # 5% max daily risk
                max_open_trades: int = 5,
                atr_period: int = 14,
                max_drawdown_limit: float = 0.15,  # 15% max drawdown
                volatility_scaling: bool = True):
        """
        Initialize the risk manager with parameters.
        
        Args:
            max_risk_per_trade: Maximum risk per trade as fraction of account (0-1)
            max_daily_risk: Maximum daily risk as fraction of account (0-1)
            max_open_trades: Maximum number of concurrent open trades
            atr_period: Period for ATR calculation
            max_drawdown_limit: Maximum allowed drawdown before reducing risk
            volatility_scaling: Whether to scale position size based on volatility
        """
        # Risk parameters
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_risk = max_daily_risk
        self.max_open_trades = max_open_trades
        self.max_drawdown_limit = max_drawdown_limit
        
        # Technical parameters
        self.atr_period = atr_period
        self.volatility_scaling = volatility_scaling
        
        # State tracking
        self.current_drawdown = 0.0
        self.peak_balance = 0.0
        self.daily_risk_used = 0.0
        self.open_trades = []
        self.trade_history = []
        self.risk_adjustment_factor = 1.0  # Scales risk based on performance
        self.last_risk_update = datetime.now()
        
    def calculate_atr(self, df: pd.DataFrame) -> float:
        """
        Calculate Average True Range (ATR) from price data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            ATR value
        """
        if len(df) < self.atr_period + 1:
            return 0.0
            
        try:
            # Calculate True Range
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            
            # Calculate ATR
            atr = true_range.rolling(window=self.atr_period).mean().iloc[-1]
            return atr
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return 0.0
    
    def calculate_position_size(self, 
                               account_balance: float, 
                               entry_price: float, 
                               stop_loss: float,
                               symbol: str = "") -> Dict[str, float]:
        """
        Calculate optimal position size based on risk parameters and volatility.
        
        Args:
            account_balance: Current account balance
            entry_price: Entry price for the trade
            stop_loss: Stop loss price for the trade
            symbol: Trading symbol (used for volatility adjustment)
            
        Returns:
            Dictionary with position details: size, risk_amount, risk_percent
        """
        # Check for valid prices
        if entry_price <= 0 or stop_loss <= 0:
            logger.error("Invalid prices for position sizing")
            return {'size': 0, 'risk_amount': 0, 'risk_percent': 0}
            
        # Calculate price risk (difference between entry and stop loss)
        price_risk_pct = abs(entry_price - stop_loss) / entry_price
        
        # Adjust risk based on current account state
        adjusted_risk = self.max_risk_per_trade * self.risk_adjustment_factor
        
        # Check daily risk limit
        remaining_risk = self.max_daily_risk - self.daily_risk_used
        if remaining_risk <= 0:
            logger.warning("Daily risk limit reached, no new positions allowed")
            return {'size': 0, 'risk_amount': 0, 'risk_percent': 0}
        
        # Use lower of remaining risk or per-trade risk
        risk_to_use = min(adjusted_risk, remaining_risk)
        
        # Calculate risk amount
        risk_amount = account_balance * risk_to_use
        
        # Calculate position size in base currency
        if price_risk_pct > 0:
            # Position value = risk amount / price risk percentage
            position_value = risk_amount / price_risk_pct
            
            # Position size in units
            position_size = position_value / entry_price
        else:
            position_size = 0
            position_value = 0
            
        return {
            'size': position_size,
            'value': position_value,
            'risk_amount': risk_amount,
            'risk_percent': risk_to_use * 100  # Convert to percentage
        }
    
    def calculate_stop_loss(self, 
                           df: pd.DataFrame, 
                           entry_price: float, 
                           direction: str,
                           atr_multiplier: float = 1.5) -> float:
        """
        Calculate dynamic stop loss based on ATR volatility.
        
        Args:
            df: DataFrame with OHLCV data
            entry_price: Entry price for the trade
            direction: Trade direction ('BUY' or 'SELL')
            atr_multiplier: Multiplier for ATR value
            
        Returns:
            Stop loss price
        """
        # Calculate ATR
        atr = self.calculate_atr(df)
        
        if atr == 0:
            # Fallback to fixed percentage if ATR calculation fails
            atr = entry_price * 0.02  # 2% of price
        
        # Calculate stop loss based on direction
        if direction.upper() == 'BUY':
            stop_loss = entry_price - (atr * atr_multiplier)
        else:  # SELL
            stop_loss = entry_price + (atr * atr_multiplier)
            
        return stop_loss
    
    def calculate_take_profit(self, 
                             entry_price: float, 
                             stop_loss: float, 
                             reward_risk_ratio: float = 2.0) -> float:
        """
        Calculate take profit level based on risk/reward ratio.
        
        Args:
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            reward_risk_ratio: Ratio of reward to risk
            
        Returns:
            Take profit price
        """
        # Calculate risk
        risk = abs(entry_price - stop_loss)
        
        # Calculate reward
        reward = risk * reward_risk_ratio
        
        # Calculate take profit based on direction (determined by stop loss position)
        if stop_loss < entry_price:  # Long position
            take_profit = entry_price + reward
        else:  # Short position
            take_profit = entry_price - reward
            
        return take_profit
    
    def update_account_state(self, 
                            current_balance: float, 
                            open_trades: List[Dict[str, Any]] = None):
        """
        Update account state for risk management.
        
        Args:
            current_balance: Current account balance
            open_trades: List of open trade details
        """
        # Update peak balance
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
        
        # Update drawdown
        if self.peak_balance > 0:
            self.current_drawdown = (self.peak_balance - current_balance) / self.peak_balance
        
        # Store open trades
        self.open_trades = open_trades or []
        
        # Update risk adjustment based on drawdown
        self._update_risk_parameters()
        
        # Reset daily risk used if it's a new day
        now = datetime.now()
        if now.date() > self.last_risk_update.date():
            self.daily_risk_used = 0.0
            self.last_risk_update = now
    
    def _update_risk_parameters(self):
        """Update risk parameters based on current account state"""
        # Reduce risk if drawdown exceeds thresholds
        if self.current_drawdown > self.max_drawdown_limit:
            # Progressively reduce risk as drawdown increases
            reduction_factor = 1 - ((self.current_drawdown - self.max_drawdown_limit) * 2)
            self.risk_adjustment_factor = max(0.25, reduction_factor)
            
            logger.info(f"High drawdown ({self.current_drawdown:.2%}), reducing risk to {self.risk_adjustment_factor:.2f}x")
        elif self.current_drawdown < self.max_drawdown_limit * 0.5:
            # If drawdown is low, gradually restore normal risk levels
            self.risk_adjustment_factor = min(1.0, self.risk_adjustment_factor + 0.05)
    
    def record_trade(self, trade: Dict[str, Any]):
        """
        Record a new trade for risk tracking.
        
        Args:
            trade: Trade details dictionary
        """
        self.trade_history.append(trade)
        
        # Add risk to daily risk used
        if 'risk_percent' in trade:
            self.daily_risk_used += trade['risk_percent'] / 100  # Convert from percentage
    
    def can_open_new_position(self, account_balance: float) -> Tuple[bool, str]:
        """
        Check if a new position can be opened based on risk constraints.
        
        Args:
            account_balance: Current account balance
            
        Returns:
            Tuple of (allowed, reason)
        """
        # Check max open trades
        if len(self.open_trades) >= self.max_open_trades:
            return False, f"Max open trades limit reached ({self.max_open_trades})"
        
        # Check daily risk limit
        if self.daily_risk_used >= self.max_daily_risk:
            return False, f"Daily risk limit reached ({self.max_daily_risk:.2%})"
        
        # Check drawdown limit
        if self.current_drawdown > self.max_drawdown_limit * 1.5:
            return False, f"Drawdown too high ({self.current_drawdown:.2%})"
            
        # All checks passed
        return True, "Position allowed"
    
    def calculate_trailing_stop(self, 
                               entry_price: float, 
                               current_price: float, 
                               initial_stop: float,
                               direction: str,
                               activation_pct: float = 0.01) -> float:
        """
        Calculate trailing stop level based on price movement.
        
        Args:
            entry_price: Entry price for the trade
            current_price: Current market price
            initial_stop: Initial stop loss level
            direction: Trade direction ('BUY' or 'SELL')
            activation_pct: Percentage move needed to activate trailing stop
            
        Returns:
            Updated stop loss price
        """
        if direction.upper() == 'BUY':
            # Long position - trailing stop moves up
            price_move = current_price - entry_price
            price_move_pct = price_move / entry_price
            
            # Only activate trailing stop if price has moved enough
            if price_move_pct >= activation_pct:
                # Calculate how much the stop should trail
                stop_trail = price_move - (entry_price * activation_pct)
                
                # Don't let stop go below initial stop
                new_stop = max(initial_stop, entry_price + stop_trail)
                return new_stop
            else:
                return initial_stop
        else:
            # Short position - trailing stop moves down
            price_move = entry_price - current_price
            price_move_pct = price_move / entry_price
            
            # Only activate trailing stop if price has moved enough
            if price_move_pct >= activation_pct:
                # Calculate how much the stop should trail
                stop_trail = price_move - (entry_price * activation_pct)
                
                # Don't let stop go above initial stop
                new_stop = min(initial_stop, entry_price - stop_trail)
                return new_stop
            else:
                return initial_stop
        
    def get_risk_info(self) -> Dict[str, Any]:
        """Get current risk management information"""
        return {
            'max_risk_per_trade': self.max_risk_per_trade * 100,  # to percentage
            'max_daily_risk': self.max_daily_risk * 100,  # to percentage
            'daily_risk_used': self.daily_risk_used * 100,  # to percentage
            'risk_adjustment': self.risk_adjustment_factor,
            'current_drawdown': self.current_drawdown * 100,  # to percentage
            'max_drawdown_limit': self.max_drawdown_limit * 100,  # to percentage
            'open_trades': len(self.open_trades),
            'max_open_trades': self.max_open_trades
        }
        
    def update_risk_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update risk management settings.
        
        Args:
            settings: Dictionary with settings to update
            
        Returns:
            Dictionary with updated settings
        """
        # Update values if provided
        if 'max_risk_per_trade' in settings:
            self.max_risk_per_trade = settings['max_risk_per_trade'] / 100  # from percentage
            
        if 'max_daily_risk' in settings:
            self.max_daily_risk = settings['max_daily_risk'] / 100  # from percentage
            
        if 'max_open_trades' in settings:
            self.max_open_trades = settings['max_open_trades']
            
        if 'max_drawdown_limit' in settings:
            self.max_drawdown_limit = settings['max_drawdown_limit'] / 100  # from percentage
            
        if 'volatility_scaling' in settings:
            self.volatility_scaling = settings['volatility_scaling']
            
        if 'atr_period' in settings:
            self.atr_period = settings['atr_period']
            
        # Return updated settings
        return self.get_risk_info()
        
    def calculate_kelly_position_size(self, 
                                     win_rate: float, 
                                     reward_risk_ratio: float, 
                                     account_balance: float,
                                     risk_modifier: float = 0.5) -> Dict[str, float]:
        """
        Calculate position size using Kelly Criterion.
        
        Args:
            win_rate: Historical win rate (0-1)
            reward_risk_ratio: Average reward to risk ratio
            account_balance: Current account balance
            risk_modifier: Factor to reduce Kelly size (often 0.5 for "half-Kelly")
            
        Returns:
            Dictionary with Kelly sizing information
        """
        # Ensure win_rate is valid
        if win_rate <= 0 or win_rate >= 1:
            logger.warning(f"Invalid win rate for Kelly calculation: {win_rate}")
            return {'kelly_fraction': 0, 'suggested_risk': 0, 'risk_amount': 0}
            
        # Calculate Kelly fraction
        kelly_fraction = (win_rate * reward_risk_ratio - (1 - win_rate)) / reward_risk_ratio
        
        # Apply risk modifier (half-Kelly is often recommended)
        adjusted_kelly = kelly_fraction * risk_modifier
        
        # Cap the maximum risk
        suggested_risk = min(adjusted_kelly, self.max_risk_per_trade)
        
        # Calculate risk amount
        risk_amount = account_balance * suggested_risk
        
        return {
            'kelly_fraction': kelly_fraction,
            'suggested_risk': suggested_risk,
            'risk_amount': risk_amount
        } 