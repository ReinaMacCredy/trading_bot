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
from bot import create_signal_embed  # Only import the create_signal_embed function, not the TradingSignalBot
from datetime import datetime
import random

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
channel_id = os.getenv('DISCORD_CHANNEL_ID')

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

bot = commands.Bot(command_prefix='b!', intents=intents)
trading_bot = None

# Add command cooldown management
from discord.ext.commands import cooldown, BucketType

# Add execution tracking to prevent duplicates
import threading
command_locks = {}
command_lock = threading.Lock()

# Global signal tracker to prevent duplicates across command invocations
# Format: {"symbol_strategy": {"timestamp": datetime, "count": int}}
signal_tracker = {}
signal_tracker_lock = threading.Lock()

def is_command_running(user_id, command_name):
    """Check if a command is already running for a user"""
    with command_lock:
        key = f"{user_id}_{command_name}"
        return key in command_locks

def set_command_running(user_id, command_name):
    """Mark a command as running for a user"""
    with command_lock:
        key = f"{user_id}_{command_name}"
        command_locks[key] = True

def clear_command_running(user_id, command_name):
    """Clear the running status for a command"""
    with command_lock:
        key = f"{user_id}_{command_name}"
        if key in command_locks:
            del command_locks[key]

def track_signal(symbol, strategy_code):
    """Record a signal to prevent duplicates"""
    with signal_tracker_lock:
        key = f"{symbol}_{strategy_code}"
        now = datetime.now()
        
        if key in signal_tracker:
            signal_tracker[key]["count"] += 1
            signal_tracker[key]["timestamp"] = now
        else:
            signal_tracker[key] = {"timestamp": now, "count": 1}
            
        return signal_tracker[key]["count"]

def is_duplicate_signal(symbol, strategy_code, window_seconds=180):
    """Check if a signal was recently generated (within the time window)"""
    with signal_tracker_lock:
        key = f"{symbol}_{strategy_code}"
        now = datetime.now()
        
        if key in signal_tracker:
            time_diff = (now - signal_tracker[key]["timestamp"]).total_seconds()
            count = signal_tracker[key]["count"]
            
            # If signal was generated in the last window_seconds and has been sent more than once
            if time_diff < window_seconds and count > 1:
                logger.warning(f"Duplicate signal detected for {symbol}-{strategy_code}: generated {time_diff:.1f}s ago, count: {count}")
                return True
        
        return False

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
    await ctx.send("**Available Trading Strategies:**\n• MA Crossover (ma_crossover)\n• RSI (rsi)\n• Bollinger Bands (bollinger_bands)\n• SC Signals (sc_signal)")

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
    """Add a trading strategy to monitor.
    
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
    
    success = trading_bot.add_strategy(strategy, symbol, interval)
    if success:
        await ctx.send(f"Added {strategy} strategy for {symbol} ({interval})")
    else:
        await ctx.send(f"Failed to add {strategy} strategy for {symbol}")

@bot.command(name='remove_strategy')
async def remove_strategy(ctx, strategy: str, symbol: str, interval: str = '1d'):
    """Remove a trading strategy.
    
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
    
    success = trading_bot.remove_strategy(strategy, symbol, interval)
    if success:
        await ctx.send(f"Removed {strategy} strategy for {symbol} ({interval})")
    else:
        await ctx.send(f"Strategy not found: {strategy} for {symbol} ({interval})")

@bot.command(name='list_active_strategies')
async def list_active_strategies(ctx):
    """List all active trading strategies"""
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    strategies = trading_bot.list_strategies()
    if not strategies:
        await ctx.send("No active strategies")
        return
    
    response = "**Active Trading Strategies:**\n"
    for i, strategy in enumerate(strategies, 1):
        response += f"{i}. {strategy['name']} - {strategy['symbol']} ({strategy['interval']})\n"
    
    await ctx.send(response)

