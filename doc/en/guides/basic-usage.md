# Basic Usage Guide

This guide will help you get started with the Professional Discord Trading Bot. After following the installation guide, you'll learn how to use the essential features and commands.

## 🚀 Getting Started

### First Steps

1. **Verify Bot is Online**: Check that the bot appears online in your Discord server
2. **Test Basic Connectivity**: Run `b!test_connection` to ensure everything is working
3. **Check Your Balance**: Use `b!balance` to verify exchange connection (if configured)

### Understanding the Command System

All commands start with the prefix `b!` followed by the command name and parameters.

```
Format: b!command_name parameter1 parameter2
Example: b!generate_signal BTC
```

## 📊 Your First Trading Signal

Let's generate your first trading signal:

### Basic Signal Generation

```discord
b!generate_signal BTC
```

This will:
- Analyze Bitcoin's current market data
- Apply technical indicators (MACD, RSI, EMA)
- Generate a professional signal with entry, stop-loss, and take-profit levels
- Provide a confidence score

### Signal Output Explanation

A typical signal looks like this:

```
🎯 TRADING SIGNAL - BTC/USDT

📈 DIRECTION: LONG
🎯 ENTRY: $60,500 - $60,800
🛑 STOP LOSS: $58,200 (-3.8%)
💰 TAKE PROFIT: $63,400 (+4.5%)
📊 CONFIDENCE: 78%

📋 ANALYSIS:
• RSI (14): 32 - Oversold
• MACD: Bullish crossover
• EMA Trend: Upward
• Volume: Above average

⚠️ Risk: 2% of portfolio
💡 Recommended position: 0.025 BTC
```

### Understanding Signal Components

- **Direction**: LONG (buy) or SHORT (sell)
- **Entry**: Price range to enter the trade
- **Stop Loss**: Maximum loss level (risk management)
- **Take Profit**: Target profit level
- **Confidence**: Algorithm confidence (0-100%)
- **Analysis**: Technical indicator readings
- **Risk**: Suggested risk percentage
- **Position**: Recommended position size

## 🔍 Market Analysis Commands

### Multiple Market Signals

Get signals for top cryptocurrencies:

```discord
b!market_signals 5
```

This generates signals for the top 5 cryptocurrencies by market cap.

### Specific Indicator Analysis

Analyze individual indicators:

```discord
b!indicator rsi BTC 1h
b!indicator macd ETH 4h
```

### Dual Timeframe Analysis

For more accurate signals, use dual timeframe analysis:

```discord
b!dual_macd_rsi BTC 1h 4h
```

This analyzes Bitcoin on both 1-hour and 4-hour timeframes for signal confirmation.

## ⚖️ Risk Management

### Setting Your Risk Parameters

Configure your risk tolerance:

```discord
b!risk_settings 2 5 1.5
```

This sets:
- 2% risk per trade
- 5% maximum daily loss
- 1.5% trailing stop

### Position Size Calculation

Calculate optimal position size for a trade:

```discord
b!position_size BTC 60000 58500
```

Parameters:
- Symbol: BTC
- Entry price: $60,000
- Stop loss: $58,500

The bot will calculate the exact amount to trade based on your risk settings.

## 📈 Chart Analysis

### Basic Charts

Generate price charts with indicators:

```discord
b!chart BTC 4h 100
```

This creates a 4-hour Bitcoin chart with the last 100 candles.

### Indicator-Specific Charts

View charts focused on specific indicators:

```discord
b!indicator_chart rsi BTC 4h
b!indicator_chart macd ETH 1h
```

### Strategy Charts

See how strategies perform visually:

```discord
b!strategy_chart bollinger_bands BTC 4h
```

## 💰 Basic Trading (Live Trading)

⚠️ **Important**: Only use live trading commands if you have:
- Configured your exchange API keys
- Tested thoroughly with paper trading
- Set appropriate risk management

### Check Current Price

```discord
b!price BTC
b!price ETHUSDT
```

### View Account Balance

```discord
b!balance
```

### Advanced Buy Order

Place a buy order with automatic stop-loss and take-profit:

