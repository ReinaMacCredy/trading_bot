from cgitb import handler
import discord
from discord.ext import commands
import logging
from typing import List, Optional
from dotenv import load_dotenv
import os
import traceback
from discord import File
from trading import TradingBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("discord.log", encoding='utf-8', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bot')

# Load environment variables
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# If token is not found in environment variables, prompt for it
if token is None:
    print("Discord token not found in environment variables.")
    token = input("Please enter your Discord bot token: ")
    if not token:
        raise ValueError("Discord token is required to run the bot.")

# Setup bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='//', intents=intents)
trading_bot = None

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    global trading_bot
    try:
        trading_bot = TradingBot()
        logger.info("Trading bot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize trading bot: {e}")
        traceback.print_exc()

@bot.command(name='price')
async def get_price(ctx, symbol: str):
    """Get the current price of a cryptocurrency.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    price = trading_bot.get_price(symbol)
    if price:
        await ctx.send(f"Current price of {symbol}: ${price}")
    else:
        await ctx.send(f"Failed to get price for {symbol}. Make sure the symbol is valid.")

@bot.command(name='balance')
async def get_balance(ctx):
    """Get your account balance"""
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    balances = trading_bot.get_account_balance()
    if not balances:
        await ctx.send("Failed to get account balance or no balance available.")
        return
    
    response = "**Your Account Balance:**\n"
    for balance in balances:
        asset = balance['asset']
        free = float(balance['free'])
        locked = float(balance['locked'])
        if free > 0 or locked > 0:
            response += f"• {asset}: Free: {free}, Locked: {locked}\n"
    
    await ctx.send(response)

@bot.command(name='chart')
async def get_chart(ctx, symbol: str, interval: str = '1d', limit: int = 30):
    """Generate a price chart for a cryptocurrency.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - interval: Time interval (default: 1d)
    - limit: Number of data points (default: 30)
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    if interval not in valid_intervals:
        await ctx.send(f"Invalid interval. Please use one of: {', '.join(valid_intervals)}")
        return
    
    await ctx.send(f"Generating chart for {symbol} ({interval})...")
    chart_data = trading_bot.generate_chart(symbol, interval, limit)
    
    if chart_data:
        await ctx.send(file=File(chart_data, filename=f"{symbol}_{interval}_chart.png"))
    else:
        await ctx.send(f"Failed to generate chart for {symbol}.")

@bot.command(name='buy')
async def buy(ctx, symbol: str, quantity: float):
    """Buy a cryptocurrency at market price.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - quantity: Amount to buy
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    await ctx.send(f"Placing market buy order for {quantity} {symbol}...")
    order = trading_bot.place_order(symbol, 'BUY', quantity)
    
    if order:
        await ctx.send(f"Order placed successfully! Order ID: {order['orderId']}")
    else:
        await ctx.send("Failed to place order. Check logs for details.")

@bot.command(name='sell')
async def sell(ctx, symbol: str, quantity: float):
    """Sell a cryptocurrency at market price.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - quantity: Amount to sell
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    await ctx.send(f"Placing market sell order for {quantity} {symbol}...")
    order = trading_bot.place_order(symbol, 'SELL', quantity)
    
    if order:
        await ctx.send(f"Order placed successfully! Order ID: {order['orderId']}")
    else:
        await ctx.send("Failed to place order. Check logs for details.")

@bot.command(name='strategies')
async def list_strategies(ctx):
    """List available trading strategies"""
    await ctx.send("**Available Trading Strategies:**\n• MA Crossover (ma_crossover)\n• RSI (rsi)\n• Bollinger Bands (bollinger_bands)")

@bot.command(name='analyze')
async def analyze(ctx, strategy: str, symbol: str, interval: str = '1d'):
    """Analyze a symbol using a specific strategy.
    
    Parameters:
    - strategy: Strategy name (e.g., ma_crossover, rsi, bollinger_bands)
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - interval: Time interval (default: 1d)
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    if interval not in valid_intervals:
        await ctx.send(f"Invalid interval. Please use one of: {', '.join(valid_intervals)}")
        return
    
    await ctx.send(f"Analyzing {symbol} with {strategy} strategy ({interval})...")
    result = trading_bot.analyze_symbol(strategy, symbol, interval)
    
    if not result:
        await ctx.send(f"Failed to analyze {symbol} with {strategy} strategy.")
        return
    
    response = f"**Analysis Result for {symbol}**\n"
    response += f"• Strategy: {result['strategy']}\n"
    response += f"• Current Price: {result['current_price']}\n"
    response += f"• Signal: {result['signal']}\n"
    
    # Add strategy-specific indicators
    if strategy.lower() == 'ma_crossover':
        response += f"• Short MA: {result['short_ma']:.2f}\n"
        response += f"• Long MA: {result['long_ma']:.2f}\n"
    elif strategy.lower() == 'rsi':
        response += f"• RSI: {result['rsi']:.2f}\n"
    elif strategy.lower() == 'bollinger_bands':
        response += f"• SMA: {result['sma']:.2f}\n"
        response += f"• Upper Band: {result['upper_band']:.2f}\n"
        response += f"• Lower Band: {result['lower_band']:.2f}\n"
    
    await ctx.send(response)

@bot.command(name='strategy_chart')
async def strategy_chart(ctx, strategy: str, symbol: str, interval: str = '1d', limit: int = 30):
    """Generate a chart with strategy indicators.
    
    Parameters:
    - strategy: Strategy name (e.g., ma_crossover, rsi, bollinger_bands)
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - interval: Time interval (default: 1d)
    - limit: Number of data points (default: 30)
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    if interval not in valid_intervals:
        await ctx.send(f"Invalid interval. Please use one of: {', '.join(valid_intervals)}")
        return
    
    await ctx.send(f"Generating strategy chart for {symbol} with {strategy} strategy ({interval})...")
    chart_data = trading_bot.generate_strategy_chart(strategy, symbol, interval, limit)
    
    if chart_data:
        await ctx.send(file=File(chart_data, filename=f"{symbol}_{strategy}_{interval}_chart.png"))
    else:
        await ctx.send(f"Failed to generate strategy chart for {symbol}.")

@bot.command(name='add_strategy')
async def add_strategy(ctx, strategy: str, symbol: str, interval: str = '1d'):
    """Add a strategy to monitor.
    
    Parameters:
    - strategy: Strategy name (e.g., ma_crossover, rsi, bollinger_bands)
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - interval: Time interval (default: 1d)
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    if interval not in valid_intervals:
        await ctx.send(f"Invalid interval. Please use one of: {', '.join(valid_intervals)}")
        return
    
    result = trading_bot.add_strategy(strategy, symbol, interval)
    
    if result:
        await ctx.send(f"Added {strategy} strategy for {symbol} ({interval}).")
    else:
        await ctx.send(f"Failed to add strategy. Check logs for details.")

@bot.command(name='remove_strategy')
async def remove_strategy(ctx, strategy: str, symbol: str, interval: str = '1d'):
    """Remove a strategy from monitoring.
    
    Parameters:
    - strategy: Strategy name (e.g., ma_crossover, rsi, bollinger_bands)
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - interval: Time interval (default: 1d)
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    result = trading_bot.remove_strategy(strategy, symbol, interval)
    
    if result:
        await ctx.send(f"Removed {strategy} strategy for {symbol} ({interval}).")
    else:
        await ctx.send(f"Strategy not found.")

@bot.command(name='list_strategies')
async def list_active_strategies(ctx):
    """List all active monitoring strategies"""
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    strategies = trading_bot.list_strategies()
    
    if not strategies:
        await ctx.send("No active strategies.")
        return
    
    response = "**Active Strategies:**\n"
    for i, strategy in enumerate(strategies, 1):
        response += f"{i}. {strategy['name']} - {strategy['symbol']} ({strategy['interval']})\n"
    
    await ctx.send(response)

@bot.command(name='test_connection')
async def test_binance_connection(ctx):
    """Test Binance API connection and credentials"""
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    await ctx.send("Testing Binance API connection...")
    
    success = trading_bot.test_connection()
    
    if success:
        await ctx.send("✅ Binance API connection successful! The API credentials are working properly.")
    else:
        await ctx.send("❌ Binance API connection failed. Check the logs for detailed error information.")
        # Check if we can at least get public data
        try:
            symbol = "BTCUSDT"
            price = trading_bot.get_price(symbol)
            if price:
                await ctx.send(f"However, public API endpoints are working. Got {symbol} price: ${price}")
                await ctx.send("This suggests your API key might be valid but doesn't have the required permissions for account access.")
            else:
                await ctx.send("Failed to access public API endpoints as well. There might be network issues or the API key is invalid.")
        except Exception as e:
            await ctx.send(f"Error testing public endpoints: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Type `//help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        if error.param.name == 'symbol':
            await ctx.send(f"Missing required argument: `symbol`. Please provide a cryptocurrency symbol (e.g., BTC, ETH).")
        else:
            await ctx.send(f"Missing required argument: `{error.param.name}`. Type `//help {ctx.command}` for more information.")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send(f"An error occurred: {error}")
        traceback.print_exc()

# Run the bot
bot.run(token)    