@bot.command(name='test_connection')
async def test_binance_connection(ctx):
    """Test the connection to Binance API"""
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    if trading_bot.test_connection():
        await ctx.send("Connection to Binance API successful! ✅")
    else:
        await ctx.send("Failed to connect to Binance API. Check logs for details. ❌")

@bot.command(name='indicator')
async def analyze_indicator(ctx, indicator_name: str, symbol: str, interval: str = "1h", *args):
    """Analyze a symbol using a specific indicator
    
    Parameters:
    - indicator_name: Name of the indicator (rsi, macd, ema)
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - interval: Time interval (default: 1h)
    - args: Additional parameters for the indicator
    
    Examples:
    b!indicator rsi BTC 1h 14 30 70
    b!indicator macd ETH 4h 12 26 9
    b!indicator ema BTC 1d 20
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    # Process the symbol
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    # Parse parameters based on indicator
    params = {}
    if indicator_name.lower() == 'rsi':
        # Default RSI parameters: period, oversold, overbought
        if len(args) >= 1:
            params['period'] = int(args[0])
        if len(args) >= 3:
            params['oversold'] = int(args[1])
            params['overbought'] = int(args[2])
    elif indicator_name.lower() == 'macd':
        # Default MACD parameters: fast_period, slow_period, signal_period
        if len(args) >= 1:
            params['fast_period'] = int(args[0])
        if len(args) >= 2:
            params['slow_period'] = int(args[1])
        if len(args) >= 3:
            params['signal_period'] = int(args[2])
    elif indicator_name.lower() == 'ema':
        # Default EMA parameter: period
        if len(args) >= 1:
            params['period'] = int(args[0])
    
    # Get analysis result
    result = trading_bot.analyze_with_indicator(indicator_name, symbol, interval, **params)
    
    if result:
        # Create embed with the analysis result
        embed = discord.Embed(
            title=f"{symbol} {indicator_name.upper()} Analysis",
            description=f"Interval: {interval}",
            color=0x00FFFF
        )
        
        # Add signal
        signal_emoji = "🔴" if result["signal"] == "SELL" else "🟢" if result["signal"] == "BUY" else "⚪"
        embed.add_field(name="Signal", value=f"{signal_emoji} {result['signal']}", inline=False)
        
        # Add current price
        embed.add_field(name="Current Price", value=f"${result['current_price']:.4f}", inline=True)
        
        # Add indicator-specific fields
        if indicator_name.lower() == 'rsi':
            embed.add_field(name="RSI Value", value=f"{result['rsi']:.2f}", inline=True)
            embed.add_field(name="Oversold", value=f"{result['oversold']}", inline=True)
            embed.add_field(name="Overbought", value=f"{result['overbought']}", inline=True)
        elif indicator_name.lower() == 'macd':
            embed.add_field(name="MACD Line", value=f"{result['macd']:.6f}", inline=True)
            embed.add_field(name="Signal Line", value=f"{result['signal_line']:.6f}", inline=True)
            embed.add_field(name="Histogram", value=f"{result['histogram']:.6f}", inline=True)
        elif indicator_name.lower() == 'ema':
            embed.add_field(name="EMA Value", value=f"{result['ema']:.4f}", inline=True)
        
        # Set timestamp
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"Could not analyze {symbol} with {indicator_name}. Please check the parameters.")

@bot.command(name='indicator_chart')
async def generate_indicator_chart(ctx, indicator_name: str, symbol: str, interval: str = "1h", *args):
    """Generate a chart with indicator visualization
    
    Parameters:
    - indicator_name: Name of the indicator (rsi, macd, ema)
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - interval: Time interval (default: 1h)
    - args: Additional parameters for the indicator
    
    Examples:
    b!indicator_chart rsi BTC 1h 14 30 70
    b!indicator_chart macd ETH 4h 12 26 9
    b!indicator_chart ema BTC 1d 20
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    await ctx.send(f"Generating {indicator_name} chart for {symbol}...")
    
    # Process the symbol
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    # Parse parameters based on indicator (same as analyze_indicator)
    params = {}
    if indicator_name.lower() == 'rsi':
        if len(args) >= 1:
            params['period'] = int(args[0])
        if len(args) >= 3:
            params['oversold'] = int(args[1])
            params['overbought'] = int(args[2])
    elif indicator_name.lower() == 'macd':
        if len(args) >= 1:
            params['fast_period'] = int(args[0])
        if len(args) >= 2:
            params['slow_period'] = int(args[1])
        if len(args) >= 3:
            params['signal_period'] = int(args[2])
    elif indicator_name.lower() == 'ema':
        if len(args) >= 1:
            params['period'] = int(args[0])
    
    # Generate chart
    chart_buf = trading_bot.generate_indicator_chart(indicator_name, symbol, interval, **params)
    
    if chart_buf:
        # Create a Discord file from the buffer
        chart_file = File(fp=chart_buf, filename=f"{symbol}_{indicator_name}_chart.png")
        
        # Create embed with the chart
        embed = discord.Embed(
            title=f"{symbol} {indicator_name.upper()} Chart",
            description=f"Interval: {interval}",
            color=0x00FFFF
        )
        
        # Set the chart image
        embed.set_image(url=f"attachment://{symbol}_{indicator_name}_chart.png")
        
        # Set timestamp
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed, file=chart_file)
    else:
        await ctx.send(f"Could not generate chart for {symbol} with {indicator_name}. Please check the parameters.")

