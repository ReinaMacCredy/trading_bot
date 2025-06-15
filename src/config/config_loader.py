import os
import logging
import yaml
from dataclasses import dataclass, field, fields
from typing import Dict, List, Any, Optional, Type, TypeVar, get_type_hints
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("config_loader")

T = TypeVar('T')

@dataclass
class TradingConfig:
    """Trading configuration settings"""
    max_risk_per_trade: float = 0.02
    max_daily_loss: float = 0.05
    max_positions: int = 5
    position_size_method: str = "fixed_percentage"

@dataclass
class IndicatorConfig:
    """Technical indicators configuration"""
    rsi_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    ema_periods: List[int] = field(default_factory=lambda: [20, 50, 200])
    bb_period: int = 20
    bb_std_dev: int = 2
    atr_period: int = 14
    stoch_k_period: int = 14
    stoch_d_period: int = 3

@dataclass
class DiscordConfig:
    """Discord bot configuration"""
    command_prefix: str = "b!"
    channels: Dict[str, str] = field(default_factory=lambda: {
        "signals": "signals",
        "alerts": "alerts",
        "admin": "admin",
        "general": "general"
    })
    embed_colors: Dict[str, int] = field(default_factory=lambda: {
        "buy": 0x00FF00,
        "sell": 0xFF0000,
        "hold": 0xFFFF00,
        "info": 0x0099FF
    })
    rate_limits: Dict[str, int] = field(default_factory=lambda: {
        "commands_per_minute": 10,
        "signals_per_hour": 20
    })

@dataclass
class ExchangeConfig:
    """Exchange configuration settings"""
    name: str = "binance"
    sandbox: bool = True
    rate_limit: int = 1200
    retry_attempts: int = 3
    retry_delay: int = 1000  # milliseconds
    timeout: int = 10
    supported_exchanges: List[str] = field(default_factory=lambda: [
        "binance", "coinbase", "kraken", "bybit"
    ])

@dataclass
class MonitoringConfig:
    """Monitoring and alerts configuration"""
    health_check_interval: int = 300
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "cpu_usage": 80,
        "memory_usage": 80,
        "error_rate": 0.05
    })
    notifications: Dict[str, bool] = field(default_factory=lambda: {
        "discord_webhook": True,
        "email": False,
        "sms": False
    })
    enable_alerts: bool = True

@dataclass
class BotConfig:
    """Main bot configuration"""
    # Core configs
    trading: TradingConfig = field(default_factory=TradingConfig)
    indicators: IndicatorConfig = field(default_factory=IndicatorConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Environment variables with defaults
    discord_token: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN", ""))
    binance_api_key: str = field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    binance_secret: str = field(default_factory=lambda: os.getenv("BINANCE_SECRET", ""))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    
    # Trading symbols and timeframes
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "ADAUSDT"])
    timeframes: Dict[str, Any] = field(default_factory=lambda: {
        "primary": "1h",
        "secondary": "4h",
        "filters": ["15m", "1d"]
    })
    
    # Optional configs with simple defaults
    initial_balance: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.0005
    paper_trading_enabled: bool = True
    logging_level: str = "INFO"
    cache_enabled: bool = True
    cache_ttl: int = 300

