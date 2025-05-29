# Discord Trading Bot

A Discord bot that lets you monitor cryptocurrency prices, view charts, and execute trades directly from Discord.

## Features

- Get real-time cryptocurrency prices
- View account balances
- Generate price charts
- Execute buy and sell orders
- Apply trading strategies for analysis
- Easy to use Discord commands

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory with the following variables:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   BINANCE_API_KEY=your_binance_api_key
   BINANCE_API_SECRET=your_binance_api_secret
   ```
   
   **Note**: If you don't create a `.env` file, the bot will prompt you to enter your Discord token when you run it.

### Discord Bot Setup

1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot for your application
3. Enable the required intents (Members and Message Content)
4. Get your bot token and add it to the `.env` file
5. Invite your bot to your server using the OAuth2 URL generator (with `bot` scope and necessary permissions)

### Binance API Setup

1. Create a Binance account if you don't have one
2. Go to API Management at https://www.binance.com/en/my/settings/api-management and create a new API key
3. Enable trading permissions for the API key (recommended to restrict by IP)
4. Add the API key and secret to your `.env` file

## Running the Bot

```
python main.py
```

## Available Commands

### Basic Commands
- `//price <symbol>` - Get the current price of a cryptocurrency (e.g., `//price BTC`)
- `//balance` - View your account balance
- `//chart <symbol> [interval] [limit]` - Generate a price chart (e.g., `//chart ETH 4h 50`)
  - Available intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
  - Default interval: 1d
  - Default limit: 30
- `//buy <symbol> <quantity>` - Place a market buy order (e.g., `//buy BTC 0.001`)
- `//sell <symbol> <quantity>` - Place a market sell order (e.g., `//sell BTC 0.001`)

### Strategy Commands
- `//strategies` - List all available trading strategies
- `//analyze <strategy> <symbol> [interval]` - Analyze a symbol using a specific strategy (e.g., `//analyze rsi BTC 4h`)
- `//strategy_chart <strategy> <symbol> [interval] [limit]` - Generate a chart with strategy indicators (e.g., `//strategy_chart bollinger_bands ETH 1d 50`)
- `//add_strategy <strategy> <symbol> [interval]` - Add a strategy to monitor (e.g., `//add_strategy ma_crossover BTC 1h`)
- `//remove_strategy <strategy> <symbol> [interval]` - Remove a strategy from monitoring (e.g., `//remove_strategy ma_crossover BTC 1h`)
- `//list_strategies` - List all active monitoring strategies

### Help
- `//help` - View all available commands

## Available Trading Strategies

### Moving Average Crossover (ma_crossover)
A strategy that generates buy signals when a shorter-term moving average crosses above a longer-term moving average, and sell signals when the shorter-term moving average crosses below the longer-term moving average.

### Relative Strength Index (rsi)
A momentum oscillator that measures the speed and change of price movements. Traditional interpretation and usage of the RSI is that values of 70 or above indicate that a security is becoming overbought or overvalued, and values of 30 or below indicate an oversold or undervalued condition.

### Bollinger Bands (bollinger_bands)
A tool defined by a set of lines plotted two standard deviations (positively and negatively) away from a simple moving average of the security's price. It can be used to generate buy signals when the price touches the lower band and sell signals when the price touches the upper band.

## Security Considerations

- Never share your API keys or Discord bot token
- Consider using API keys with restricted permissions (read-only if you only need price data)
- Use IP restrictions for your API keys when possible
- Test with small amounts before executing large trades

## Disclaimer

This bot is for educational purposes only. Use at your own risk. The creators are not responsible for any financial losses incurred through the use of this bot. 