@bot.command(name='help_indicators')
async def help_indicators(ctx):
    """Show help for indicator commands"""
    embed = discord.Embed(
        title="Technical Indicator Commands",
        description="Commands for analyzing and visualizing technical indicators",
        color=0x00FFFF
    )
    
    embed.add_field(
        name="b!indicator <indicator_name> <symbol> [interval] [params]",
        value="Analyze a symbol using a specific indicator\n"
              "Example: `b!indicator rsi BTC 1h 14 30 70`",
        inline=False
    )
    
    embed.add_field(
        name="b!indicator_chart <indicator_name> <symbol> [interval] [params]",
        value="Generate a chart with indicator visualization\n"
              "Example: `b!indicator_chart macd ETH 4h 12 26 9`",
        inline=False
    )
    
    embed.add_field(
        name="Available Indicators",
        value="- `rsi`: Relative Strength Index [period] [oversold] [overbought]\n"
              "- `macd`: Moving Average Convergence Divergence [fast_period] [slow_period] [signal_period]\n"
              "- `ema`: Exponential Moving Average [period]",
        inline=False
    )
    
    embed.add_field(
        name="Default Parameters",
        value="- RSI: period=14, oversold=30, overbought=70\n"
              "- MACD: fast_period=12, slow_period=26, signal_period=9\n"
              "- EMA: period=20",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='signal')
async def send_signal(ctx, symbol: str, strategy_code: str, entry_price: float, tp_price: float, sl_price: float, ratio: str = "0.0%", status: str = "takeprofit", imminent: int = 1):
    """Send a trading signal like in the example.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., AAVE)
    - strategy_code: Strategy code (e.g., SC02, SC02+FRVP)
    - entry_price: Entry price
    - tp_price: Take profit price
    - sl_price: Stop loss price
    - ratio: Risk/reward ratio (default: 0.0%)
    - status: Signal status (default: takeprofit)
    - imminent: Imminent entry indicator (default: 1)
    """
    embed = create_signal_embed(f"{symbol}-{strategy_code}", "", entry_price, tp_price, sl_price, ratio, status, imminent, "Reina")
    await ctx.send(embed=embed)