class ConfigLoader:
    """Simple and functional configuration loader"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "src/config/config.yml")
        self._config: Optional[BotConfig] = None
    
    def load_config(self) -> BotConfig:
        """Load configuration from YAML file and environment variables"""
        try:
            yaml_data = self._load_yaml()
            config = self._create_config_from_yaml(yaml_data)
            self._apply_env_overrides(config)
            self._validate_config(config)
            
            self._config = config
            logger.info("Configuration loaded successfully")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
            return BotConfig()
    
    def _load_yaml(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found at {self.config_path}")
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except Exception as e:
            logger.error(f"Failed to parse YAML: {e}")
            return {}
    
    def _create_config_from_yaml(self, yaml_data: Dict[str, Any]) -> BotConfig:
        """Create configuration from YAML data using smart mapping"""
        config = BotConfig()
        
        # Map trading configuration
        if trading_data := yaml_data.get('trading'):
            config.trading = self._map_to_dataclass(
                TradingConfig, trading_data.get('risk_management', {})
            )
            
            # Map indicators with nested structure handling
            if indicators_data := trading_data.get('indicators'):
                config.indicators = self._map_indicators(indicators_data)
            
            # Simple direct mappings
            config.symbols = trading_data.get('symbols', config.symbols)
            config.timeframes = trading_data.get('timeframes', config.timeframes)
        
        # Map other configs directly
        if discord_data := yaml_data.get('discord'):
            config.discord = self._map_to_dataclass(DiscordConfig, discord_data)
        
        if exchange_data := yaml_data.get('exchanges', {}).get('binance'):
            config.exchange = self._map_to_dataclass(ExchangeConfig, exchange_data)
        
        if monitoring_data := yaml_data.get('monitoring'):
            config.monitoring = self._map_to_dataclass(MonitoringConfig, monitoring_data)
        
        # Map simple config values
        self._map_simple_configs(config, yaml_data)
        
        return config
    
    def _map_to_dataclass(self, cls: Type[T], data: Dict[str, Any]) -> T:
        """Generic function to map dictionary to dataclass"""
        if not data:
            return cls()
        
        try:
            # Get valid field names for the dataclass
            valid_fields = {f.name for f in fields(cls)} # type: ignore
            
            # Filter data to only include valid fields
            filtered_data = {k: v for k, v in data.items() if k in valid_fields}
            
            return cls(**filtered_data)
        except Exception as e:
            logger.warning(f"Failed to map {cls.__name__}: {e}")
            return cls()
    
    def _map_indicators(self, indicators_data: Dict[str, Any]) -> IndicatorConfig:
        """Map indicators configuration with nested structure handling"""
        config = IndicatorConfig()
        
        # RSI mapping
        if rsi_data := indicators_data.get('rsi'):
            config.rsi_period = rsi_data.get('period', config.rsi_period)
            config.rsi_overbought = rsi_data.get('overbought', config.rsi_overbought)
            config.rsi_oversold = rsi_data.get('oversold', config.rsi_oversold)
        
        # MACD mapping
        if macd_data := indicators_data.get('macd'):
            config.macd_fast = macd_data.get('fast_period', config.macd_fast)
            config.macd_slow = macd_data.get('slow_period', config.macd_slow)
            config.macd_signal = macd_data.get('signal_period', config.macd_signal)
        
        # EMA periods
        config.ema_periods = indicators_data.get('ema_periods', config.ema_periods)
        
        # Bollinger Bands
        if bb_data := indicators_data.get('bollinger_bands'):
            config.bb_period = bb_data.get('period', config.bb_period)
            config.bb_std_dev = bb_data.get('std_dev', config.bb_std_dev)
        
        # ATR
        if atr_data := indicators_data.get('atr'):
            config.atr_period = atr_data.get('period', config.atr_period)
        
        # Stochastic
        if stoch_data := indicators_data.get('stochastic'):
            config.stoch_k_period = stoch_data.get('k_period', config.stoch_k_period)
            config.stoch_d_period = stoch_data.get('d_period', config.stoch_d_period)
        
        return config
    
    def _map_simple_configs(self, config: BotConfig, yaml_data: Dict[str, Any]):
        """Map simple configuration values"""
        # Backtesting
        if bt_data := yaml_data.get('backtesting'):
            config.initial_balance = bt_data.get('initial_balance', config.initial_balance)
            config.commission = bt_data.get('commission', config.commission)
            config.slippage = bt_data.get('slippage', config.slippage)
        
        # Paper trading
        if pt_data := yaml_data.get('paper_trading'):
            config.paper_trading_enabled = pt_data.get('enabled', config.paper_trading_enabled)
        
        # Logging
        if log_data := yaml_data.get('logging'):
            config.logging_level = log_data.get('level', config.logging_level)
        
        # Performance
        if perf_data := yaml_data.get('performance'):
            config.cache_enabled = perf_data.get('cache_enabled', config.cache_enabled)
            config.cache_ttl = perf_data.get('cache_ttl', config.cache_ttl)
    
    def _apply_env_overrides(self, config: BotConfig):
        """Apply environment variable overrides"""
        # Environment variables that might override config
        env_overrides = {
            'SYMBOLS': lambda v: config.__setattr__('symbols', v.split(',')),
            'PRIMARY_TIMEFRAME': lambda v: config.timeframes.update({'primary': v}),
            'SANDBOX': lambda v: config.exchange.__setattr__('sandbox', v.lower() == 'true'),
            'MAX_RISK_PER_TRADE': lambda v: config.trading.__setattr__('max_risk_per_trade', float(v)),
            'COMMAND_PREFIX': lambda v: config.discord.__setattr__('command_prefix', v),
            'LOGGING_LEVEL': lambda v: setattr(config, 'logging_level', v),
        }
        
        for env_var, setter in env_overrides.items():
            if value := os.getenv(env_var):
                try:
                    setter(value)
                    logger.info(f"Applied environment override: {env_var}={value}")
                except Exception as e:
                    logger.warning(f"Failed to apply env override {env_var}: {e}")
    
    def _validate_config(self, config: BotConfig):
        """Validate configuration settings"""
        errors = []
        
        # Validate trading settings
        if not 0 < config.trading.max_risk_per_trade <= 1:
            errors.append("max_risk_per_trade must be between 0 and 1")
        
        if config.trading.max_positions <= 0:
            errors.append("max_positions must be greater than 0")
        
        # Validate symbols
        if not config.symbols:
            errors.append("At least one trading symbol must be configured")
        
        # Validate required environment variables for production
        if config.environment == "production":
            required_env = ['discord_token', 'binance_api_key', 'binance_secret']
            for env_var in required_env:
                if not getattr(config, env_var):
                    errors.append(f"Required environment variable {env_var} is missing")
        
        if errors:
            error_msg = "Configuration validation failed: " + "; ".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def get_config(self) -> BotConfig:
        """Get current configuration, loading if necessary"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def reload_config(self) -> BotConfig:
        """Reload configuration from file"""
        self._config = None
        return self.load_config()
    
    def update_config(self, updates: Dict[str, Any]) -> BotConfig:
        """Update specific configuration values"""
        config = self.get_config()
        
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
                logger.info(f"Updated config: {key}={value}")
            else:
                logger.warning(f"Unknown config key: {key}")
        
        return config

# Global config instance
_config_loader = ConfigLoader()

def get_config() -> BotConfig:
    """Get the global configuration instance"""
    return _config_loader.get_config()

def reload_config() -> BotConfig:
    """Reload the global configuration"""
    return _config_loader.reload_config() 

def update_config(updates: Dict[str, Any]) -> BotConfig:
    """Update the global configuration"""
    return _config_loader.update_config(updates)

# Convenience functions for specific config sections
def get_trading_config() -> TradingConfig:
    """Get trading configuration"""
    return get_config().trading

def get_discord_config() -> DiscordConfig:
    """Get Discord configuration"""
    return get_config().discord

def get_exchange_config() -> ExchangeConfig:
    """Get exchange configuration"""
    return get_config().exchange

def is_production() -> bool:
    """Check if running in production environment"""
    return get_config().environment == "production"

def is_sandbox() -> bool:
    """Check if using sandbox/testnet"""
    return get_config().exchange.sandbox 