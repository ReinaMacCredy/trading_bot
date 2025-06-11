import logging
import pandas as pd
import numpy as np
import itertools
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import os
import json

logger = logging.getLogger(__name__)

class ParameterOptimizer:
    """
    Performs parameter optimization for trading strategies using grid search.
    Finds optimal parameters for technical indicators to maximize trading performance.
    """
    
    def __init__(self,
                exchange_client = None,
                symbols: List[str] = None,
                timeframe: str = '1h',
                data_dir: str = 'data',
                results_dir: str = 'results/optimizations'):
        """
        Initialize the parameter optimizer.
        
        Args:
            exchange_client: Exchange client for fetching market data
            symbols: List of trading pair symbols to optimize for
            timeframe: Timeframe for data analysis
            data_dir: Directory for storing data
            results_dir: Directory for storing optimization results
        """
        self.exchange_client = exchange_client
        self.symbols = symbols or ['BTC/USDT', 'ETH/USDT']
        self.timeframe = timeframe
        self.data_dir = data_dir
        self.results_dir = results_dir
        
        # Ensure directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        
        # Default parameter search spaces
        self.param_search_spaces = {
            'rsi_period': [7, 10, 14, 21],
            'macd_fast': [8, 12, 16],
            'macd_slow': [21, 26, 30],
            'macd_signal': [7, 9, 11],
            'ema_periods': [[9, 21, 50], [7, 21, 55], [8, 20, 50], [10, 25, 50]],
            'atr_period': [10, 14, 21],
            'volume_period': [10, 15, 20, 30]
        }
        
        # Store optimization results
        self.optimization_results = {}
        
    def optimize_parameters(self, 
                           days: int = 30,
                           metric: str = 'profit_factor') -> Dict[str, Any]:
        """
        Run grid search optimization to find optimal parameters.
        
        Args:
            days: Number of days of historical data to use
            metric: Performance metric to optimize for
                ('profit_factor', 'total_return', 'sharpe_ratio', etc.)
            
        Returns:
            Dictionary with optimized parameters
        """
        logger.info(f"Starting parameter optimization for {len(self.symbols)} symbols")
        
        # Results for each symbol
        symbol_results = {}
        
        try:
            for symbol in self.symbols:
                logger.info(f"Optimizing parameters for {symbol}")
                
                # Get historical data
                df = self._get_historical_data(symbol, days)
                if df is None or len(df) < 100:
                    logger.warning(f"Insufficient data for {symbol}, skipping")
                    continue
                
                # Run grid search
                symbol_results[symbol] = self._grid_search(df, metric)
                
            # Combine results across symbols
            optimized_params = self._aggregate_results(symbol_results)
            
            # Save results
            self._save_results(optimized_params)
            
            return optimized_params
            
        except Exception as e:
            logger.error(f"Error in parameter optimization: {e}")
            # Return default parameters if optimization fails
            return self._get_default_parameters()
    
    def _get_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical OHLCV data for a symbol"""
        try:
            if self.exchange_client is None:
                logger.warning(f"No exchange client available, using mock data for {symbol}")
                return self._create_mock_data(days)
                
            # Calculate number of candles
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
            logger.error(f"Error fetching data for {symbol}: {e}")
            return self._create_mock_data(days)
    
    def _create_mock_data(self, days: int) -> pd.DataFrame:
        """Create mock OHLCV data for testing"""
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
    
    def _grid_search(self, df: pd.DataFrame, metric: str) -> Dict[str, Any]:
        """
        Perform grid search over parameter combinations.
        
        Args:
            df: DataFrame with OHLCV data
            metric: Performance metric to optimize
            
        Returns:
            Dictionary with best parameters and performance metrics
        """
        # Generate parameter combinations
        param_combinations = self._generate_param_combinations()
        
        best_score = -float('inf')
        best_params = None
        best_metrics = None
        
        for params in param_combinations:
            # Configure strategy with these parameters
            from src.trading.multi_indicator_strategy import MultiIndicatorStrategy
            strategy = MultiIndicatorStrategy(
                rsi_period=params['rsi_period'],
                macd_fast=params['macd_fast'],
                macd_slow=params['macd_slow'],
                macd_signal=params['macd_signal'],
                ema_periods=params['ema_periods'],
                atr_period=params['atr_period'],
                volume_period=params['volume_period']
            )
            
            # Backtest strategy with these parameters
            backtest_result = strategy.backtest(df)
            
            # Extract the target metric
            score = backtest_result.get(metric, 0)
            
            # Update best parameters if this is better
            if score > best_score:
                best_score = score
                best_params = params
                best_metrics = {
                    'profit_factor': backtest_result.get('profit_factor', 0),
                    'total_return': backtest_result.get('total_return', 0),
                    'win_rate': backtest_result.get('win_rate', 0),
                    'max_drawdown': backtest_result.get('max_drawdown', 0),
                    'total_trades': backtest_result.get('total_trades', 0),
                    'sharpe_ratio': backtest_result.get('sharpe_ratio', 0)
                }
        
        return {
            'parameters': best_params,
            'metrics': best_metrics
        }
    
    def _generate_param_combinations(self) -> List[Dict[str, Any]]:
        """Generate combinations of parameters for grid search"""
        # Extract search spaces for all parameters except ema_periods
        keys = [k for k in self.param_search_spaces.keys() if k != 'ema_periods']
        values = [self.param_search_spaces[k] for k in keys]
        
        # Generate combinations for all parameters except ema_periods
        combinations = list(itertools.product(*values))
        
        # Create parameter dictionaries with all combinations
        param_combinations = []
        for combo in combinations:
            params = {keys[i]: combo[i] for i in range(len(keys))}
            
            # Add each ema_periods option
            for ema_periods in self.param_search_spaces['ema_periods']:
                params_with_ema = params.copy()
                params_with_ema['ema_periods'] = ema_periods
                param_combinations.append(params_with_ema)
        
        return param_combinations
    
    def _aggregate_results(self, symbol_results: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Aggregate results across multiple symbols.
        
        Args:
            symbol_results: Dictionary with results for each symbol
            
        Returns:
            Dictionary with aggregated parameters
        """
        if not symbol_results:
            return self._get_default_parameters()
            
        # Aggregate parameters using weighted average based on performance
        weighted_params = {}
        total_weight = 0
        
        for symbol, result in symbol_results.items():
            params = result.get('parameters')
            metrics = result.get('metrics')
            
            if not params or not metrics:
                continue
                
            # Use profit factor as weight
            weight = metrics.get('profit_factor', 0)
            if weight <= 0:
                weight = 0.1  # Minimum weight
                
            total_weight += weight
            
            # Add weighted parameters
            for key, value in params.items():
                if key not in weighted_params:
                    weighted_params[key] = 0
                    
                if key == 'ema_periods':
                    # Handle list parameter separately
                    if 'ema_periods_weighted' not in weighted_params:
                        weighted_params['ema_periods_weighted'] = []
                    weighted_params['ema_periods_weighted'].append((value, weight))
                else:
                    weighted_params[key] += value * weight
        
        # Normalize parameters
        if total_weight > 0:
            for key in weighted_params:
                if key != 'ema_periods_weighted':
                    weighted_params[key] = round(weighted_params[key] / total_weight)
            
            # Handle ema_periods - use most frequently selected with highest weights
            if 'ema_periods_weighted' in weighted_params:
                ema_weights = {}
                for ema_list, weight in weighted_params['ema_periods_weighted']:
                    ema_tuple = tuple(ema_list)  # Convert list to tuple for dict key
                    if ema_tuple not in ema_weights:
                        ema_weights[ema_tuple] = 0
                    ema_weights[ema_tuple] += weight
                
                # Select EMA periods with highest weight
                best_ema = max(ema_weights.items(), key=lambda x: x[1])[0]
                weighted_params['ema_periods'] = list(best_ema)  # Convert back to list
                del weighted_params['ema_periods_weighted']
        
        return {
            'parameters': weighted_params,
            'timestamp': datetime.now().isoformat(),
            'symbols': list(symbol_results.keys())
        }
    
    def _save_results(self, results: Dict[str, Any]):
        """Save optimization results to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            symbols_str = '_'.join([s.replace('/', '') for s in self.symbols[:2]])
            if len(self.symbols) > 2:
                symbols_str += f"_and_{len(self.symbols)-2}_more"
                
            filename = f"param_opt_{symbols_str}_{self.timeframe}_{timestamp}.json"
            filepath = os.path.join(self.results_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=4)
                
            logger.info(f"Saved optimization results to {filepath}")
            
            # Also save as latest result
            latest_path = os.path.join(self.results_dir, "latest_parameters.json")
            with open(latest_path, 'w') as f:
                json.dump(results, f, indent=4)
                
        except Exception as e:
            logger.error(f"Error saving optimization results: {e}")
            
    def _get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters if optimization fails"""
        return {
            'parameters': {
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'ema_periods': [9, 21, 50],
                'atr_period': 14,
                'volume_period': 20
            },
            'timestamp': datetime.now().isoformat(),
            'symbols': self.symbols,
            'note': 'Default parameters (optimization failed)'
        }
    
    def load_parameters(self, filepath: str = None) -> Dict[str, Any]:
        """
        Load saved parameters from file.
        
        Args:
            filepath: Path to parameters file
            
        Returns:
            Dictionary with parameters
        """
        try:
            # Default to latest parameters if filepath not provided
            if filepath is None:
                filepath = os.path.join(self.results_dir, "latest_parameters.json")
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Parameter file {filepath} not found, using defaults")
                return self._get_default_parameters()
                
        except Exception as e:
            logger.error(f"Error loading parameters: {e}")
            return self._get_default_parameters() 