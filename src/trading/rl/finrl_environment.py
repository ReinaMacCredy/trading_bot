import gymnasium as gym
import numpy as np
import pandas as pd
import logging
from gymnasium import spaces
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class CryptoTradingEnv(gym.Env):
    """
    FinRL-compatible cryptocurrency trading environment for Discord trading bot.
    
    This environment integrates with the existing bot infrastructure and provides
    a standardized interface for training reinforcement learning agents.
    """
    
    def __init__(self, 
                 df: pd.DataFrame,
                 initial_amount: float = 10000,
                 transaction_cost_pct: float = 0.001,
                 tech_indicator_list: List[str] = None,
                 max_stock: int = 1,
                 lookback: int = 252,
                 day: int = 0,
                 turbulence_threshold: int = None,
                 risk_indicator_col: str = 'turbulence',
                 print_verbosity: int = 10,
                 iteration: str = '',
                 previous_state: List = None,
                 model_name: str = '',
                 mode: str = 'train',
                 env_config: Dict = None):
        """
        Initialize the trading environment.
        
        Args:
            df: DataFrame with OHLCV data and technical indicators
            initial_amount: Initial portfolio value
            transaction_cost_pct: Transaction cost as percentage
            tech_indicator_list: List of technical indicators to use
            max_stock: Maximum number of shares (set to 1 for crypto)
            lookback: Number of days to look back for features
            day: Starting day
            turbulence_threshold: Threshold for market volatility
            risk_indicator_col: Column name for risk indicator
            print_verbosity: Verbosity level for printing
            iteration: Training iteration identifier
            previous_state: Previous state for warm start
            model_name: Name of the RL model
            mode: 'train' or 'test'
            env_config: Additional environment configuration
        """
        # Environment parameters
        self.day = day
        self.lookback = lookback
        self.df = df
        self.initial_amount = initial_amount
        self.transaction_cost_pct = transaction_cost_pct
        self.max_stock = max_stock
        self.turbulence_threshold = turbulence_threshold
        self.risk_indicator_col = risk_indicator_col
        self.print_verbosity = print_verbosity
        self.iteration = iteration
        self.model_name = model_name
        self.mode = mode
        self.env_config = env_config or {}
        
        # Technical indicators
        if tech_indicator_list is None:
            self.tech_indicator_list = [
                'rsi', 'macd', 'ema_9', 'ema_21', 'ema_50', 
                'bb_upper', 'bb_lower', 'atr', 'volume_ratio'
            ]
        else:
            self.tech_indicator_list = tech_indicator_list
            
        # Data preprocessing
        self._prepare_data()
        
        # Environment state
        self.terminal = False
        self.portfolio_value = self.initial_amount
        self.asset_memory = [self.initial_amount]
        self.portfolio_return_memory = [0]
        self.actions_memory = []
        self.date_memory = []
        
        # Initialize state
        if previous_state is None:
            self.state = self._initiate_state()
        else:
            self.state = previous_state
            
        # Action and observation spaces
        self.action_space = spaces.Box(
            low=-1, 
            high=1, 
            shape=(len(self.df.tic.unique()),), 
            dtype=np.float32
        )
        
        # Observation space includes: balance, positions, prices, technical indicators
        observation_dim = (
            1 +  # balance
            len(self.df.tic.unique()) +  # positions
            len(self.df.tic.unique()) +  # prices
            len(self.df.tic.unique()) * len(self.tech_indicator_list)  # technical indicators
        )
        
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(observation_dim,),
            dtype=np.float32
        )
        
        # Trading parameters
        self.reward_scaling = 1e-4
        self.state_space = observation_dim
        self.action_space_dim = len(self.df.tic.unique())
        
        # Portfolio tracking
        self.stocks_owned = np.zeros(self.action_space_dim)
        self.stocks_price = np.array([0] * self.action_space_dim)
        
        logger.info(f"FinRL Crypto Trading Environment initialized")
        logger.info(f"Action space: {self.action_space}")
        logger.info(f"Observation space: {self.observation_space}")
        
    def _prepare_data(self):
        """Prepare and validate the trading data"""
        # Ensure required columns exist
        required_columns = ['date', 'tic', 'close', 'volume']
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"DataFrame missing required column: {col}")
                
        # Sort data by date and symbol
        self.df = self.df.sort_values(['date', 'tic']).reset_index(drop=True)
        
        # Get unique symbols and dates
        self.tic_list = list(self.df.tic.unique())
        self.trade_dates = list(self.df.date.unique())
        
        # Validate technical indicators
        missing_indicators = []
        for indicator in self.tech_indicator_list:
            if indicator not in self.df.columns:
                missing_indicators.append(indicator)
                
        if missing_indicators:
            logger.warning(f"Missing technical indicators: {missing_indicators}")
            # Remove missing indicators from the list
            self.tech_indicator_list = [
                ind for ind in self.tech_indicator_list 
                if ind not in missing_indicators
            ]
            
        logger.info(f"Trading symbols: {self.tic_list}")
        logger.info(f"Trading period: {self.trade_dates[0]} to {self.trade_dates[-1]}")
        logger.info(f"Technical indicators: {self.tech_indicator_list}")
        
    def _initiate_state(self):
        """Initialize the environment state"""
        if self.day >= len(self.trade_dates):
            self.terminal = True
            return None
            
        # Get current date's data
        current_date = self.trade_dates[self.day]
        current_data = self.df[self.df.date == current_date]
        
        # Initialize portfolio
        balance = self.initial_amount
        positions = np.zeros(len(self.tic_list))
        prices = current_data.close.values
        
        # Get technical indicators
        tech_indicators = []
        for indicator in self.tech_indicator_list:
            if indicator in current_data.columns:
                tech_indicators.extend(current_data[indicator].values)
            else:
                tech_indicators.extend(np.zeros(len(self.tic_list)))
                
        # Combine all state components
        state = np.concatenate([
            [balance],
            positions,
            prices,
            tech_indicators
        ])
        
        # Update tracking variables
        self.stocks_price = prices
        self.portfolio_value = balance + np.sum(positions * prices)
        
        return state.astype(np.float32)
        
    def step(self, actions):
        """Execute one trading step"""
        # Check if terminal
        if self.terminal:
            return self.state, 0, True, False, {}
            
        # Validate actions
        actions = np.array(actions).astype(np.float32)
        actions = np.clip(actions, -1, 1)  # Ensure actions are in valid range
        
        # Get current date and data
        current_date = self.trade_dates[self.day]
        current_data = self.df[self.df.date == current_date]
        current_prices = current_data.close.values
        
        # Calculate portfolio value before action
        portfolio_value_prev = self.portfolio_value
        
        # Execute trading actions
        self._execute_trades(actions, current_prices)
        
        # Update day
        self.day += 1
        
        # Check if episode is done
        done = self.day >= len(self.trade_dates) - 1
        
        if done:
            self.terminal = True
            
        # Get next state
        if not self.terminal:
            next_state = self._get_state()
        else:
            next_state = self.state
            
        # Calculate reward
        reward = self._calculate_reward(portfolio_value_prev)
        
        # Update memory
        self.asset_memory.append(self.portfolio_value)
        self.portfolio_return_memory.append(
            (self.portfolio_value - portfolio_value_prev) / portfolio_value_prev
        )
        self.actions_memory.append(actions)
        self.date_memory.append(current_date)
        
        # Update state
        self.state = next_state
        
        # Additional info
        info = {
            'portfolio_value': self.portfolio_value,
            'total_asset': self.portfolio_value,
            'reward': reward,
            'date': current_date,
            'actions': actions,
            'positions': self.stocks_owned.copy()
        }
        
        return self.state, reward, done, False, info
        
    def _execute_trades(self, actions, current_prices):
        """Execute trading actions"""
        # Calculate current portfolio value
        balance = self.state[0]
        current_positions = self.stocks_owned
        
        # Calculate transaction costs and new positions
        for i, action in enumerate(actions):
            price = current_prices[i]
            current_position = current_positions[i]
            
            # Determine trade size based on action
            if action > 0:  # Buy
                # Calculate maximum affordable quantity
                max_affordable = balance / price
                trade_quantity = min(action * max_affordable, max_affordable)
                
                if trade_quantity > 0:
                    # Execute buy order
                    cost = trade_quantity * price
                    transaction_cost = cost * self.transaction_cost_pct
                    total_cost = cost + transaction_cost
                    
                    if total_cost <= balance:
                        balance -= total_cost
                        current_positions[i] += trade_quantity
                        
            elif action < 0 and current_position > 0:  # Sell
                # Calculate sell quantity
                trade_quantity = min(abs(action) * current_position, current_position)
                
                if trade_quantity > 0:
                    # Execute sell order
                    proceeds = trade_quantity * price
                    transaction_cost = proceeds * self.transaction_cost_pct
                    net_proceeds = proceeds - transaction_cost
                    
                    balance += net_proceeds
                    current_positions[i] -= trade_quantity
                    
        # Update state
        self.stocks_owned = current_positions
        self.stocks_price = current_prices
        self.portfolio_value = balance + np.sum(current_positions * current_prices)
        
        # Update state vector
        self.state[0] = balance
        self.state[1:1+len(self.tic_list)] = current_positions
        self.state[1+len(self.tic_list):1+2*len(self.tic_list)] = current_prices
        
    def _get_state(self):
        """Get current environment state"""
        if self.day >= len(self.trade_dates):
            return self.state
            
        # Get current date's data
        current_date = self.trade_dates[self.day]
        current_data = self.df[self.df.date == current_date]
        
        # Get current prices
        current_prices = current_data.close.values
        
        # Get technical indicators
        tech_indicators = []
        for indicator in self.tech_indicator_list:
            if indicator in current_data.columns:
                tech_indicators.extend(current_data[indicator].values)
            else:
                tech_indicators.extend(np.zeros(len(self.tic_list)))
                
        # Update state with new prices and indicators
        balance = self.state[0]
        positions = self.stocks_owned
        
        # Combine all state components
        state = np.concatenate([
            [balance],
            positions,
            current_prices,
            tech_indicators
        ])
        
        # Update portfolio value
        self.portfolio_value = balance + np.sum(positions * current_prices)
        
        return state.astype(np.float32)
        
    def _calculate_reward(self, portfolio_value_prev):
        """Calculate reward for the current step"""
        # Portfolio return
        portfolio_return = (self.portfolio_value - portfolio_value_prev) / portfolio_value_prev
        
        # Risk-adjusted reward
        if len(self.portfolio_return_memory) > 1:
            # Calculate Sharpe-like ratio
            returns = np.array(self.portfolio_return_memory[-30:])  # Last 30 returns
            if len(returns) > 5 and np.std(returns) > 0:
                risk_adjusted_return = np.mean(returns) / np.std(returns)
                reward = portfolio_return + 0.1 * risk_adjusted_return
            else:
                reward = portfolio_return
        else:
            reward = portfolio_return
            
        # Apply reward scaling
        reward = reward * self.reward_scaling
        
        # Penalty for excessive trading (to prevent overfitting)
        if len(self.actions_memory) > 0:
            action_penalty = np.sum(np.abs(self.actions_memory[-1])) * 0.001
            reward -= action_penalty
            
        return reward
        
    def reset(self, seed=None, options=None):
        """Reset the environment"""
        # Reset day
        self.day = 0
        
        # Reset terminal flag
        self.terminal = False
        
        # Reset portfolio
        self.portfolio_value = self.initial_amount
        self.stocks_owned = np.zeros(self.action_space_dim)
        
        # Reset memory
        self.asset_memory = [self.initial_amount]
        self.portfolio_return_memory = [0]
        self.actions_memory = []
        self.date_memory = []
        
        # Reset state
        self.state = self._initiate_state()
        
        return self.state, {}
        
    def render(self, mode='human'):
        """Render the environment"""
        if mode == 'human':
            print(f"Day: {self.day}")
            print(f"Portfolio Value: ${self.portfolio_value:.2f}")
            print(f"Positions: {self.stocks_owned}")
            print(f"Current Prices: {self.stocks_price}")
            print("-" * 50)
            
    def get_sb_env(self):
        """Get environment for Stable Baselines3 compatibility"""
        return self
        
    def save_asset_memory(self):
        """Save portfolio performance memory"""
        date_list = self.date_memory
        asset_list = self.asset_memory
        portfolio_return = self.portfolio_return_memory
        
        df_account_value = pd.DataFrame({
            'date': date_list,
            'account_value': asset_list,
            'daily_return': portfolio_return
        })
        
        return df_account_value
        
    def save_action_memory(self):
        """Save action memory"""
        if len(self.actions_memory) > 0:
            date_list = self.date_memory
            df_actions = pd.DataFrame(self.actions_memory)
            df_actions['date'] = date_list
            df_actions.columns = [f'{tic}_action' for tic in self.tic_list] + ['date']
            return df_actions
        else:
            return pd.DataFrame()