@bot.command(name='sc01')
async def sc01_signal(ctx, symbol: str, strategy_code: str, entry_price: float, tp_price: float, sl_price: float, ratio: str = "0.0%", status: str = "takeprofit", imminent: int = 1):
    """Send an SC01 trading signal.
    
    Parameters as in //signal command
    """
    embed = discord.Embed(
        title=f"SC01 trading signals [Reina]",
        description="",
        color=0x7CFC00  # Green color
    )
    
    # Add a smaller embed for the signal
    signal_embed = create_signal_embed(f"{symbol}-{strategy_code}", "", entry_price, tp_price, sl_price, ratio, status, imminent, "Reina")
    
    # Convert the signal embed to a field in the main embed
    embed.add_field(name=f"{symbol} - {strategy_code}", value=signal_embed.description, inline=False)
    embed.set_footer(text="By Reina~")
    
    await ctx.send(embed=embed)

@bot.command(name='sc_add')
async def add_sc_signal(ctx, symbol: str, strategy_code: str, entry_price: float, tp_price: float, sl_price: float, ratio: str = "0.0%"):
    """Add an SC trading signal to the bot's database.
    
    Parameters similar to //signal command
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    try:
        # Create an SC strategy instance
        sc_strategy = trading_bot.get_strategy('sc_signal', version="SC01", author="Reina")
        
        # Generate the signal
        signal = sc_strategy.generate_signal(
            symbol=symbol,
            strategy_code=strategy_code,
            entry_price=entry_price,
            tp_price=tp_price,
            sl_price=sl_price,
            ratio=ratio,
            status="takeprofit",
            imminent=1
        )
        
        # Store the signal (you'd need to implement this in TradingBot)
        if hasattr(trading_bot, 'store_signal'):
            trading_bot.store_signal(signal)
            await ctx.send(f"Added SC signal for {symbol}-{strategy_code}")
        else:
            embed = create_signal_embed(f"{symbol}-{strategy_code}", "", entry_price, tp_price, sl_price, ratio, "takeprofit", 1, "Reina")
            await ctx.send("Signal created (but storage not implemented):", embed=embed)
    
    except Exception as e:
        await ctx.send(f"Error adding signal: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
        return
    
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"Invalid argument: {str(error)}")
        return

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Command on cooldown. Please wait {error.retry_after:.1f} seconds before trying again.")
        return
    
    # Log the error
    logger.error(f"Error in command {ctx.command}: {error}")
    traceback.print_exception(type(error), error, error.__traceback__)
    
    # Send error message to the user
    await ctx.send(f"An error occurred while executing the command: {str(error)}")

@bot.command(name='generate_signal')
@cooldown(1, 10, BucketType.user)  # Increase cooldown to 10 seconds
async def generate_signal(ctx, symbol: str, strategy_code: str = "SC02", risk_reward: float = 2.0):
    """Generate a trading signal using real Binance data
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., AAVE, BTC)
    - strategy_code: Strategy code (default: SC02)
    - risk_reward: Risk/reward ratio (default: 2.0)
    """
    logger.info(f"Generate signal command called by {ctx.author} for {symbol} with {strategy_code}")
    
    # Pre-check for duplicate signals
    symbol = symbol.upper()
    if is_duplicate_signal(symbol, strategy_code):
        await ctx.send(f"A signal for {symbol}-{strategy_code} was recently generated. Please wait before requesting another.")
        return
    
    # Check if this command is already running for this user
    if is_command_running(ctx.author.id, 'generate_signal'):
        logger.warning(f"Generate signal command already running for user {ctx.author}")
        await ctx.send("Signal generation is already in progress. Please wait for it to complete.")
        return
    
    # Track this signal generation attempt
    track_count = track_signal(symbol, strategy_code)
    if track_count > 1:
        logger.warning(f"Signal for {symbol}-{strategy_code} has been requested {track_count} times recently")
    
    # Mark command as running
    set_command_running(ctx.author.id, 'generate_signal')
    
    # Create a single status message we'll use for updates
    status_message = None
    signal_sent = False  # Track if signal has been sent
    
    try:
        if not trading_bot:
            await ctx.send("Trading bot is not initialized. Check logs for details.")
            return
        
        # Send only one status message
        status_message = await ctx.send(f"Generating trading signal for {symbol} with {strategy_code} strategy...")
        
        logger.info(f"Starting signal generation for {symbol}-{strategy_code}")
        
        # Generate signal from real market data with author explicitly set to "Reina"
        signal = trading_bot.generate_trading_signal(symbol, strategy_code, risk_reward, "Reina")
        
        if not signal:
            logger.warning(f"Failed to generate signal for {symbol}")
            await status_message.edit(content=f"Failed to generate signal for {symbol}. Check logs for details.")
            return
        
        logger.info(f"Signal generated for {symbol}: {signal['entry_price']}")
        
        # Check if a similar signal already exists to prevent duplicates
        existing_signals = trading_bot.get_signals(symbol)
        for existing in existing_signals:
            if (existing['strategy_code'] == signal['strategy_code'] and
                existing['entry_price'] == signal['entry_price']):
                logger.info(f"Duplicate signal detected in existing signals check for {symbol}")
                await status_message.edit(content=f"A signal for {symbol} with same parameters already exists.")
                return
        
        # Store the signal (returns False if it's a duplicate)
        store_result = trading_bot.store_signal(signal)
        logger.info(f"Store signal result for {symbol}: {store_result}")
        
        if not store_result:
            await status_message.edit(content=f"A signal for {symbol} with same parameters already exists. Use a different strategy or wait for market conditions to change.")
            return
        
        # Create the embed once with the author explicitly set to "Reina"
        embed = create_signal_embed(
            f"{signal['symbol']}-{signal['strategy_code']}", 
            "",
            signal['entry_price'], 
            signal['tp_price'], 
            signal['sl_price'], 
            signal['ratio'], 
            signal['status'], 
            signal['imminent'],
            "Reina"  # Explicitly set author to Reina
        )
        
        logger.info(f"About to send signal embed for {symbol}")
        
        # Delete the status message to avoid clutter
        try:
            await status_message.delete()
            status_message = None
        except:
            pass
        
        # Send the signal only once and mark as sent
        if not signal_sent:
            await ctx.send(embed=embed)
            signal_sent = True
            logger.info(f"Signal sent successfully for {symbol}")
        
    except Exception as e:
        logger.error(f"Error generating signal for {symbol}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            if status_message:
                await status_message.edit(content=f"Error generating signal: {e}")
        except:
            await ctx.send(f"Error generating signal: {e}")
    finally:
        # Always clear the running status
        clear_command_running(ctx.author.id, 'generate_signal')

@bot.command(name='market_signals')
@cooldown(1, 15, BucketType.user)  # Increased cooldown to 15 seconds per user
async def market_signals(ctx, count: int = 3):
    """Generate trading signals for top market cap coins
    
    Parameters:
    - count: Number of signals to generate (default: 3)
    """
    # Check if this command is already running for this user
    if is_command_running(ctx.author.id, 'market_signals'):
        logger.warning(f"Market signals command already running for user {ctx.author}")
        await ctx.send("Market signal generation is already in progress. Please wait for it to complete.")
        return
    
    # Mark command as running
    set_command_running(ctx.author.id, 'market_signals')
    
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        clear_command_running(ctx.author.id, 'market_signals')
        return
    
    # Top market cap coins
    top_coins = ["BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOT", "AVAX", "MATIC"]
    
    # Send a single status message that we'll update
    status_message = await ctx.send(f"Generating trading signals for top {count} coins...")
    
    # Strategy codes to use
    strategies = ["SC01", "SC02", "SC02+FRVP"]
    
    # Main embed
    main_embed = discord.Embed(
        title=f"SC01 trading signals [Reina]",
        description="",
        color=0x7CFC00  # Green color
    )
    
    signals_count = 0
    attempted_coins = set()
    processed_combinations = set()  # Track which symbol-strategy combinations we've tried
    
    # Try to generate unique signals up to a maximum number of attempts
    max_attempts = len(top_coins) * len(strategies)
    attempts = 0
    
    while signals_count < count and attempts < max_attempts:
        attempts += 1
        
        # Pick a coin that hasn't been attempted yet if possible
        available_coins = [coin for coin in top_coins if coin not in attempted_coins]
        if not available_coins:
            # If all coins have been attempted, reset and try again with different strategies
            attempted_coins = set()
            available_coins = top_coins
        
        symbol = random.choice(available_coins)
        attempted_coins.add(symbol)
        
        # Try each strategy for this symbol until we find one that works
        random.shuffle(strategies)  # Randomize strategy order
        strategy_found = False
        
        for strategy_code in strategies:
            # Skip if we've already tried this combination
            combo = f"{symbol}_{strategy_code}"
            if combo in processed_combinations:
                continue
            
            processed_combinations.add(combo)
            
            # Check for recent duplicate signals
            if is_duplicate_signal(symbol, strategy_code):
                logger.info(f"Skipping {symbol}-{strategy_code} as it was recently generated")
                continue
                
            try:
                # Track this signal generation attempt
                track_signal(symbol, strategy_code)
                
                # Generate signal - always use Reina as author for consistency
                signal = trading_bot.generate_trading_signal(symbol, strategy_code, 2.0, "Reina")
                
                if not signal:
                    continue
                    
                # Store the signal (will return False if duplicate)
                if not trading_bot.store_signal(signal):
                    continue
                
                # Create embedded content
                entry_text = f"Entry: {signal['entry_price']}"
                tp_text = f"TP (2R): {signal['tp_price']}"
                sl_text = f"SL: {signal['sl_price']}"
                
                signal_content = f"{entry_text} - {tp_text} - {sl_text}\n"
                signal_content += f"Imminent (Sắp vào Entry): {signal['imminent']}\n"
                signal_content += f"Ratio (Tỉ lệ): {signal['ratio']}%\n"
                signal_content += f"Status (Trạng thái): {signal['status']}"
                
                # Add to main embed
                main_embed.add_field(
                    name=f"🟢 {signal['symbol']} - {signal['strategy_code']}", 
                    value=signal_content, 
                    inline=False
                )
                
                signals_count += 1
                strategy_found = True
                break  # Move to next coin after finding a valid strategy
                
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        
        # If we couldn't find any valid strategy for this symbol, continue to the next
        if not strategy_found:
            continue
    
    # Delete status message before sending the results
    try:
        await status_message.delete()
    except:
        pass
    
    if signals_count > 0:
        main_embed.set_footer(text="By Reina~")
        await ctx.send(embed=main_embed)
    else:
        await ctx.send("Failed to generate any signals. Check logs for details.")
    
    # Clear command running status
    clear_command_running(ctx.author.id, 'market_signals')

@bot.command(name='live_signal')
@cooldown(1, 10, BucketType.user)  # Increased cooldown to 10 seconds per user
async def live_signal(ctx, channel_id: str = None):
    """Send a live trading signal to a specified channel
    
    Parameters:
    - channel_id: Optional channel ID to send signal to (default: current channel)
    """
    # Check if this command is already running for this user
    if is_command_running(ctx.author.id, 'live_signal'):
        logger.warning(f"Live signal command already running for user {ctx.author}")
        await ctx.send("Signal generation is already in progress. Please wait for it to complete.")
        return
    
    # Mark command as running
    set_command_running(ctx.author.id, 'live_signal')
    
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        clear_command_running(ctx.author.id, 'live_signal')
        return
    
    # Use provided channel or current channel
    target_channel_id = channel_id or ctx.channel.id
    
    # Top market cap coins
    top_coins = ["BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOT", "AVAX", "MATIC", "LINK", "ATOM", "UNI", "AAVE"]
    
    # Send a single status message that we'll update
    status_message = await ctx.send(f"Generating a live trading signal...")
    signal_sent = False  # Track if signal has been sent
    
    # Choose a random coin
    symbol = random.choice(top_coins)
    
    # Strategy codes to use
    strategies = ["SC01", "SC02", "SC02+FRVP"]
    strategy_code = random.choice(strategies)
    
    # Check for duplicate signals first
    if is_duplicate_signal(symbol, strategy_code):
        # If duplicate detected, try a different coin and strategy
        remaining_coins = [coin for coin in top_coins if coin != symbol]
        symbol = random.choice(remaining_coins) if remaining_coins else symbol
        strategy_code = random.choice([s for s in strategies if s != strategy_code])
        
        # Still check again with new selection
        if is_duplicate_signal(symbol, strategy_code):
            await status_message.edit(content=f"A signal for {symbol}-{strategy_code} was recently generated. Please try again later.")
            clear_command_running(ctx.author.id, 'live_signal')
            return
    
    # Track this signal generation attempt
    track_count = track_signal(symbol, strategy_code)
    if track_count > 1:
        logger.warning(f"Signal for {symbol}-{strategy_code} has been requested {track_count} times recently")
    
    try:
        # Generate signal - always use Reina as author for consistency
        signal = trading_bot.generate_trading_signal(symbol, strategy_code, 2.0, "Reina")
        
        if not signal:
            await status_message.edit(content=f"Failed to generate signal. Check logs for details.")
            clear_command_running(ctx.author.id, 'live_signal')
            return
            
        # Store the signal (will return False if duplicate)
        if not trading_bot.store_signal(signal):
            await status_message.edit(content=f"Signal for {symbol} already exists. Generating a new one...")
            # Try a different coin
            remaining_coins = [coin for coin in top_coins if coin != symbol]
            if remaining_coins:
                symbol = random.choice(remaining_coins)
                signal = trading_bot.generate_trading_signal(symbol, strategy_code, 2.0, "Reina")
                if not signal or not trading_bot.store_signal(signal):
                    await status_message.edit(content=f"Failed to generate a unique signal. Try again later.")
                    clear_command_running(ctx.author.id, 'live_signal')
                    return
            else:
                await status_message.edit(content=f"Failed to generate a unique signal. Try again later.")
                clear_command_running(ctx.author.id, 'live_signal')
                return
        
        # Get target channel
        target_channel = bot.get_channel(int(target_channel_id))
        if not target_channel:
            await status_message.edit(content=f"Channel with ID {target_channel_id} not found.")
            clear_command_running(ctx.author.id, 'live_signal')
            return
        
        # Create and send the embed only once
        if not signal_sent:
            embed = create_signal_embed(
                f"{signal['symbol']}-{signal['strategy_code']}", 
                "",
                signal['entry_price'], 
                signal['tp_price'], 
                signal['sl_price'], 
                signal['ratio'], 
                signal['status'], 
                signal['imminent'],
                "Reina"  # Explicitly set author to Reina
            )
            
            # Delete status message if sending to the same channel
            if int(target_channel_id) == ctx.channel.id:
                await status_message.delete()
                status_message = None
            else:
                await status_message.edit(content=f"Signal sent to channel {target_channel.name}.")
            
            await target_channel.send(embed=embed)
            signal_sent = True
            logger.info(f"Live signal sent successfully for {symbol}")
        
    except Exception as e:
        logger.error(f"Error generating live signal: {e}")
        if status_message:
            await status_message.edit(content=f"Error generating live signal: {e}")
    finally:
        # Always clear the command running status
        clear_command_running(ctx.author.id, 'live_signal')

def run_bot():
    """Run the Discord bot"""
    bot.run(token)

if __name__ == "__main__":
    run_bot()    