import os
import logging
import yaml

logger = logging.getLogger("config_loader")

class ConfigLoader:
    """Configuration loader for the trading bot"""
    
    def __init__(self, config_path="src/config/config.yml"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self):
        """Load config from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                logger.error(f"Config file not found: {self.config_path}")
                return self._get_default_config()
                
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                logger.info(f"Config loaded from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
            
    def _get_default_config(self):
        """Return default configuration if file not found"""
        logger.warning("Using default configuration")
        return {
            "trading": {
                "risk_percentage": 2.0,
                "max_positions": 5,
                "max_daily_loss": 5.0,
                "trailing_stop": 1.5,
                "indicators": {
                    "rsi_period": 14,
                    "macd_fast": 12,
                    "macd_slow": 26, 
                    "macd_signal": 9,
                    "ema_periods": [12, 26, 50, 200]
                }
            },
            "discord": {
                "command_prefix": "b!",
                "embed_color": 0x7CFC00,
                "cooldown_seconds": 10,
                "cooldown_market_signals": 15
            },
            "security": {
                "encryption_enabled": False
            },
            "database": {
                "use_database": False,
                "type": "sqlite",
                "connection_string": "sqlite:///trading_bot.db"
            }
        }
        
    def get(self, section, key=None, default=None):
        """Get a config value by section and key"""
        if section not in self.config:
            logger.warning(f"Config section not found: {section}")
            return default
            
        if key is None:
            return self.config[section]
            
        if key not in self.config[section]:
            logger.warning(f"Config key not found: {section}.{key}")
            return default
            
        return self.config[section][key]
        
    def save_config(self):
        """Save current config to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False)
                logger.info(f"Config saved to {self.config_path}")
                return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

# Create a singleton instance
config = ConfigLoader() 