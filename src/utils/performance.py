import time
import logging
import functools
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional

logger = logging.getLogger('performance')

def track_performance(func):
    """
    Decorator to track function performance
    
    Logs the execution time of the function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        logger.info("Function performance", 
                   function=func.__name__,
                   execution_time=execution_time)
        return result
    
    return wrapper


def async_track_performance(func):
    """
    Decorator to track async function performance
    
    Logs the execution time of the async function
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        logger.info("Function performance", 
                   function=func.__name__,
                   execution_time=execution_time)
        return result
    
    return wrapper


class PerformanceMetrics:
    """Class to track and report performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def record(self, name, value):
        """Record a metric value"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(value)
    
    def get_average(self, name):
        """Get the average value for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        
        return sum(self.metrics[name]) / len(self.metrics[name])
    
    def get_max(self, name):
        """Get the maximum value for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        
        return max(self.metrics[name])
    
    def get_min(self, name):
        """Get the minimum value for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        
        return min(self.metrics[name])
    
    def report(self):
        """Generate a report of all metrics"""
        report = {}
        
        for name, values in self.metrics.items():
            if not values:
                continue
                
            report[name] = {
                'count': len(values),
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values)
            }
        
        return report
    
    def reset(self):
        """Reset all metrics"""
        self.metrics = {}

# Create a global instance for convenience
performance_metrics = PerformanceMetrics() 


class PerformanceTracker:
    """
    Tracks and analyzes trading performance metrics.
    Calculates key performance indicators such as profit factor, 
    Sharpe ratio, max drawdown, win rate, etc.
    """
    
    def __init__(self):
        """Initialize the performance tracker"""
        self.reset()
        
    def reset(self):
        """Reset all performance metrics"""
        self.trades = []
        self.equity_curve = []
        self.drawdowns = []
        self.returns = []
        
    def add_trade(self, 
                 symbol: str,
                 entry_time: Any,
                 exit_time: Any,
                 entry_price: float,
                 exit_price: float,
                 position_size: float,
                 profit_loss: float,
                 trade_type: str = 'long',
                 fees: float = 0.0,
                 metadata: Dict = None):
        """
        Add a completed trade to the tracker.
        
        Args:
            symbol: Trading pair symbol
            entry_time: Entry timestamp
            exit_time: Exit timestamp
            entry_price: Entry price
            exit_price: Exit price
            position_size: Position size
            profit_loss: Profit/loss amount
            trade_type: 'long' or 'short'
            fees: Trading fees
            metadata: Additional trade metadata
        """
        trade = {
            'symbol': symbol,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position_size': position_size,
            'profit_loss': profit_loss,
            'trade_type': trade_type,
            'fees': fees,
            'metadata': metadata or {}
        }
        
        self.trades.append(trade)
        
        # Update equity and returns if we have enough data
        if self.equity_curve:
            self.equity_curve.append(self.equity_curve[-1] + profit_loss - fees)
            self.returns.append((profit_loss - fees) / self.equity_curve[-2] if self.equity_curve[-2] > 0 else 0)
        else:
            # First trade
            self.equity_curve.append(profit_loss - fees)
            self.returns.append(0)  # No previous equity to calculate return
            
        # Calculate drawdown
        if len(self.equity_curve) > 1:
            peak = max(self.equity_curve)
            current = self.equity_curve[-1]
            drawdown = (peak - current) / peak if peak > 0 else 0
            self.drawdowns.append(drawdown)
            
    def update_equity(self, current_equity: float):
        """
        Update equity curve without recording a trade.
        Used for tracking equity between trades.
        
        Args:
            current_equity: Current account equity
        """
        if self.equity_curve:
            # Calculate return
            prev_equity = self.equity_curve[-1]
            ret = (current_equity - prev_equity) / prev_equity if prev_equity > 0 else 0
            self.returns.append(ret)
        
        self.equity_curve.append(current_equity)
        
        # Calculate drawdown
        if len(self.equity_curve) > 1:
            peak = max(self.equity_curve)
            drawdown = (peak - current_equity) / peak if peak > 0 else 0
            self.drawdowns.append(drawdown)
            
    def get_metrics(self) -> Dict[str, Any]:
        """
        Calculate and return performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'total_return': 0,
                'profit_factor': 0,
                'win_rate': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'avg_trade': 0
            }
            
        # Basic metrics
        total_trades = len(self.trades)
        gross_profit = sum(t['profit_loss'] for t in self.trades if t['profit_loss'] > 0)
        gross_loss = sum(t['profit_loss'] for t in self.trades if t['profit_loss'] <= 0)
        total_fees = sum(t['fees'] for t in self.trades)
        net_profit = gross_profit + gross_loss - total_fees
        
        # Win/loss metrics
        winning_trades = [t for t in self.trades if t['profit_loss'] > 0]
        win_count = len(winning_trades)
        loss_count = total_trades - win_count
        win_rate = win_count / total_trades if total_trades > 0 else 0
        
        # Profit factor
        profit_factor = abs(gross_profit / gross_loss) if gross_loss < 0 else float('inf')
        
        # Returns and drawdowns
        if self.equity_curve:
            initial_equity = self.equity_curve[0]
            final_equity = self.equity_curve[-1]
            total_return = (final_equity / initial_equity - 1) if initial_equity > 0 else 0
            max_drawdown = max(self.drawdowns) if self.drawdowns else 0
        else:
            total_return = 0
            max_drawdown = 0
            
        # Risk-adjusted returns
        if len(self.returns) > 1:
            # Annualized metrics (assuming daily data)
            avg_return = np.mean(self.returns)
            std_return = np.std(self.returns)
            sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
            
        # Average trade metrics
        avg_trade = net_profit / total_trades if total_trades > 0 else 0
        avg_win = gross_profit / win_count if win_count > 0 else 0
        avg_loss = gross_loss / loss_count if loss_count > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': win_count,
            'losing_trades': loss_count,
            'win_rate': win_rate,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'total_fees': total_fees,
            'net_profit': net_profit,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_trade': avg_trade,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        } 