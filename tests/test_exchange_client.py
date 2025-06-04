import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.trading import exchange_client as ec
from src.config.config_loader import ConfigLoader


class DummyExchange:
    def __init__(self, config=None):
        self.config = config
        self.apiKey = config.get("apiKey") if config else None


def test_exchange_client_uses_defaults(monkeypatch):
    # Patch ccxt.binance with dummy exchange
    import ccxt
    monkeypatch.setattr(ccxt, 'binance', DummyExchange, raising=False)
    loader = ConfigLoader("src/config/config.yml")
    config = loader.load_config()
    client = ec.ExchangeClient(config=config)
    assert config.exchange.name == "binance"
    assert config.exchange.retry_delay == 1000
    assert isinstance(client.exchange, DummyExchange)
