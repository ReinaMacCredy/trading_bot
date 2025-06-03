import schedule
import time
import numpy as np
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class ParameterOptimizer:
    """
    Automatic parameter optimization framework that periodically optimizes
    trading strategy parameters based on recent market data.
    """
    
    def __init__(self, 
                optimization_window: int = 14,  # 2 weeks of data
                trading_window: int = 7,       # 1 week trading window
                exchange_client = None,
                symbols: List[str] = None,
                timeframe: str = '1h'):
        """
        Initialize the parameter optimizer.
        
        Args:
            optimization_window: Number of days of historical data to use for optimization
            trading_window: Number of days to use for forward testing
            exchange_client: Exchange client for fetching data
            symbols: List of trading symbols to optimize for
            timeframe: Timeframe to use for optimization
        """
        self.optimization_window = optimization_window
        self.trading_window = trading_window
        self.exchange_client = exchange_client
        self.symbols = symbols or ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        self.timeframe = timeframe
        self.current_params = {}
        self.optimization_history = []
        
    def fetch_recent_data(self, symbol: str, days: int) -> pd.DataFrame:
        """
        Fetch recent OHLCV data for the given symbol and timeframe.
        
        Args:
            symbol: Trading pair symbol
            days: Number of days of data to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.exchange_client:
            logger.warning("No exchange client provided, using mock data")
            # Create mock data for testing
            return self._create_mock_data(days)
        
        try:
            # Calculate number of candles needed
            candles_per_day = 24 if self.timeframe == '1h' else (24 * 60 // int(self.timeframe[:-1]))
            limit = days * candles_per_day
            
            # Fetch data from exchange
            ohlcv = self.exchange_client.fetch_ohlcv(symbol, self.timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return self._create_mock_data(days)
    
    def _create_mock_data(self, days: int) -> pd.DataFrame:
        """Create mock OHLCV data for testing purposes"""
        periods = days * 24  # Hourly data
        timestamps = pd.date_range(end=datetime.now(), periods=periods, freq='H')
        
        # Generate random price data with trend
        close = 10000 + np.cumsum(np.random.normal(0, 100, periods))
        
        # Create OHLCV data
        data = {
            'timestamp': timestamps,
            'open': close * (1 + np.random.normal(0, 0.005, periods)),
            'high': close * (1 + abs(np.random.normal(0, 0.01, periods))),
            'low': close * (1 - abs(np.random.normal(0, 0.01, periods))),
            'close': close,
            'volume': np.random.normal(5000, 1000, periods) * close / 10000
        }
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
        
    def optimize_parameters(self) -> Dict[str, Any]:
        """
        Optimize parameters based on recent market data.
        
        Returns:
            Dictionary of optimized parameters
        """
        logger.info("Starting parameter optimization")
        best_params_by_symbol = {}
        
        for symbol in self.symbols:
            logger.info(f"Optimizing parameters for {symbol}")
            
            try:
                # Fetch historical data
                recent_data = self.fetch_recent_data(symbol, self.optimization_window)
                
                # Split data into optimization and validation sets
                split_idx = int(len(recent_data) * 0.7)
                opt_data = recent_data.iloc[:split_idx]
                val_data = recent_data.iloc[split_idx:]
                
                # Grid search for optimal parameters
                best_params = self.grid_search_optimization(opt_data, val_data)
                best_params_by_symbol[symbol] = best_params
                
                logger.info(f"Optimized parameters for {symbol}: {best_params}")
            except Exception as e:
                logger.error(f"Error optimizing parameters for {symbol}: {e}")
        
        # Aggregate parameters across all symbols
        self.current_params = self._aggregate_parameters(best_params_by_symbol)
        
        # Store optimization history
        self.optimization_history.append({
            'timestamp': datetime.now(),
            'parameters': self.current_params.copy()
        })
        
        return self.current_params
    
    def grid_search_optimization(self, 
                               opt_data: pd.DataFrame, 
                               val_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform grid search to find optimal stop-loss and take-profit parameters.
        
        Args:
            opt_data: Data for optimization
            val_data: Data for validation
            
        Returns:
            Dictionary of best parameters
        """
        best_return = -float('inf')
        best_params = {}
        
        # Parameter ranges
        sl_atr_range = [0.5, 1.0, 1.5, 2.0, 2.5]
        tp_ratio_range = [1.5, 2.0, 2.5, 3.0, 3.5]
        rsi_period_range = [9, 14, 21]
        macd_fast_range = [8, 12, 16]
        macd_slow_range = [21, 26, 30]
        
        # Grid search for SL/TP parameters
        for sl_atr in sl_atr_range:
            for tp_ratio in tp_ratio_range:
                # Only test a subset of RSI/MACD parameters for efficiency
                for rsi_period in [14]:  # Just test the default for now
                    for macd_fast in [12]:  # Just test the default for now
                        for macd_slow in [26]:  # Just test the default for now
                            params = {
                                'sl_atr': sl_atr,
                                'tp_ratio': tp_ratio,
                                'rsi_period': rsi_period,
                                'macd_fast': macd_fast,
                                'macd_slow': macd_slow
                            }
                            
                            # Backtest on optimization data
                            returns = self.backtest_parameters(opt_data, params)
                            
                            # Validate on out-of-sample data
                            if returns > 0:  # Only validate promising parameters
                                val_returns = self.backtest_parameters(val_data, params)
                                
                                # Use both optimization and validation performance
                                combined_score = returns * 0.4 + val_returns * 0.6
                                
                                if combined_score > best_return:
                                    best_return = combined_score
                                    best_params = params.copy()
        
        # If no good parameters found, use defaults
        if not best_params:
            best_params = {
                'sl_atr': 1.5,
                'tp_ratio': 2.0,
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26
            }
        
        return best_params
                    
    def backtest_parameters(self, data: pd.DataFrame, params: Dict[str, Any]) -> float:
        """
        Backtest a set of parameters on historical data.
        
        Args:
            data: Historical price data
            params: Strategy parameters to test
            
        Returns:
            Performance metric (e.g., return, Sharpe ratio)
        """
        if len(data) < 50:
            return -float('inf')  # Not enough data
            
        try:
            # Calculate indicators
            # RSI
            delta = data['close'].diff()
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            avg_gain = gain.rolling(window=params['rsi_period']).mean()
            avg_loss = abs(loss.rolling(window=params['rsi_period']).mean())
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # MACD
            ema_fast = data['close'].ewm(span=params['macd_fast']).mean()
            ema_slow = data['close'].ewm(span=params['macd_slow']).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=9).mean()
            
            # ATR for stop loss
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            atr = true_range.rolling(window=14).mean()
            
            # Generate signals
            buy_signal = (rsi > 50) & (macd_line > signal_line)
            sell_signal = (rsi < 50) & (macd_line < signal_line)
            
            # Simulate trading
            position = 0
            entry_price = 0
            stop_loss = 0
            take_profit = 0
            trades = []
            
            for i in range(30, len(data)):
                # Skip if not enough data for indicators
                if np.isnan(rsi[i]) or np.isnan(macd_line[i]) or np.isnan(atr[i]):
                    continue
                    
                # If no position and buy signal
                if position == 0 and buy_signal[i]:
                    position = 1
                    entry_price = data['close'][i]
                    stop_loss = entry_price - (atr[i] * params['sl_atr'])
                    take_profit = entry_price + (atr[i] * params['sl_atr'] * params['tp_ratio'])
                
                # If in position
                elif position == 1:
                    # Check for stop loss
                    if data['low'][i] <= stop_loss:
                        trades.append((entry_price, stop_loss, 'stop'))
                        position = 0
                    
                    # Check for take profit
                    elif data['high'][i] >= take_profit:
                        trades.append((entry_price, take_profit, 'tp'))
                        position = 0
                    
                    # Check for sell signal
                    elif sell_signal[i]:
                        trades.append((entry_price, data['close'][i], 'signal'))
                        position = 0
            
            # Calculate returns
            if not trades:
                return 0  # No trades
                
            returns = [(exit_price / entry_price) - 1 for entry_price, exit_price, _ in trades]
            total_return = np.sum(returns)
            
            # Calculate risk-adjusted return (Sharpe-like)
            if len(returns) > 1:
                sharpe = total_return / (np.std(returns) + 1e-10)  # Avoid division by zero
                return sharpe
            else:
                return total_return
                
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return -float('inf')
    
    def _aggregate_parameters(self, params_by_symbol: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate parameters across multiple symbols to get overall optimal parameters.
        
        Args:
            params_by_symbol: Dictionary of parameters by symbol
            
        Returns:
            Aggregated parameters
        """
        if not params_by_symbol:
            return {
                'sl_atr': 1.5,
                'tp_ratio': 2.0,
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26
            }
            
        # Average parameters across symbols
        all_params = list(params_by_symbol.values())
        
        agg_params = {}
        for key in all_params[0].keys():
            values = [p[key] for p in all_params if key in p]
            agg_params[key] = float(np.median(values))  # Use median for robustness
            
            # Round integer parameters
            if key in ['rsi_period', 'macd_fast', 'macd_slow']:
                agg_params[key] = int(round(agg_params[key]))
        
        return agg_params
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """Get the current optimized parameters"""
        if not self.current_params:
            # Return default parameters
            return {
                'sl_atr': 1.5,
                'tp_ratio': 2.0,
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26
            }
        return self.current_params
    
    def schedule_optimization(self, day='monday', time='07:00'):
        """Schedule regular optimization"""
        if day.lower() == 'monday':
            schedule.every().monday.at(time).do(self.optimize_parameters)
        elif day.lower() == 'daily':
            schedule.every().day.at(time).do(self.optimize_parameters)
        else:
            schedule.every().week.day.at(time).do(self.optimize_parameters)
        
        logger.info(f"Scheduled parameter optimization for {day} at {time}")
        
    def run_scheduler(self, blocking=False):
        """Run the scheduler in a separate thread"""
        if blocking:
            while True:
                schedule.run_pending()
                time.sleep(60)
        else:
            import threading
            thread = threading.Thread(target=self._scheduler_worker, daemon=True)
            thread.start()
            
    def _scheduler_worker(self):
        """Worker function for running the scheduler in a separate thread"""
        while True:
            schedule.run_pending()
            time.sleep(60) 