class FinRLDataProcessor:
    """
    Data processor for FinRL integration with the Discord trading bot.
    Converts bot's market data format to FinRL-compatible format.
    """
    
    def __init__(self, 
                 symbols: List[str] = None,
                 tech_indicator_list: List[str] = None,
                 use_turbulence: bool = True,
                 user_defined_feature: bool = False):
        """
        Initialize the data processor.
        
        Args:
            symbols: List of trading symbols
            tech_indicator_list: List of technical indicators
            use_turbulence: Whether to calculate turbulence index
            user_defined_feature: Whether to use user-defined features
        """
        self.symbols = symbols or ['BTC/USDT', 'ETH/USDT']
        self.use_turbulence = use_turbulence
        self.user_defined_feature = user_defined_feature
        
        if tech_indicator_list is None:
            self.tech_indicator_list = [
                'rsi', 'macd', 'ema_9', 'ema_21', 'ema_50',
                'bb_upper', 'bb_lower', 'atr', 'volume_ratio'
            ]
        else:
            self.tech_indicator_list = tech_indicator_list
            
    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process data for FinRL compatibility.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Processed DataFrame suitable for FinRL
        """
        try:
            # Ensure required columns
            required_columns = ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"DataFrame missing required column: {col}")
                    
            # Rename columns to FinRL format
            df_processed = df.copy()
            df_processed = df_processed.rename(columns={
                'timestamp': 'date',
                'symbol': 'tic'
            })
            
            # Ensure date column is datetime
            if not pd.api.types.is_datetime64_any_dtype(df_processed['date']):
                df_processed['date'] = pd.to_datetime(df_processed['date'])
                
            # Sort by date and symbol
            df_processed = df_processed.sort_values(['date', 'tic']).reset_index(drop=True)
            
            # Add technical indicators if not present
            df_processed = self._add_technical_indicators(df_processed)
            
            # Add turbulence if requested
            if self.use_turbulence:
                df_processed = self._add_turbulence(df_processed)
                
            # Add VIX if available (crypto fear & greed index)
            df_processed = self._add_vix(df_processed)
            
            logger.info(f"Data processing completed. Shape: {df_processed.shape}")
            return df_processed
            
        except Exception as e:
            logger.error(f"Error in data processing: {e}")
            raise
            
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the DataFrame"""
        import pandas_ta as ta
        
        df_with_indicators = df.copy()
        
        # Group by symbol for indicator calculation
        for symbol in df['tic'].unique():
            symbol_data = df[df['tic'] == symbol].copy()
            
            # Calculate indicators
            if 'rsi' in self.tech_indicator_list and 'rsi' not in symbol_data.columns:
                symbol_data['rsi'] = ta.rsi(symbol_data['close'], length=14)
                
            if 'macd' in self.tech_indicator_list and 'macd' not in symbol_data.columns:
                macd = ta.macd(symbol_data['close'])
                symbol_data['macd'] = macd['MACD_12_26_9']
                
            if 'ema_9' in self.tech_indicator_list and 'ema_9' not in symbol_data.columns:
                symbol_data['ema_9'] = ta.ema(symbol_data['close'], length=9)
                
            if 'ema_21' in self.tech_indicator_list and 'ema_21' not in symbol_data.columns:
                symbol_data['ema_21'] = ta.ema(symbol_data['close'], length=21)
                
            if 'ema_50' in self.tech_indicator_list and 'ema_50' not in symbol_data.columns:
                symbol_data['ema_50'] = ta.ema(symbol_data['close'], length=50)
                
            if any(ind in self.tech_indicator_list for ind in ['bb_upper', 'bb_lower']):
                bb = ta.bbands(symbol_data['close'])
                if bb is not None:
                    symbol_data['bb_upper'] = bb['BBU_20_2.0']
                    symbol_data['bb_lower'] = bb['BBL_20_2.0']
                    
            if 'atr' in self.tech_indicator_list and 'atr' not in symbol_data.columns:
                symbol_data['atr'] = ta.atr(
                    symbol_data['high'], 
                    symbol_data['low'], 
                    symbol_data['close']
                )
                
            if 'volume_ratio' in self.tech_indicator_list and 'volume_ratio' not in symbol_data.columns:
                symbol_data['volume_ratio'] = symbol_data['volume'] / symbol_data['volume'].rolling(20).mean()
                
            # Update main dataframe
            df_with_indicators.loc[df_with_indicators['tic'] == symbol] = symbol_data
            
        # Fill NaN values
        df_with_indicators = df_with_indicators.fillna(method='ffill').fillna(0)
        
        return df_with_indicators
        
    def _add_turbulence(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add turbulence index for risk management"""
        try:
            from finrl.finrl_meta.preprocessor.yahoodownloader import YahooDownloader
            
            # Calculate turbulence based on price movements
            df_turbulence = df.copy()
            
            # Simple turbulence calculation
            for symbol in df['tic'].unique():
                symbol_data = df[df['tic'] == symbol].copy()
                
                # Calculate returns
                returns = symbol_data['close'].pct_change().fillna(0)
                
                # Rolling volatility as turbulence proxy
                turbulence = returns.rolling(20).std() * np.sqrt(252)
                
                df_turbulence.loc[df_turbulence['tic'] == symbol, 'turbulence'] = turbulence
                
            df_turbulence['turbulence'] = df_turbulence['turbulence'].fillna(0)
            
            return df_turbulence
            
        except Exception as e:
            logger.warning(f"Could not calculate turbulence: {e}")
            df['turbulence'] = 0
            return df
            
    def _add_vix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add VIX-like volatility index for crypto"""
        try:
            # Use average volatility across all symbols as VIX proxy
            df_vix = df.copy()
            
            # Calculate volatility for each symbol
            for date in df['date'].unique():
                date_data = df[df['date'] == date]
                
                volatilities = []
                for symbol in date_data['tic'].unique():
                    symbol_data = df[df['tic'] == symbol]
                    symbol_data = symbol_data[symbol_data['date'] <= date].tail(20)
                    
                    if len(symbol_data) > 5:
                        returns = symbol_data['close'].pct_change().dropna()
                        vol = returns.std() * np.sqrt(252) * 100  # Annualized volatility %
                        volatilities.append(vol)
                        
                # Average volatility as VIX
                vix_value = np.mean(volatilities) if volatilities else 20
                df_vix.loc[df_vix['date'] == date, 'vix'] = vix_value
                
            df_vix['vix'] = df_vix['vix'].fillna(20)
            
            return df_vix
            
        except Exception as e:
            logger.warning(f"Could not calculate VIX: {e}")
            df['vix'] = 20  # Default VIX value
            return df 