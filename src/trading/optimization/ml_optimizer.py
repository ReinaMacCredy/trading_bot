import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
import time
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.model_selection import TimeSeriesSplit, train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("Scikit-learn not available. ML optimization disabled.")
    SKLEARN_AVAILABLE = False

class MLOptimizer:
    """
    Machine learning based optimizer for trading strategy parameters.
    Adapts strategy parameters to current market conditions.
    """
    
    def __init__(self, 
                model_type: str = 'regressor',
                n_estimators: int = 100,
                random_state: int = 42,
                parameter_ranges: Dict[str, Tuple] = None,
                feature_columns: List[str] = None):
        """
        Initialize the ML optimizer.
        
        Args:
            model_type: Type of model to use ('regressor' or 'classifier')
            n_estimators: Number of estimators for the random forest
            random_state: Random state for reproducibility
            parameter_ranges: Dictionary of parameter names and (min, max) tuples
            feature_columns: List of feature columns to use for predictions
        """
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.random_state = random_state
        
        # Parameter ranges for optimization
        self.parameter_ranges = parameter_ranges or {
            'rsi_period': (9, 25),
            'macd_fast': (8, 20),
            'macd_slow': (20, 40),
            'ema_short': (5, 20),
            'ema_long': (20, 100),
            'sl_atr': (0.5, 3.0),
            'tp_ratio': (1.0, 4.0)
        }
        
        # Feature columns for market regime detection
        self.feature_columns = feature_columns or [
            'volatility', 'trend_strength', 'volume_ratio', 
            'rsi', 'macd', 'ema_ratio', 'market_regime'
        ]
        
        # Initialize model
        if SKLEARN_AVAILABLE:
            if model_type == 'regressor':
                self.model = RandomForestRegressor(
                    n_estimators=n_estimators,
                    random_state=random_state
                )
            else:
                self.model = RandomForestClassifier(
                    n_estimators=n_estimators,
                    random_state=random_state
                )
        else:
            self.model = None
            
        self.scaler = None
        self.is_fitted = False
        self.parameter_names = list(self.parameter_ranges.keys())
        self.best_params_by_regime = {}
        
    def prepare_features(self, market_data: pd.DataFrame) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Prepare features and parameter combinations for model training.
        
        Args:
            market_data: DataFrame with OHLCV data
            
        Returns:
            Tuple of (features array, parameter combinations list)
        """
        if not SKLEARN_AVAILABLE:
            logger.error("Scikit-learn not available. Cannot prepare features.")
            return np.array([]), []
            
        if market_data is None or market_data.empty:
            logger.error("No market data provided for feature preparation")
            return np.array([]), []
            
        try:
            # Calculate market regime features
            features_df = self._calculate_market_regime_features(market_data)
            
            # Generate parameter combinations for testing
            param_combinations = self._generate_parameter_combinations()
            
            # Create full feature dataset by combining market features with parameters
            all_features = []
            
            for market_idx, market_row in features_df.iterrows():
                for params in param_combinations:
                    # Combine market features with parameter values
                    feature_row = list(market_row.values) + list(params.values())
                    all_features.append(feature_row)
                    
            # Convert to numpy array
            features_array = np.array(all_features)
            
            # Create repeated list of parameter dictionaries
            param_dicts = []
            for _ in range(len(features_df)):
                param_dicts.extend(param_combinations)
                
            return features_array, param_dicts
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return np.array([]), []
            
    def _calculate_market_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate market regime features from OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with market regime features
        """
        try:
            # Ensure we have all needed columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"DataFrame missing required column: {col}")
                
            result = pd.DataFrame(index=df.index)
            
            # Volatility (20-day standard deviation of returns)
            result['volatility'] = df['close'].pct_change().rolling(20).std()
            
            # Trend strength (absolute value of 20-day price change)
            result['trend_strength'] = abs(df['close'].pct_change(20))
            
            # Volume ratio (current volume to 20-day average)
            result['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = abs(loss.rolling(window=14).mean())
            rs = avg_gain / avg_loss
            result['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            ema_12 = df['close'].ewm(span=12).mean()
            ema_26 = df['close'].ewm(span=26).mean()
            result['macd'] = ema_12 - ema_26
            
            # EMA ratio (9-day EMA to 50-day EMA)
            ema_9 = df['close'].ewm(span=9).mean()
            ema_50 = df['close'].ewm(span=50).mean()
            result['ema_ratio'] = ema_9 / ema_50
            
            # Market regime classification
            # 0 = ranging, 1 = trending up, 2 = trending down, 3 = volatile
            conditions = [
                (result['volatility'] > result['volatility'].quantile(0.8)),
                (result['trend_strength'] > result['trend_strength'].quantile(0.7)) & 
                (df['close'] > df['close'].shift(20)),
                (result['trend_strength'] > result['trend_strength'].quantile(0.7)) & 
                (df['close'] < df['close'].shift(20))
            ]
            choices = [3, 1, 2]
            result['market_regime'] = np.select(conditions, choices, default=0)
            
            # Fill NaN values
            result = result.fillna(method='bfill')
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating market regime features: {e}")
            empty_df = pd.DataFrame(index=df.index)
            for col in self.feature_columns:
                empty_df[col] = 0
            return empty_df
    
    def _generate_parameter_combinations(self, num_combinations: int = 50) -> List[Dict[str, Any]]:
        """
        Generate parameter combinations for testing.
        
        Args:
            num_combinations: Number of combinations to generate
            
        Returns:
            List of parameter combinations as dictionaries
        """
        combinations = []
        
        # For each combination, randomly select parameter values
        for _ in range(num_combinations):
            params = {}
            for name, (min_val, max_val) in self.parameter_ranges.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    params[name] = np.random.randint(min_val, max_val + 1)
                else:
                    params[name] = np.random.uniform(min_val, max_val)
            combinations.append(params)
            
        return combinations
    
    def fit(self, 
           features: np.ndarray, 
           parameter_dicts: List[Dict[str, Any]], 
           performance_scores: List[float]):
        """
        Fit the ML model to historical data.
        
        Args:
            features: Feature array (market conditions + parameters)
            parameter_dicts: List of parameter dictionaries
            performance_scores: List of performance scores for each parameter combination
        """
        if not SKLEARN_AVAILABLE:
            logger.error("Scikit-learn not available. Cannot fit model.")
            return
            
        try:
            # Check if we have enough data
            if len(features) < 10 or len(performance_scores) < 10:
                logger.warning("Not enough data to fit ML model")
                return
                
            # Create target array
            y = np.array(performance_scores)
            
            # Scale features
            self.scaler = StandardScaler()
            X = self.scaler.fit_transform(features)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=self.random_state
            )
            
            # Fit model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            if self.model_type == 'regressor':
                train_score = self.model.score(X_train, y_train)
                test_score = self.model.score(X_test, y_test)
                logger.info(f"Model fitted: R² train={train_score:.4f}, test={test_score:.4f}")
            else:
                train_preds = self.model.predict(X_train)
                test_preds = self.model.predict(X_test)
                train_score = accuracy_score(y_train, train_preds)
                test_score = accuracy_score(y_test, test_preds)
                logger.info(f"Model fitted: Accuracy train={train_score:.4f}, test={test_score:.4f}")
                
            self.is_fitted = True
            
            # Determine best parameters by market regime
            self._find_best_params_by_regime(features, parameter_dicts, performance_scores)
            
        except Exception as e:
            logger.error(f"Error fitting ML model: {e}")
    
    def _find_best_params_by_regime(self, 
                                  features: np.ndarray, 
                                  parameter_dicts: List[Dict[str, Any]], 
                                  performance_scores: List[float]):
        """
        Find the best parameters for each market regime.
        
        Args:
            features: Feature array (market conditions + parameters)
            parameter_dicts: List of parameter dictionaries
            performance_scores: List of performance scores for each parameter combination
        """
        # Get the market regime from the features
        regime_feature_idx = self.feature_columns.index('market_regime')
        
        # Group by market regime
        regimes = {}
        for i, score in enumerate(performance_scores):
            regime = int(features[i, regime_feature_idx])
            if regime not in regimes:
                regimes[regime] = {'scores': [], 'params': []}
            regimes[regime]['scores'].append(score)
            regimes[regime]['params'].append(parameter_dicts[i])
        
        # Find best parameters for each regime
        for regime, data in regimes.items():
            if data['scores']:
                best_idx = np.argmax(data['scores'])
                self.best_params_by_regime[regime] = data['params'][best_idx]
                
                logger.info(f"Best parameters for regime {regime}: {self.best_params_by_regime[regime]}")
    
    def predict_best_parameters(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Predict best parameters for current market conditions.
        
        Args:
            market_data: DataFrame with recent OHLCV data
            
        Returns:
            Dictionary of best parameters
        """
        if not SKLEARN_AVAILABLE:
            logger.error("Scikit-learn not available. Cannot predict parameters.")
            return self._get_default_parameters()
            
        if not self.is_fitted:
            logger.warning("Model not fitted yet. Using default parameters.")
            return self._get_default_parameters()
            
        try:
            # Calculate market regime features
            features_df = self._calculate_market_regime_features(market_data)
            
            # Get latest feature values
            current_features = features_df.iloc[-1].values
            
            # Detect current market regime
            current_regime = int(current_features[self.feature_columns.index('market_regime')])
            
            # If we have pre-computed best parameters for this regime, use them
            if current_regime in self.best_params_by_regime:
                logger.info(f"Using pre-computed best parameters for regime {current_regime}")
                return self.best_params_by_regime[current_regime]
            
            # Generate parameter combinations
            param_combinations = self._generate_parameter_combinations(100)
            
            # Create features for prediction
            prediction_features = []
            for params in param_combinations:
                # Combine market features with parameter values
                feature_row = list(current_features) + list(params.values())
                prediction_features.append(feature_row)
                
            X_pred = np.array(prediction_features)
            X_pred = self.scaler.transform(X_pred)
            
            # Predict performance
            predictions = self.model.predict(X_pred)
            
            # Find best parameters
            best_idx = np.argmax(predictions)
            best_params = param_combinations[best_idx]
            
            # Round integer parameters
            for key in best_params:
                if isinstance(self.parameter_ranges[key][0], int):
                    best_params[key] = int(round(best_params[key]))
                    
            logger.info(f"Predicted best parameters for current market conditions: {best_params}")
                    
            return best_params
            
        except Exception as e:
            logger.error(f"Error predicting parameters: {e}")
            return self._get_default_parameters()
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters (middle of each range)"""
        defaults = {}
        for name, (min_val, max_val) in self.parameter_ranges.items():
            if isinstance(min_val, int) and isinstance(max_val, int):
                defaults[name] = (min_val + max_val) // 2
            else:
                defaults[name] = (min_val + max_val) / 2
        return defaults
    
    def detect_market_regime(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect current market regime.
        
        Args:
            market_data: DataFrame with recent OHLCV data
            
        Returns:
            Dictionary with market regime information
        """
        try:
            # Calculate market regime features
            features_df = self._calculate_market_regime_features(market_data)
            
            # Get latest values
            latest = features_df.iloc[-1]
            
            # Classify regime
            regime_map = {
                0: 'Ranging',
                1: 'Trending Up',
                2: 'Trending Down',
                3: 'Volatile'
            }
            
            regime = int(latest['market_regime'])
            
            return {
                'regime': regime,
                'regime_name': regime_map.get(regime, 'Unknown'),
                'volatility': latest['volatility'],
                'trend_strength': latest['trend_strength'],
                'volume_ratio': latest['volume_ratio'],
                'rsi': latest['rsi'],
                'macd': latest['macd'],
                'ema_ratio': latest['ema_ratio']
            }
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return {
                'regime': 0,
                'regime_name': 'Unknown',
                'error': str(e)
            }
    
    def optimize_for_regime(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Optimize parameters based on current market regime.
        
        Args:
            market_data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with optimized parameters
        """
        # Detect market regime
        regime_info = self.detect_market_regime(market_data)
        
        # Get appropriate parameters
        if self.is_fitted:
            params = self.predict_best_parameters(market_data)
        else:
            params = self._get_default_parameters()
            
        # Combine results
        result = {
            'parameters': params,
            'market_regime': regime_info
        }
        
        return result 