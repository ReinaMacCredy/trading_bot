"""Trading indicator modules."""

from .indicators import TechnicalIndicators, IndicatorResult
from .legacy_indicators import (
    Indicator,
    EMAIndicator,
    RSIIndicator,
    MACDIndicator,
    BollingerBandsIndicator,
    DualMACD_RSI_Strategy,
    IndicatorFactory
)

__all__ = [
    "TechnicalIndicators",
    "IndicatorResult",
    "Indicator",
    "EMAIndicator",
    "RSIIndicator",
    "MACDIndicator",
    "BollingerBandsIndicator",
    "DualMACD_RSI_Strategy",
    "IndicatorFactory"
] 