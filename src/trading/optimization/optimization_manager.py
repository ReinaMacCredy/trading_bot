import logging
import pandas as pd
import numpy as np
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable

from .parameter_optimizer import ParameterOptimizer
from src.trading.strategies import MultiIndicatorStrategy
from .genetic_optimizer import GeneticOptimizer
from .ml_optimizer import MLOptimizer
from src.trading.core.risk_manager import DynamicRiskManager
from src.utils.performance import PerformanceTracker

logger = logging.getLogger(__name__)

class OptimizationManager:
    """
    Central manager for all trading strategy optimization techniques.
    Coordinates parameter optimization, genetic algorithms, machine learning,
    and risk management.
    """
    
    def __init__(self,
                exchange_client = None,
                config: Dict[str, Any] = None,
                data_dir: str = 'data',
                results_dir: str = 'results'):
        """
        Initialize the optimization manager.
        
        Args:
            exchange_client: Exchange client for fetching market data
            config: Configuration dictionary
            data_dir: Directory for storing data
            results_dir: Directory for storing optimization results
        """
        self.exchange_client = exchange_client
        self.config = config or {}
        self.data_dir = data_dir
        self.results_dir = results_dir
        
        # Ensure directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        
        # Initialize optimization components
        self._init_components()
        
        # Track optimization results
        self.optimization_history = []
        self.best_parameters = {}
        self.current_market_regime = None
        self.performance_tracker = PerformanceTracker()
        
    def _init_components(self):
        """Initialize optimization components"""
        # Initialize parameter optimizer
        self.param_optimizer = ParameterOptimizer(
            exchange_client=self.exchange_client,
            symbols=self.config.get('symbols', ['BTC/USDT', 'ETH/USDT']),
            timeframe=self.config.get('timeframe', '1h')
        )
        
        # Initialize genetic optimizer
        self.genetic_optimizer = GeneticOptimizer(
            population_size=self.config.get('population_size', 50),
            generations=self.config.get('generations', 50)
        )
        
        # Initialize ML optimizer
        self.ml_optimizer = MLOptimizer()
        
        # Initialize risk manager
        self.risk_manager = DynamicRiskManager(
            max_risk_per_trade=self.config.get('max_risk_per_trade', 0.02),
            max_daily_risk=self.config.get('max_daily_risk', 0.05),
            max_open_trades=self.config.get('max_open_trades', 5)
        )
        
        # Initialize trading strategy
        self.strategy = MultiIndicatorStrategy()
        
    def fetch_historical_data(self, 
                             symbol: str, 
                             timeframe: str = '1h', 
                             days: int = 30) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for data
            days: Number of days of data to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            if self.exchange_client is None:
                logger.warning("No exchange client, using mock data")
                return self._create_mock_data(days)
            
            # Calculate number of candles needed
            candles_per_day = 24 if timeframe == '1h' else (24 * 60 // int(timeframe[:-1]))
            limit = days * candles_per_day
            
            # Fetch data from exchange
            ohlcv = self.exchange_client.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Cache data
            self._cache_data(df, symbol, timeframe)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
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
    
    def _cache_data(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """Cache data to disk"""
        try:
            # Create clean filename
            symbol_clean = symbol.replace('/', '_')
            filename = f"{symbol_clean}_{timeframe}_{datetime.now().strftime('%Y%m%d')}.csv"
            filepath = os.path.join(self.data_dir, filename)
            
            # Save to disk
            df.to_csv(filepath)
            logger.info(f"Cached data to {filepath}")
            
        except Exception as e:
            logger.error(f"Error caching data: {e}")
    
    def run_parameter_optimization(self, symbols: List[str] = None, timeframe: str = None) -> Dict[str, Any]:
        """
        Run grid search parameter optimization.
        
        Args:
            symbols: List of symbols to optimize for
            timeframe: Timeframe for optimization
            
        Returns:
            Dictionary of optimized parameters
        """
        start_time = time.time()
        
        # Set default values
        symbols = symbols or ['BTC/USDT', 'ETH/USDT']
        timeframe = timeframe or '1h'
        
        logger.info(f"Running parameter optimization for {symbols} on {timeframe} timeframe")
        
        # Update param optimizer settings
        self.param_optimizer.symbols = symbols
        self.param_optimizer.timeframe = timeframe
        
        # Run optimization
        params = self.param_optimizer.optimize_parameters()
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Store results
        result = {
            'params': params,
            'symbols': symbols,
            'timeframe': timeframe,
            'elapsed_time': elapsed_time,
            'timestamp': datetime.now().isoformat()
        }
        
        self.optimization_history.append(result)
        self.best_parameters = params
        
        # Save results
        self._save_optimization_result(result, method='grid_search')
        
        return params
    
    def run_genetic_optimization(self, 
                               symbol: str, 
                               timeframe: str = '1h',
                               days: int = 30) -> Dict[str, Any]:
        """
        Run genetic algorithm optimization.
        
        Args:
            symbol: Symbol to optimize for
            timeframe: Timeframe for optimization
            days: Number of days of data to use
            
        Returns:
            Dictionary of optimization results
        """
        start_time = time.time()
        
        logger.info(f"Running genetic optimization for {symbol} on {timeframe} timeframe")
        
        # Fetch historical data
        data = self.fetch_historical_data(symbol, timeframe, days)
        
        # Define fitness function
        def fitness_function(params: Dict[str, Any]) -> float:
            try:
                # Create strategy with these parameters
                strategy = MultiIndicatorStrategy(
                    rsi_period=params['rsi_period'],
                    macd_fast=params['macd_fast'],
                    macd_slow=params['macd_slow'],
                    ema_periods=[params['ema_short'], params['ema_long']]
                )
                
                # Backtest strategy
                results = strategy.backtest(data)
                
                # Calculate fitness based on Sharpe ratio and win rate
                sharpe = results['sharpe_ratio']
                win_rate = results['win_rate'] / 100  # Convert to fraction
                return_pct = results['total_return_pct']
                
                # Prefer strategies with more trades
                trade_factor = min(1.0, results['num_trades'] / 10) if 'num_trades' in results else 0.5
                
                # Fitness function that rewards Sharpe, win rate, and return
                fitness = (sharpe * 0.5) + (win_rate * 0.3) + (return_pct * 0.02) + (trade_factor * 0.2)
                
                return max(0, fitness)  # Prevent negative fitness
                
            except Exception as e:
                logger.error(f"Error in fitness function: {e}")
                return 0.0
        
        # Set fitness function
        self.genetic_optimizer.set_fitness_function(fitness_function)
        
        # Run optimization
        result = self.genetic_optimizer.optimize()
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Store best parameters
        self.best_parameters = result['best_params']
        
        # Add extra info to result
        result.update({
            'symbol': symbol,
            'timeframe': timeframe,
            'data_days': days,
            'elapsed_time': elapsed_time,
            'timestamp': datetime.now().isoformat()
        })
        
        # Store in history
        self.optimization_history.append(result)
        
        # Save results
        self._save_optimization_result(result, method='genetic')
        
        return result
    
    def train_ml_optimizer(self, 
                          symbols: List[str], 
                          timeframe: str = '1h',
                          days: int = 60) -> bool:
        """
        Train ML optimizer on historical data.
        
        Args:
            symbols: List of symbols to train on
            timeframe: Timeframe to use
            days: Number of days of data to use
            
        Returns:
            Success flag
        """
        try:
            logger.info(f"Training ML optimizer on {symbols} with {timeframe} timeframe")
            
            all_features = []
            all_params = []
            all_scores = []
            
            # Process each symbol
            for symbol in symbols:
                # Fetch data
                data = self.fetch_historical_data(symbol, timeframe, days)
                
                # Prepare features
                features, params = self.ml_optimizer.prepare_features(data)
                
                # Calculate performance for each parameter set
                scores = []
                for param_dict in params:
                    # Create strategy with parameters
                    strategy = MultiIndicatorStrategy(
                        rsi_period=param_dict.get('rsi_period', 14),
                        macd_fast=param_dict.get('macd_fast', 12),
                        macd_slow=param_dict.get('macd_slow', 26),
                        ema_periods=[
                            param_dict.get('ema_short', 9), 
                            param_dict.get('ema_long', 50)
                        ]
                    )
                    
                    # Backtest
                    results = strategy.backtest(data)
                    
                    # Calculate score
                    sharpe = results['sharpe_ratio']
                    win_rate = results['win_rate'] / 100  # Convert to fraction
                    return_pct = results['total_return_pct']
                    
                    # Score function
                    score = (sharpe * 0.5) + (win_rate * 0.3) + (return_pct * 0.02)
                    scores.append(max(0, score))  # No negative scores
                
                # Append to main lists
                all_features.append(features)
                all_params.extend(params)
                all_scores.extend(scores)
            
            # Combine features from all symbols
            if all_features:
                combined_features = np.vstack(all_features)
                
                # Train the model
                self.ml_optimizer.fit(
                    features=combined_features,
                    parameter_dicts=all_params,
                    performance_scores=all_scores
                )
                
                logger.info("ML optimizer training completed successfully")
                return True
            else:
                logger.warning("No features generated for ML training")
                return False
                
        except Exception as e:
            logger.error(f"Error training ML optimizer: {e}")
            return False
    
    def optimize_for_market_conditions(self, 
                                     symbol: str, 
                                     timeframe: str = '1h') -> Dict[str, Any]:
        """
        Optimize parameters based on current market conditions.
        
        Args:
            symbol: Symbol to optimize for
            timeframe: Timeframe to use
            
        Returns:
            Dictionary with optimized parameters and market regime info
        """
        try:
            # Fetch recent data
            data = self.fetch_historical_data(symbol, timeframe, days=30)
            
            # Get market regime and parameters
            result = self.ml_optimizer.optimize_for_regime(data)
            
            # Store current market regime
            self.current_market_regime = result['market_regime']
            
            # Use the optimized parameters
            self.best_parameters = result['parameters']
            
            # Add metadata
            result.update({
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat()
            })
            
            # Store in history
            self.optimization_history.append(result)
            
            # Save results
            self._save_optimization_result(result, method='ml_regime')
            
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing for market conditions: {e}")
            return {
                'error': str(e),
                'parameters': self.param_optimizer.get_current_parameters(),
                'symbol': symbol,
                'timeframe': timeframe
            }
    
    def get_optimized_parameters(self) -> Dict[str, Any]:
        """Get current optimized parameters"""
        if not self.best_parameters:
            # Return default parameters
            return self.param_optimizer.get_current_parameters()
        return self.best_parameters
    
    def calculate_position_size(self, 
                              symbol: str, 
                              account_balance: float,
                              risk_percent: float = None) -> Dict[str, Any]:
        """
        Calculate optimal position size based on risk management.
        
        Args:
            symbol: Trading symbol
            account_balance: Current account balance
            risk_percent: Risk percentage override
            
        Returns:
            Dictionary with position sizing information
        """
        try:
            # Fetch recent data
            data = self.fetch_historical_data(symbol, '1h', days=10)
            
            # Get current price
            current_price = data['close'].iloc[-1]
            
            # Get strategy parameters
            params = self.get_optimized_parameters()
            
            # Create strategy with optimized parameters
            strategy = MultiIndicatorStrategy(
                rsi_period=params.get('rsi_period', 14),
                macd_fast=params.get('macd_fast', 12),
                macd_slow=params.get('macd_slow', 26)
            )
            
            # Get signal details
            signal_details = strategy.get_signal_with_details(data)
            
            # Get entry and stop loss prices
            entry_price = signal_details.get('entry', current_price)
            stop_loss = signal_details.get('stop_loss', entry_price * 0.95)  # Default 5% stop
            
            # Calculate position size
            if risk_percent is not None:
                # Use specified risk percentage
                position = self.risk_manager.calculate_position_size(
                    account_balance, entry_price, stop_loss, symbol)
            else:
                # Use dynamic risk management
                position = self.risk_manager.calculate_position_size(
                    account_balance, entry_price, stop_loss, symbol)
            
            # Add additional information
            position.update({
                'symbol': symbol,
                'current_price': current_price,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': signal_details.get('take_profit', entry_price * 1.1),
                'signal': signal_details.get('signal', 'HOLD'),
                'risk_reward': signal_details.get('risk_reward', 0)
            })
            
            return position
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {
                'size': 0,
                'error': str(e),
                'symbol': symbol
            }
    
    def get_market_regime(self, symbol: str, timeframe: str = '1h') -> Dict[str, Any]:
        """
        Get current market regime information.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe to analyze
            
        Returns:
            Dictionary with market regime details
        """
        try:
            # Fetch recent data
            data = self.fetch_historical_data(symbol, timeframe, days=30)
            
            # Detect market regime
            regime_info = self.ml_optimizer.detect_market_regime(data)
            
            # Store current market regime
            self.current_market_regime = regime_info
            
            # Add metadata
            regime_info.update({
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat()
            })
            
            return regime_info
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return {
                'error': str(e),
                'regime': 0,
                'regime_name': 'Unknown',
                'symbol': symbol
            }
    
    def update_risk_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update risk management settings.
        
        Args:
            settings: Dictionary with settings to update
            
        Returns:
            Dictionary with updated settings
        """
        result = self.risk_manager.update_risk_settings(settings)
        
        # Update config with new settings
        for key, value in settings.items():
            if key in self.config:
                self.config[key] = value
        
        return result
    
    def _save_optimization_result(self, result: Dict[str, Any], method: str):
        """
        Save optimization result to disk.
        
        Args:
            result: Result dictionary
            method: Optimization method name
        """
        try:
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"opt_{method}_{timestamp}.json"
            filepath = os.path.join(self.results_dir, filename)
            
            # Convert any non-serializable objects
            result_copy = {}
            for key, value in result.items():
                if isinstance(value, (int, float, str, bool, list, dict, type(None))):
                    result_copy[key] = value
                else:
                    result_copy[key] = str(value)
            
            # Save to disk
            with open(filepath, 'w') as f:
                json.dump(result_copy, f, indent=2)
                
            logger.info(f"Saved optimization result to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving optimization result: {e}")
    
    def load_optimization_result(self, filepath: str) -> Dict[str, Any]:
        """
        Load optimization result from disk.
        
        Args:
            filepath: Path to result file
            
        Returns:
            Result dictionary
        """
        try:
            with open(filepath, 'r') as f:
                result = json.load(f)
                
            # Update best parameters if available
            if 'params' in result:
                self.best_parameters = result['params']
            elif 'best_params' in result:
                self.best_parameters = result['best_params']
            elif 'parameters' in result:
                self.best_parameters = result['parameters']
                
            return result
            
        except Exception as e:
            logger.error(f"Error loading optimization result: {e}")
            return {}
    
    def schedule_optimizations(self, schedule_type: str = 'daily'):
        """
        Schedule regular optimizations.
        
        Args:
            schedule_type: Type of schedule ('daily', 'weekly', 'monthly')
        """
        # Schedule parameter optimization
        if schedule_type == 'daily':
            self.param_optimizer.schedule_optimization(day='daily', time='00:00')
        elif schedule_type == 'weekly':
            self.param_optimizer.schedule_optimization(day='monday', time='00:00')
        else:
            self.param_optimizer.schedule_optimization(day='monday', time='00:00')
            
        # Start scheduler
        self.param_optimizer.run_scheduler(blocking=False)
        
        logger.info(f"Scheduled {schedule_type} optimizations") 