import logging
import numpy as np
import pandas as pd
import pickle
import os
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# FinRL and RL imports
try:
    from stable_baselines3 import PPO, A2C, SAC, TD3, DDPG
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.results_plotter import load_results, ts2xy
    import torch
    
    from finrl.meta.env_crypto_trading.env_cryptocurrencies import CryptoEnv
    from finrl.agents.stablebaselines3.models import DRLAgent
    
    SB3_AVAILABLE = True
except ImportError:
    logger.warning("Stable Baselines3 or FinRL not available. RL features disabled.")
    SB3_AVAILABLE = False

from src.trading.finrl_environment import CryptoTradingEnv, FinRLDataProcessor

class TradingCallback(BaseCallback):
    """
    Custom callback for monitoring trading performance during training.
    """
    def __init__(self, check_freq: int, save_path: str, verbose=1):
        super(TradingCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.save_path = save_path
        self.best_mean_reward = -np.inf

    def _init_callback(self) -> None:
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            # Get mean reward from monitor
            if hasattr(self.model, 'ep_info_buffer') and len(self.model.ep_info_buffer) > 0:
                mean_reward = np.mean([ep_info['r'] for ep_info in self.model.ep_info_buffer])
                
                if self.verbose > 0:
                    logger.info(f"Step {self.n_calls}: Mean reward: {mean_reward:.2f}")
                
                # Save best model
                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
                    if self.save_path is not None:
                        self.model.save(os.path.join(self.save_path, 'best_model'))
                        if self.verbose > 0:
                            logger.info(f"New best model saved with reward: {mean_reward:.2f}")
        
        return True

class RLAgentManager:
    """
    Manager for multiple reinforcement learning agents used in crypto trading.
    Supports PPO, A2C, SAC, TD3, and DDPG agents with ensemble capabilities.
    """
    
    def __init__(self, 
                 exchange_client=None,
                 config: Dict[str, Any] = None,
                 models_dir: str = 'models/rl',
                 results_dir: str = 'results/rl'):
        """
        Initialize the RL Agent Manager.
        
        Args:
            exchange_client: Exchange client for market data
            config: Configuration dictionary
            models_dir: Directory to save trained models
            results_dir: Directory to save training results
        """
        self.exchange_client = exchange_client
        self.config = config or {}
        self.models_dir = models_dir
        self.results_dir = results_dir
        
        # Ensure directories exist
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        
        # Available agent types
        self.agent_types = {
            'PPO': PPO if SB3_AVAILABLE else None,
            'A2C': A2C if SB3_AVAILABLE else None,
            'SAC': SAC if SB3_AVAILABLE else None,
            'TD3': TD3 if SB3_AVAILABLE else None,
            'DDPG': DDPG if SB3_AVAILABLE else None
        }
        
        # Initialize components
        self.data_processor = FinRLDataProcessor(
            symbols=self.config.get('symbols', ['BTC/USDT', 'ETH/USDT']),
            tech_indicator_list=self.config.get('tech_indicators', [
                'rsi', 'macd', 'ema_9', 'ema_21', 'ema_50', 
                'bb_upper', 'bb_lower', 'atr', 'volume_ratio'
            ])
        )
        
        # Store trained agents
        self.trained_agents = {}
        self.ensemble_weights = {}
        self.training_history = {}
        
        logger.info(f"RL Agent Manager initialized with {len(self.agent_types)} agent types")
        
    def prepare_training_data(self, 
                            symbols: List[str] = None, 
                            timeframe: str = '1h',
                            days: int = 365) -> pd.DataFrame:
        """
        Prepare training data for RL agents.
        
        Args:
            symbols: List of symbols to fetch data for
            timeframe: Timeframe for the data
            days: Number of days of historical data
            
        Returns:
            Processed DataFrame ready for RL training
        """
        try:
            symbols = symbols or self.config.get('symbols', ['BTC/USDT', 'ETH/USDT'])
            
            # Fetch historical data
            all_data = []
            
            for symbol in symbols:
                logger.info(f"Fetching data for {symbol}")
                
                if self.exchange_client:
                    # Fetch from exchange
                    since = datetime.now() - timedelta(days=days)
                    ohlcv = self.exchange_client.fetch_ohlcv(
                        symbol, timeframe, since=int(since.timestamp() * 1000)
                    )
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df['tic'] = symbol.replace('/', '')  # Remove slash for FinRL compatibility
                    
                else:
                    # Generate dummy data for testing
                    logger.warning(f"No exchange client, generating dummy data for {symbol}")
                    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
                    np.random.seed(42)
                    
                    # Generate realistic crypto price data
                    returns = np.random.normal(0.001, 0.05, len(dates))
                    price = 100 * np.exp(np.cumsum(returns))
                    
                    df = pd.DataFrame({
                        'date': dates,
                        'tic': symbol.replace('/', ''),
                        'open': price * (1 + np.random.normal(0, 0.001, len(dates))),
                        'high': price * (1 + np.abs(np.random.normal(0, 0.02, len(dates)))),
                        'low': price * (1 - np.abs(np.random.normal(0, 0.02, len(dates)))),
                        'close': price,
                        'volume': np.random.exponential(1000000, len(dates))
                    })
                
                all_data.append(df)
            
            # Combine all symbol data
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.sort_values(['date', 'tic']).reset_index(drop=True)
            
            # Process with technical indicators
            processed_df = self.data_processor.process_data(combined_df)
            
            logger.info(f"Prepared training data: {len(processed_df)} rows, {len(symbols)} symbols")
            return processed_df
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return pd.DataFrame()
    
    def create_trading_environment(self, 
                                 df: pd.DataFrame,
                                 initial_amount: float = 10000,
                                 transaction_cost_pct: float = 0.001) -> CryptoTradingEnv:
        """
        Create a trading environment for RL training.
        
        Args:
            df: Processed DataFrame with OHLCV and technical indicators
            initial_amount: Initial portfolio value
            transaction_cost_pct: Transaction cost percentage
            
        Returns:
            CryptoTradingEnv instance
        """
        try:
            env = CryptoTradingEnv(
                df=df,
                initial_amount=initial_amount,
                transaction_cost_pct=transaction_cost_pct,
                tech_indicator_list=self.data_processor.tech_indicator_list,
                mode='train'
            )
            
            logger.info(f"Created trading environment with observation space: {env.observation_space.shape}")
            return env
            
        except Exception as e:
            logger.error(f"Error creating trading environment: {e}")
            return None
    
    def train_agent(self, 
                   agent_type: str,
                   df: pd.DataFrame,
                   total_timesteps: int = 50000,
                   eval_freq: int = 5000,
                   save_freq: int = 10000) -> bool:
        """
        Train a specific RL agent.
        
        Args:
            agent_type: Type of agent ('PPO', 'A2C', 'SAC', 'TD3', 'DDPG')
            df: Training data
            total_timesteps: Total training timesteps
            eval_freq: Evaluation frequency
            save_freq: Model saving frequency
            
        Returns:
            Success flag
        """
        if not SB3_AVAILABLE:
            logger.error("Stable Baselines3 not available. Cannot train agents.")
            return False
            
        if agent_type not in self.agent_types:
            logger.error(f"Unknown agent type: {agent_type}")
            return False
            
        try:
            logger.info(f"Training {agent_type} agent...")
            
            # Create training environment
            train_env = self.create_trading_environment(df)
            if train_env is None:
                return False
                
            # Wrap environment
            train_env = Monitor(train_env, self.results_dir)
            train_env = DummyVecEnv([lambda: train_env])
            
            # Create validation environment (last 20% of data)
            split_idx = int(len(df) * 0.8)
            val_df = df.iloc[split_idx:].reset_index(drop=True)
            val_env = self.create_trading_environment(val_df)
            val_env = Monitor(val_env, self.results_dir)
            val_env = DummyVecEnv([lambda: val_env])
            
            # Initialize agent
            agent_class = self.agent_types[agent_type]
            
            # Agent-specific parameters
            if agent_type in ['PPO', 'A2C']:
                model = agent_class(
                    'MlpPolicy',
                    train_env,
                    verbose=1,
                    tensorboard_log=os.path.join(self.results_dir, 'tensorboard'),
                    device='auto'
                )
            elif agent_type in ['SAC', 'TD3', 'DDPG']:
                model = agent_class(
                    'MlpPolicy',
                    train_env,
                    verbose=1,
                    tensorboard_log=os.path.join(self.results_dir, 'tensorboard'),
                    device='auto',
                    buffer_size=100000,
                    learning_starts=1000
                )
            
            # Setup callbacks
            model_save_path = os.path.join(self.models_dir, agent_type.lower())
            os.makedirs(model_save_path, exist_ok=True)
            
            callback = TradingCallback(
                check_freq=save_freq,
                save_path=model_save_path,
                verbose=1
            )
            
            eval_callback = EvalCallback(
                val_env,
                best_model_save_path=model_save_path,
                log_path=self.results_dir,
                eval_freq=eval_freq,
                deterministic=True,
                render=False
            )
            
            # Train the model
            start_time = datetime.now()
            model.learn(
                total_timesteps=total_timesteps,
                callback=[callback, eval_callback],
                progress_bar=True
            )
            training_time = datetime.now() - start_time
            
            # Save final model
            final_model_path = os.path.join(model_save_path, 'final_model')
            model.save(final_model_path)
            
            # Store trained agent
            self.trained_agents[agent_type] = {
                'model': model,
                'model_path': final_model_path,
                'training_time': training_time,
                'trained_at': datetime.now()
            }
            
            # Update training history
            self.training_history[agent_type] = {
                'timesteps': total_timesteps,
                'training_time': training_time,
                'final_model_path': final_model_path,
                'completed_at': datetime.now().isoformat()
            }
            
            logger.info(f"{agent_type} agent training completed in {training_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error training {agent_type} agent: {e}")
            return False
    
    def load_trained_agent(self, agent_type: str, model_path: str = None) -> bool:
        """
        Load a pre-trained agent.
        
        Args:
            agent_type: Type of agent to load
            model_path: Path to the model file (optional)
            
        Returns:
            Success flag
        """
        if not SB3_AVAILABLE:
            logger.error("Stable Baselines3 not available. Cannot load agents.")
            return False
            
        try:
            if model_path is None:
                model_path = os.path.join(self.models_dir, agent_type.lower(), 'best_model')
            
            if not os.path.exists(model_path + '.zip'):
                logger.error(f"Model file not found: {model_path}.zip")
                return False
            
            # Load the model
            agent_class = self.agent_types[agent_type]
            model = agent_class.load(model_path)
            
            # Store loaded agent
            self.trained_agents[agent_type] = {
                'model': model,
                'model_path': model_path,
                'loaded_at': datetime.now()
            }
            
            logger.info(f"Successfully loaded {agent_type} agent from {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading {agent_type} agent: {e}")
            return False
    
    def predict_action(self, 
                      agent_type: str, 
                      market_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Get trading action prediction from a specific agent.
        
        Args:
            agent_type: Type of agent to use for prediction
            market_data: Current market data
            
        Returns:
            Dictionary with predicted actions and confidence
        """
        if agent_type not in self.trained_agents:
            logger.error(f"Agent {agent_type} not trained or loaded")
            return None
            
        try:
            # Process market data
            processed_data = self.data_processor.process_data(market_data)
            
            # Create environment for prediction
            pred_env = self.create_trading_environment(
                processed_data, 
                mode='test'
            )
            
            if pred_env is None:
                return None
            
            # Get current state
            obs = pred_env.reset()
            
            # Predict action
            model = self.trained_agents[agent_type]['model']
            action, _states = model.predict(obs, deterministic=True)
            
            # Convert action to trading signals
            symbols = processed_data['tic'].unique()
            predictions = {}
            
            for i, symbol in enumerate(symbols):
                if i < len(action):
                    # Action is typically in [-1, 1] range
                    action_value = float(action[i])
                    
                    if action_value > 0.3:
                        signal = 'BUY'
                        confidence = min(action_value, 1.0)
                    elif action_value < -0.3:
                        signal = 'SELL'
                        confidence = min(abs(action_value), 1.0)
                    else:
                        signal = 'HOLD'
                        confidence = 1.0 - abs(action_value)
                    
                    predictions[symbol] = {
                        'signal': signal,
                        'confidence': confidence,
                        'raw_action': action_value
                    }
            
            return {
                'agent_type': agent_type,
                'predictions': predictions,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting with {agent_type}: {e}")
            return None
    
    def ensemble_predict(self, 
                        market_data: pd.DataFrame,
                        agent_types: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get ensemble predictions from multiple agents.
        
        Args:
            market_data: Current market data
            agent_types: List of agent types to use (all if None)
            
        Returns:
            Dictionary with ensemble predictions
        """
        if agent_types is None:
            agent_types = list(self.trained_agents.keys())
        
        agent_predictions = {}
        
        # Get predictions from each agent
        for agent_type in agent_types:
            pred = self.predict_action(agent_type, market_data)
            if pred:
                agent_predictions[agent_type] = pred
        
        if not agent_predictions:
            logger.error("No agent predictions available for ensemble")
            return None
        
        try:
            # Combine predictions using weighted voting
            symbols = list(next(iter(agent_predictions.values()))['predictions'].keys())
            ensemble_predictions = {}
            
            for symbol in symbols:
                signal_votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
                confidence_sum = 0
                total_weight = 0
                
                for agent_type, prediction in agent_predictions.items():
                    if symbol in prediction['predictions']:
                        pred_data = prediction['predictions'][symbol]
                        weight = self.ensemble_weights.get(agent_type, 1.0)
                        
                        signal_votes[pred_data['signal']] += weight * pred_data['confidence']
                        confidence_sum += pred_data['confidence'] * weight
                        total_weight += weight
                
                # Determine ensemble signal
                final_signal = max(signal_votes, key=signal_votes.get)
                final_confidence = confidence_sum / total_weight if total_weight > 0 else 0
                
                ensemble_predictions[symbol] = {
                    'signal': final_signal,
                    'confidence': final_confidence,
                    'agent_votes': signal_votes
                }
            
            return {
                'ensemble_predictions': ensemble_predictions,
                'agent_predictions': agent_predictions,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating ensemble prediction: {e}")
            return None
    
    def update_ensemble_weights(self, performance_metrics: Dict[str, float]):
        """
        Update ensemble weights based on agent performance.
        
        Args:
            performance_metrics: Dictionary with agent performance scores
        """
        try:
            # Normalize performance scores to weights
            total_performance = sum(performance_metrics.values())
            
            if total_performance > 0:
                for agent_type, performance in performance_metrics.items():
                    self.ensemble_weights[agent_type] = performance / total_performance
            
            logger.info(f"Updated ensemble weights: {self.ensemble_weights}")
            
        except Exception as e:
            logger.error(f"Error updating ensemble weights: {e}")
    
    def get_training_status(self) -> Dict[str, Any]:
        """
        Get status of all trained agents.
        
        Returns:
            Dictionary with training status information
        """
        status = {
            'available_agents': list(self.agent_types.keys()),
            'trained_agents': list(self.trained_agents.keys()),
            'training_history': self.training_history,
            'ensemble_weights': self.ensemble_weights,
            'models_directory': self.models_dir,
            'results_directory': self.results_dir
        }
        
        return status
    
    def save_manager_state(self, filepath: str = None):
        """
        Save the manager state to file.
        
        Args:
            filepath: Path to save the state file
        """
        if filepath is None:
            filepath = os.path.join(self.models_dir, 'agent_manager_state.pkl')
        
        try:
            state = {
                'config': self.config,
                'ensemble_weights': self.ensemble_weights,
                'training_history': self.training_history,
                'models_dir': self.models_dir,
                'results_dir': self.results_dir
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(state, f)
            
            logger.info(f"Manager state saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving manager state: {e}")
    
    def load_manager_state(self, filepath: str = None):
        """
        Load the manager state from file.
        
        Args:
            filepath: Path to load the state file from
        """
        if filepath is None:
            filepath = os.path.join(self.models_dir, 'agent_manager_state.pkl')
        
        try:
            if not os.path.exists(filepath):
                logger.warning(f"State file not found: {filepath}")
                return
            
            with open(filepath, 'rb') as f:
                state = pickle.load(f)
            
            self.ensemble_weights = state.get('ensemble_weights', {})
            self.training_history = state.get('training_history', {})
            
            logger.info(f"Manager state loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading manager state: {e}") 