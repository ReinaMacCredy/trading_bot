# Commands Reference

This document provides a complete reference for all Discord bot commands available in the Professional Discord Trading Bot.

## 🎯 Command Prefix

All commands use the prefix **`b!`**

## 📊 Signal Generation Commands

### `b!generate_signal <symbol> [strategy] [risk_reward]`

Generates a trading signal with real market data using advanced technical analysis.

**Parameters:**
- `symbol` (required): Trading pair symbol (e.g., BTC, ETH, BTCUSDT)
- `strategy` (optional): Strategy to use (default: SC02)
- `risk_reward` (optional): Risk/reward ratio (default: 2.5)

**Available Strategies:**
- `SC02`: MACD + RSI strategy
- `bollinger_bands`: Bollinger Bands strategy
- `ema_crossover`: EMA crossover strategy

**Examples:**
```
b!generate_signal BTC
b!generate_signal ETH SC02 3.0
b!generate_signal BTCUSDT bollinger_bands 2.0
```

**Output:** Professional signal format with entry, stop-loss, take-profit levels, and confidence score.

---

### `b!market_signals [count]`

Generates trading signals for multiple top market cap cryptocurrencies.

**Parameters:**
- `count` (optional): Number of signals to generate (default: 5, max: 20)

**Example:**
```
b!market_signals 10
```

**Output:** List of signals for top cryptocurrencies with performance metrics.

---

### `b!live_signal [channel_id]`

Sends a live trading signal to the specified Discord channel.

**Parameters:**
- `channel_id` (optional): Target channel ID (uses current channel if not specified)

**Example:**
```
b!live_signal 123456789012345678
```

**Requirements:** Bot must have send message permissions in the target channel.

## 📈 Technical Analysis Commands

### `b!dual_macd_rsi <symbol> [interval] [higher_tf]`

Performs dual timeframe MACD + RSI analysis for enhanced signal accuracy.

**Parameters:**
- `symbol` (required): Trading pair symbol
- `interval` (optional): Primary timeframe (default: 1h)
- `higher_tf` (optional): Higher timeframe (default: 4h)

