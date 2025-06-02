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
- **Fixed duplicate signal output bug by removing TradingSignalBot import in main.py**
- **Fixed issue with inconsistent author names in signals by adding author parameter to create_signal_embed**
- **Added signal_sent flag to prevent multiple signals from being sent for a single command**
- **Fixed duplicate signals bug by removing the TradingSignalBot class from bot.py**
- **Enhanced duplicate signal detection in generate_signal command**
- **Standardized author attribution to always use "Reina" in all signal commands**
- **LATEST FIX: Implemented comprehensive duplicate signal prevention system with:**
  - Command execution locking to prevent multiple simultaneous executions of the same command by the same user
  - Enhanced timestamp-based duplicate detection in signal storage (within 30 seconds)
  - Improved logging for debugging signal generation flow
  - Removed redundant signal_sent flag logic that was causing confusion
  - Added proper error handling to prevent status message update failures
- **NEW FIX: Resolved duplicate signals issue by:**
  - Adding explicit signal sent tracking in the generate_signal command
  - Enhancing the store_signal method with better duplicate detection (60-second window)
  - Adding more comprehensive error handling for command execution
  - Improving timestamp validation in signal storage
  - Adding more detailed logging for signal generation and storage
- **MAJOR ENHANCEMENT (Based on Discord Trade Bot Guide):**
  - Added CCXT integration for multi-exchange support beyond just Binance
  - Implemented professional risk management with position sizing and max daily loss limits
  - Added pandas-ta for more reliable technical indicators (replacing manual calculations)
  - Created dual timeframe MACD+RSI strategy for better signal confirmation
  - Added advanced order placement with take-profit and stop-loss
  - Enhanced chart generation with technical indicators (RSI, EMA)
  - Added new commands for position sizing, risk settings, and advanced buying
  - Implemented comprehensive error handling for all exchange operations

## Next Steps
1. Implement multiple signal templates (beyond SC01)
2. Add support for signal history and retrieval (database storage)
3. Create scheduled signal broadcasting
4. Add support for signal attachments (like images/charts)
5. Add signal reactions for user feedback
6. Add translation support for multilingual signals
7. Create a signal dashboard for tracking performance
8. Implement automatic signal generation based on multiple timeframes
9. Add user authentication for secure trading operations
10. Implement trailing stop functionality
11. Create circuit breakers for market volatility protection
12. Add paper trading mode for strategy testing
13. Implement comprehensive logging and performance tracking

## Active Decisions and Considerations

### Signal Format
- Using Discord embeds for rich formatting
- Green color for active signals
- Structured layout with clear sections for price levels
- Including both English and Vietnamese labels for international users
- **Consistent "By Reina~" footer on all signals**

### Signal Generation Logic
- **Using Average True Range (ATR) for volatility-based TP/SL calculation**
- **Risk/reward ratio of 2.0 by default (customizable)**
- **Simple trend detection for determining signal status**
- **Price proximity check for imminent entry determination**
- **Dual timeframe confirmation (using higher timeframe trend to filter signals)**
- **Combined MACD + RSI for more reliable signals with less false positives**
- **Position sizing based on account risk percentage (Kelly Criterion inspired)**

### Command Structure
- Using prefix commands (`b!signal`, `b!sc01`) for signal creation
- Parameters follow a logical order: symbol, strategy, prices, then optional parameters
- Default values for optional parameters to simplify basic usage
- **New commands focus on automatic signal generation**
- **Command cooldowns added to prevent duplicate signals from rapid clicks**
- **Command execution locking to prevent multiple simultaneous executions**
- **New advanced commands like `b!risk_settings` for professional risk management**
- **New `b!position_size` command to calculate optimal position sizes**

### Exchange Integration
- **Multi-exchange support via CCXT library (beyond just Binance)**
- **Standardized exchange interface for consistent API access**
- **Enhanced error handling for exchange errors and rate limiting**
- **Support for different order types (market, limit, stop-loss)**
- **Advanced order placement with take-profit and stop-loss in one command**

### Risk Management
- **Position sizing based on fixed percentage risk (default 2%)**
- **Daily loss limits to protect account balance**
- **Trailing stop support for maximizing profits in trends**
- **Maximum drawdown protection to prevent catastrophic losses**
- **User-configurable risk parameters through Discord commands**

### Error Handling
- Comprehensive error handling for all commands
- User-friendly error messages
- Logging of errors for troubleshooting
- **Demo mode fallback when API credentials are not available**
- **Added specific handling for command cooldown errors**
- **Enhanced error handling for Discord API rate limits**

### Performance Considerations
- Efficient storage of signals
- Minimizing API calls to Binance
- Optimizing chart generation for faster response
- **Caching price data to avoid redundant API calls**
- **Duplicate signal prevention to avoid data redundancy** 
- **Fixed bot architecture to prevent duplicate signals from being sent** 
- **Added safeguards to ensure each command only sends one signal** 
- **Implemented threading locks to prevent race conditions in signal generation**
- **Enhanced duplicate detection with timestamp checking for signals generated within 60 seconds**
- **Rate limiting on API calls to prevent exchange bans**

### Technical Analysis Improvements
- **Using pandas-ta library for professional-grade indicators**
- **Multi-timeframe analysis for better signal confirmation**
- **Combined strategies (MACD+RSI) for higher signal reliability**
- **Enhanced charting with multiple indicators displayed**
- **Proper backtesting capability with accurate historical data** 