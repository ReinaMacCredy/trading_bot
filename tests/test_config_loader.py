import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from src.config.config_loader import ConfigLoader


def test_exchange_config_defaults():
    loader = ConfigLoader("src/config/config.yml")
    config = loader.load_config()
    assert config.exchange.name == "binance"
    assert config.exchange.retry_delay == 1000
