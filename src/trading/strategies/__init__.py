"""Trading strategy modules."""

from .multi_indicator_strategy import MultiIndicatorStrategy
from .strategies import (
    BaseStrategy,
    MACDRSIStrategy,
    BollingerBandsStrategy,
    MultiTimeframeStrategy,
    StrategyManager,
    TradingSignal,
    BacktestResult
)
from .legacy_strategies import (
    TradingStrategy,
    MovingAverageCrossover,
    RSIStrategy,
    BollingerBandsStrategy as LegacyBollingerBandsStrategy,
    MACDRSIStrategy as LegacyMACDRSIStrategy,
    SCStrategySignal,
    get_strategy
)

__all__ = [
    "MultiIndicatorStrategy",
    "BaseStrategy",
    "MACDRSIStrategy",
    "BollingerBandsStrategy",
    "MultiTimeframeStrategy",
    "StrategyManager",
    "TradingSignal",
    "BacktestResult",
    "TradingStrategy",
    "MovingAverageCrossover",
    "RSIStrategy",
    "LegacyBollingerBandsStrategy",
    "LegacyMACDRSIStrategy",
    "SCStrategySignal",
    "get_strategy"
] 