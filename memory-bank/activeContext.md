# Active Context: Discord Trading Signal Bot

## Current Work Focus
The current focus is implementing a Discord trading signal bot that displays formatted trading signals similar to the example provided. The bot now connects to Binance API to generate real-time trading signals based on actual market data. It creates Discord embeds that show cryptocurrency trading signals with information such as:

- Symbol and strategy code (e.g., AAVE - SC02)
- Entry price (calculated from current price)
- Take profit (TP) price (calculated based on ATR volatility)
- Stop loss (SL) price (calculated based on ATR volatility)
- Imminent entry indicator (calculated from price proximity)
- Ratio percentage (calculated from entry/SL distance)
- Status (determined by trend analysis)
- Attribution ("By Reina~")

## Recent Changes
- Created the `bot.py` file with the core Discord bot functionality
- Added the `create_signal_embed` function to format signals as Discord embeds
- Implemented the `SCStrategySignal` class in strategies.py
- Added new commands in main.py for creating and sending signals
- Updated the TradingBot class to support signal storage
- **Added demo mode for running without Binance API credentials**
- **Implemented automatic TP/SL calculation based on ATR volatility**
- **Added automatic signal generation from current market data**
- **Created commands for generating real-time signals for specific coins**
- **Added market_signals command to generate signals for top coins**
- **Fixed duplicate signal bug by implementing duplicate checking**
- **Added command cooldowns to prevent accidental multiple executions**
- **Improved status message handling to reduce chat clutter**
- **Standardized author name to "Reina" for consistency**

## Next Steps
1. Implement multiple signal templates (beyond SC01)
2. Add support for signal history and retrieval (database storage)
3. Create scheduled signal broadcasting
4. Add support for signal attachments (like images/charts)
5. Implement signal reactions for user feedback
6. Add translation support for multilingual signals
7. Create a signal dashboard for tracking performance
8. Implement automatic signal generation based on multiple timeframes

## Active Decisions and Considerations

### Signal Format
- Using Discord embeds for rich formatting
- Green color for active signals
- Structured layout with clear sections for price levels
- Including both English and Vietnamese labels for international users

### Signal Generation Logic
- **Using Average True Range (ATR) for volatility-based TP/SL calculation**
- **Risk/reward ratio of 2.0 by default (customizable)**
- **Simple trend detection for determining signal status**
- **Price proximity check for imminent entry determination**

### Command Structure
- Using prefix commands (`//signal`, `//sc01`) for signal creation
- Parameters follow a logical order: symbol, strategy, prices, then optional parameters
- Default values for optional parameters to simplify basic usage
- **New commands focus on automatic signal generation**
- **Command cooldowns added to prevent duplicate signals from rapid clicks**

### Error Handling
- Comprehensive error handling for all commands
- User-friendly error messages
- Logging of errors for troubleshooting
- **Demo mode fallback when API credentials are not available**
- **Added specific handling for command cooldown errors**

### Performance Considerations
- Efficient storage of signals
- Minimizing API calls to Binance
- Optimizing chart generation for faster response
- **Caching price data to avoid redundant API calls**
- **Duplicate signal prevention to avoid data redundancy** 