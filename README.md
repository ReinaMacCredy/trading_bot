# Discord Trading Signal Bot

A Discord bot for cryptocurrency trading signals and analysis. The bot can generate trading signals in a format similar to professional trading channels.

## Features

- Generate and display trading signals with entry, take profit, and stop loss prices
- Format signals with customizable parameters including ratio and status
- Analyze cryptocurrencies using various strategies (MA Crossover, RSI, Bollinger Bands)
- Generate price charts and strategy-specific visualizations
- Monitor prices and execute trades (when connected to an exchange)
- **NEW: Generate real signals based on actual Binance market data**
- **NEW: Auto-calculate entry, TP, and SL prices based on volatility**

## Setup

1. Clone this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   DISCORD_CHANNEL_ID=your_channel_id
   BINANCE_API_KEY=your_binance_api_key
   BINANCE_API_SECRET=your_binance_api_secret
   ```
   - Note: If you don't provide Binance API credentials, the bot will run in demo mode with simulated market data.

## Running the Bot

```
python main.py
```

## Available Commands

### Real-time Trading Signal Commands

- `//generate_signal <symbol> [strategy_code] [risk_reward]`
  - Generates a trading signal with real Binance data
  - Example: `//generate_signal BTC SC02 2.5`

- `//market_signals [count]`
  - Generates trading signals for top market cap coins
  - Example: `//market_signals 5`

- `//live_signal [channel_id]`
  - Sends a live trading signal to a specified channel
  - Example: `//live_signal 123456789012345678`

### Manual Trading Signal Commands

- `//signal <symbol> <strategy_code> <entry_price> <tp_price> <sl_price> [ratio] [status] [imminent]`
  - Sends a trading signal for a specific cryptocurrency
  - Example: `//signal AAVE SC02 180.6627 181.3468 180.3207 0.19% takeprofit 1`

- `//sc01 <symbol> <strategy_code> <entry_price> <tp_price> <sl_price> [ratio] [status] [imminent]`
  - Sends an SC01-style trading signal with formatting similar to the example
  - Example: `//sc01 AAVE SC02 180.6627 181.3468 180.3207 0.19% takeprofit 1`

### Analysis Commands

- `//price <symbol>`
  - Get current price of a cryptocurrency
  - Example: `//price BTC`

- `//chart <symbol> [interval] [limit]`
  - Generate a price chart
  - Example: `//chart ETH 4h 50`

- `//analyze <strategy> <symbol> [interval]`
  - Analyze a symbol using a specific strategy
  - Example: `//analyze rsi BTC 1h`

- `//strategy_chart <strategy> <symbol> [interval] [limit]`
  - Generate a chart with strategy indicators
  - Example: `//strategy_chart bollinger_bands ETH 4h`

- `//indicator <indicator_name> <symbol> [interval] [params]`
  - Analyze a symbol using a specific technical indicator (MACD, RSI, EMA)
  - Example: `//indicator rsi BTC 1h 14 30 70`
  - Available indicators: `rsi`, `macd`, `ema`

- `//indicator_chart <indicator_name> <symbol> [interval] [params]`
  - Generate a chart with technical indicator visualization
  - Example: `//indicator_chart macd ETH 4h 12 26 9`

- `//help_indicators`
  - Show help for indicator commands and parameters

### Strategy Management

- `//strategies`
  - List available trading strategies

- `//add_strategy <strategy> <symbol> [interval]`
  - Add a trading strategy to monitor
  - Example: `//add_strategy ma_crossover BTC 1h`

- `//remove_strategy <strategy> <symbol> [interval]`
  - Remove a trading strategy
  - Example: `//remove_strategy ma_crossover BTC 1h`

- `//list_active_strategies`
  - List all active trading strategies

### Account Management

- `//balance`
  - Get your account balance

- `//buy <symbol> <quantity>`
  - Buy a cryptocurrency at market price
  - Example: `//buy BTC 0.01`

- `//sell <symbol> <quantity>`
  - Sell a cryptocurrency at market price
  - Example: `//sell BTC 0.01`

### Utilities

- `//test_connection`
  - Test the connection to Binance API

## Example Output

The trading signals will appear similar to this format:

```
SC01 trading signals [Hina]
🟢 AAVE - SC02
Entry: 180.6627 - TP (2R): 181.3468 - SL: 180.3207
Imminent (Sắp vào Entry): 1
Ratio (Tỉ lệ): 0.19%
Status (Trạng thái): takeprofit
By Hina~
```

## Demo Mode

If you don't provide Binance API credentials in the `.env` file, the bot will run in demo mode. In this mode:
- The bot will use public Binance API endpoints for market data
- Account-specific commands will return simulated data
- Trading signals will still be generated with real market prices
- No actual trades will be executed

## License

This project is licensed under the MIT License - see the LICENSE file for details. 