**Available Intervals:**
- `1m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `12h`, `1d`, `3d`, `1w`

**Example:**
```
b!dual_macd_rsi BTC 1h 4h
b!dual_macd_rsi ETH 15m 1h
```

**Output:** Comprehensive analysis with both timeframes and confluence signals.

---

### `b!market_regime <symbol> [timeframe]`

Detects market regime and optimizes parameters accordingly.

**Parameters:**
- `symbol` (required): Trading pair symbol
- `timeframe` (optional): Analysis timeframe (default: 1h)

**Example:**
```
b!market_regime BTC 4h
```

**Output:** Market regime classification (trending, ranging, volatile) with optimized parameters.

---

### `b!indicator <indicator> <symbol> [interval] [params]`

Analyzes specific technical indicators with customizable parameters.

**Parameters:**
- `indicator` (required): Indicator type
- `symbol` (required): Trading pair symbol
- `interval` (optional): Timeframe (default: 1h)
- `params` (optional): Custom parameters

**Available Indicators:**
- `rsi`: RSI with period and overbought/oversold levels
- `macd`: MACD with fast, slow, and signal periods
- `ema`: EMA with period
- `bollinger`: Bollinger Bands with period and standard deviation
- `atr`: Average True Range with period

**Examples:**
```
b!indicator rsi BTC 1h 14 30 70
b!indicator macd ETH 4h 12 26 9
b!indicator bollinger BTC 1h 20 2.0
```

**Output:** Detailed indicator analysis with buy/sell signals.

## ⚖️ Risk Management Commands

### `b!risk_settings [risk] [daily_loss] [trailing_stop]`

Updates risk management parameters for trading.

**Parameters:**
- `risk` (optional): Risk per trade as percentage (default: 2%)
- `daily_loss` (optional): Maximum daily loss percentage (default: 5%)
- `trailing_stop` (optional): Trailing stop percentage (default: 1.5%)

**Examples:**
```
b!risk_settings 1.5 3 1.0
b!risk_settings 2.5
```

**Output:** Updated risk parameters confirmation.

---

### `b!position_size <symbol> <entry> <stop_loss>`

Calculates optimal position size based on risk management rules.

**Parameters:**
- `symbol` (required): Trading pair symbol
- `entry` (required): Entry price
- `stop_loss` (required): Stop-loss price

**Example:**
```
b!position_size BTC 60000 58500
```

**Output:** Recommended position size, risk amount, and risk percentage.

---

### `b!position_size_advanced <symbol> [balance] [risk_percent]`

Advanced position sizing with dynamic risk calculation.

**Parameters:**
- `symbol` (required): Trading pair symbol
- `balance` (optional): Account balance (uses actual if not specified)
- `risk_percent` (optional): Risk percentage (uses settings if not specified)

**Example:**
```
b!position_size_advanced BTC 1000 2.0
```

**Output:** Advanced position sizing with multiple scenarios and ATR-based stops.

## 🔧 Optimization Commands

### `b!optimize_params [symbol] [timeframe]`

Performs grid search parameter optimization for trading strategies.

**Parameters:**
- `symbol` (optional): Trading pair symbol (default: BTC)
- `timeframe` (optional): Timeframe for optimization (default: 1h)

**Example:**
```
b!optimize_params ETH 4h
```

**Output:** Optimized parameters with performance metrics and backtesting results.

---

### `b!genetic_optimize <symbol> [timeframe] [generations]`

Uses genetic algorithm for strategy parameter optimization.

**Parameters:**
- `symbol` (required): Trading pair symbol
- `timeframe` (optional): Timeframe (default: 1h)
- `generations` (optional): Number of generations (default: 20)

**Example:**
```
b!genetic_optimize ETH 1h 30
```

**Output:** Evolution progress and final optimized parameters.

## 💰 Trading Commands

### `b!advanced_buy <symbol> <quantity> [tp] [sl]`

Places an advanced buy order with automatic take-profit and stop-loss.

**Parameters:**
- `symbol` (required): Trading pair symbol
- `quantity` (required): Quantity to buy
- `tp` (optional): Take-profit price
- `sl` (optional): Stop-loss price

**Example:**
```
b!advanced_buy BTC 0.01 61500 58500
```

**Output:** Order confirmation with all order details.

---

### `b!price <symbol>`

Gets current market price for the specified symbol.

**Parameters:**
- `symbol` (required): Trading pair symbol

**Example:**
```
b!price BTC
b!price ETHUSDT
```

**Output:** Current price with 24h change and volume.

---

### `b!balance`

Displays current account balance and portfolio information.

**Example:**
```
b!balance
```

**Output:** Account balance, available funds, and open positions.

---

### `b!test_connection`

Tests connectivity to exchange APIs and Discord.

**Example:**
```
b!test_connection
```

**Output:** Connection status for all services.

## 📊 Charting Commands

### `b!chart <symbol> [interval] [limit]`

Generates price charts with technical indicators.

**Parameters:**
- `symbol` (required): Trading pair symbol
- `interval` (optional): Timeframe (default: 4h)
- `limit` (optional): Number of candles (default: 100)

**Example:**
```
b!chart ETH 1h 50
```

**Output:** Chart image with price action and basic indicators.

---

### `b!indicator_chart <indicator> <symbol> [interval]`

Creates charts with specific indicator visualization.

**Parameters:**
- `indicator` (required): Indicator type (rsi, macd, bollinger, etc.)
- `symbol` (required): Trading pair symbol
- `interval` (optional): Timeframe (default: 4h)

**Example:**
```
b!indicator_chart macd BTC 4h
```

**Output:** Chart with the specified indicator highlighted.

---

### `b!strategy_chart <strategy> <symbol> [interval]`

Displays charts with strategy entry/exit signals.

**Parameters:**
- `strategy` (required): Strategy name
- `symbol` (required): Trading pair symbol
- `interval` (optional): Timeframe (default: 4h)

**Example:**
```
b!strategy_chart bollinger_bands ETH 4h
```

**Output:** Chart showing strategy signals and performance.

## 🔍 Information Commands

### `b!help [command]`

Shows help information for commands.

**Parameters:**
- `command` (optional): Specific command to get help for

**Examples:**
```
b!help
b!help generate_signal
```

---

### `b!status`

Displays bot status and system information.

**Example:**
```
b!status
```

**Output:** Bot uptime, system resources, and active features.

---

### `b!version`

Shows bot version and update information.

**Example:**
```
b!version
```

## ⚠️ Error Handling

All commands include comprehensive error handling:

- **Invalid parameters**: Clear error messages with usage examples
- **API failures**: Automatic retry with user notification
- **Rate limiting**: Queue management and user notification
- **Exchange errors**: Detailed error explanations

## 🔐 Permission Requirements

Some commands require specific permissions:

- **Trading commands**: Require "Trader" role or admin permissions
- **Risk settings**: Require "Risk Manager" role or admin permissions
- **Bot configuration**: Require administrator permissions

## 📝 Command Aliases

Many commands have shorter aliases:

- `b!gs` → `b!generate_signal`
- `b!ms` → `b!market_signals`
- `b!ps` → `b!position_size`
- `b!opt` → `b!optimize_params`

## 🔄 Rate Limits

Commands are subject to rate limiting to prevent abuse:

- **Signal generation**: 5 requests per minute per user
- **Chart generation**: 10 requests per minute per user
- **Trading commands**: 3 requests per minute per user
- **Optimization**: 1 request per 5 minutes per user

---

For more detailed examples and advanced usage, see the [Basic Usage Guide](../guides/basic-usage.md) and [Advanced Features](../guides/advanced-features.md). 