```discord
b!advanced_buy BTC 0.01 61500 58500
```

Parameters:
- Symbol: BTC
- Quantity: 0.01 BTC
- Take profit: $61,500
- Stop loss: $58,500

## 🔧 Optimization Features

### Basic Parameter Optimization

Optimize strategy parameters for better performance:

```discord
b!optimize_params BTC 1h
```

This runs grid search optimization on the default strategy.

### Market Regime Detection

Understand current market conditions:

```discord
b!market_regime BTC 4h
```

This helps adapt your trading approach to current market conditions.

## 📝 Best Practices for Beginners

### 1. Start with Paper Trading

- Enable paper trading mode in your configuration
- Practice with virtual money before risking real funds
- Learn how signals perform in different market conditions

### 2. Use Conservative Risk Settings

```discord
b!risk_settings 1 3 1.0
```

Start with:
- 1% risk per trade (conservative)
- 3% maximum daily loss
- 1% trailing stop

### 3. Focus on Higher Timeframes

- Start with 4h and daily timeframes
- Avoid scalping (1m, 5m) until experienced
- Higher timeframes are generally more reliable

### 4. Diversify Your Analysis

- Don't rely on a single signal
- Use dual timeframe analysis
- Check multiple indicators
- Consider market regime

### 5. Monitor Performance

- Keep track of your trades
- Use the bot's performance tracking
- Adjust strategies based on results

## 🔍 Understanding Market Conditions

### Trending Markets

In trending markets (detected by `b!market_regime`):
- Follow the trend direction
- Use momentum indicators (MACD)
- Set wider stop losses

### Ranging Markets

In sideways markets:
- Use mean reversion strategies
- Look for oversold/overbought conditions
- Use tighter profit targets

### Volatile Markets

In high volatility:
- Reduce position sizes
- Use wider stops
- Consider shorter timeframes

## 🚨 Common Beginner Mistakes

### 1. Ignoring Risk Management
- **Problem**: Trading without stop losses
- **Solution**: Always set stop losses and position sizes

### 2. Overtrading
- **Problem**: Taking every signal
- **Solution**: Be selective, focus on high-confidence signals

### 3. FOMO (Fear of Missing Out)
- **Problem**: Chasing pumps and entering late
- **Solution**: Wait for proper entry points

### 4. Emotional Trading
- **Problem**: Letting emotions drive decisions
- **Solution**: Stick to the bot's signals and risk rules

### 5. Insufficient Testing
- **Problem**: Going live without proper testing
- **Solution**: Extensive paper trading and backtesting

## 📞 Getting Help

### Built-in Help System

```discord
b!help
b!help generate_signal
```

### Status and Information

```discord
b!status      # Bot status and performance
b!version     # Current bot version
```

### Common Issues

If commands aren't working:

1. **Check bot permissions**: Ensure bot can send messages and embeds
2. **Verify API connections**: Use `b!test_connection`
3. **Check command syntax**: Use `b!help command_name`
4. **Review logs**: Check console output for errors

## 🔄 Next Steps

Once you're comfortable with basic usage:

1. **[Trading Signals Guide](trading-signals.md)** - Advanced signal analysis
2. **[Risk Management](risk-management.md)** - Professional risk techniques
3. **[Strategy Optimization](strategy-optimization.md)** - Enhance performance
4. **[Advanced Features](advanced-features.md)** - Expert-level functionality

## 💡 Pro Tips

### Quick Commands
- Use aliases: `b!gs BTC` instead of `b!generate_signal BTC`
- Chain analysis: Run multiple indicators for confirmation
- Save settings: Configure once, reuse everywhere

### Efficiency Tips
- Set up dedicated trading channels
- Use channel-specific risk settings
- Monitor multiple timeframes simultaneously

### Performance Tips
- Review signals in different market conditions
- Track which strategies work best for you
- Adjust parameters based on performance data

---

**Remember**: Trading is risky. Always start small, use proper risk management, and never trade more than you can afford to lose. The bot is a tool to assist your trading, not a guarantee of profits.

*Ready for more advanced features? Check out our [Advanced Features Guide](advanced-features.md)!* 