import discord
from discord.ext import commands
import logging
from typing import List, Optional
from dotenv import load_dotenv
import os
import traceback
from discord import File
from legacy.trading import TradingBot
from legacy.bot import create_signal_embed  # Only import the create_signal_embed function, not the TradingSignalBot
from legacy.indicators import IndicatorFactory
from datetime import datetime
import random
import ccxt
import json
import asyncio
import aiohttp
from pathlib import Path

# Import optimization components
from src.trading.optimization_manager import OptimizationManager
from src.trading.parameter_optimizer import ParameterOptimizer
from src.trading.multi_indicator_strategy import MultiIndicatorStrategy
from src.trading.genetic_optimizer import GeneticOptimizer
from src.trading.ml_optimizer import MLOptimizer
from src.trading.risk_manager import DynamicRiskManager

# Import command functions
from src.bot.commands.history_commands import status_commands, active_commands, inactive_commands, order_history
from src.trading.order_history import OrderHistory

# Import RL commands
from src.bot.commands.rl_commands import RLCommands

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

# Load environment variables and configuration
load_dotenv()

# Import our new configuration loader
from src.config.config_loader import get_config, get_discord_config, is_sandbox

# Get configuration
config = get_config()
discord_config = get_discord_config()

# Get token from config
token = config.discord_token
channel_id = os.getenv('DISCORD_CHANNEL_ID')

# Health check and monitoring setup
health_check_file = Path("/tmp/bot_healthy")
startup_time = datetime.now()

# If token is not found, prompt for it
if not token:
    print("Discord token not found in environment variables.")
    token = input("Please enter your Discord bot token: ")
    if not token:
        raise ValueError("Discord token is required to run the bot.")

# Setup bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=discord_config.command_prefix, intents=intents, help_command=None)
trading_bot = None
optimization_manager = None

# Add command usage tracking for the bot
bot.command_usage = {}

# Add order history functionality
bot.order_history = OrderHistory()

# Create a simple exchange client mock that provides order history
class ExchangeClientMock:
    def __init__(self, order_history):
        self.order_history_obj = order_history
    
    def get_order_history(self):
        return self.order_history_obj.get_all_orders()
    
    def fetch_ticker(self, symbol):
        """Mock method for slash commands that need ticker data"""
        return {
            'symbol': symbol,
            'last': 50000.0,
            'percentage': 2.5,
            'change': 1200.0
        }
    
    def get_price(self, symbol):
        """Mock method for price queries"""
        return 50000.0

bot.exchange_client = ExchangeClientMock(bot.order_history)

def get_command_status():
    """Return lists of active and inactive commands"""
    all_commands = [cmd.name for cmd in bot.commands]
    active = list(bot.command_usage.keys())
    inactive = [c for c in all_commands if c not in active]
    return active, inactive

# Attach the method to the bot
bot.get_command_status = get_command_status

# Health monitoring variables
bot_healthy = False
last_heartbeat = datetime.now()

def update_health_status(status: bool = True):
    """Update the health check file for Docker health monitoring"""
    global bot_healthy, last_heartbeat
    bot_healthy = status
    last_heartbeat = datetime.now()
    
    try:
        if status:
            health_check_file.touch()
            logger.debug("Health check file updated")
        else:
            if health_check_file.exists():
                health_check_file.unlink()
            logger.warning("Health check file removed - bot unhealthy")
    except Exception as e:
        logger.error(f"Failed to update health status: {e}")

async def health_monitor():
    """Background task to monitor bot health"""
    while True:
        try:
            # Check if bot is connected and responsive
            if bot.is_ready() and trading_bot is not None:
                update_health_status(True)
            else:
                update_health_status(False)
                
            # Log health status every 5 minutes
            uptime = datetime.now() - startup_time
            if uptime.total_seconds() % 300 < 10:  # Every 5 minutes
                logger.info(f"Bot health check - Uptime: {uptime}, Connected: {bot.is_ready()}, Trading bot: {trading_bot is not None}")
                
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
            update_health_status(False)
            await asyncio.sleep(30)

async def start_health_server():
    """Start a simple HTTP health server for monitoring"""
    from aiohttp import web
    
    async def health_endpoint(request):
        """Health check endpoint"""
        uptime = datetime.now() - startup_time
        health_data = {
            "status": "healthy" if bot_healthy else "unhealthy",
            "uptime_seconds": int(uptime.total_seconds()),
            "bot_ready": bot.is_ready(),
            "trading_bot_initialized": trading_bot is not None,
            "last_heartbeat": last_heartbeat.isoformat(),
            "environment": os.getenv("ENVIRONMENT", "development")
        }
        
        status_code = 200 if bot_healthy else 503
        return web.json_response(health_data, status=status_code)
    
    async def metrics_endpoint(request):
        """Metrics endpoint for monitoring"""
        uptime = datetime.now() - startup_time
        metrics = {
            "bot_uptime_seconds": int(uptime.total_seconds()),
            "bot_connected": 1 if bot.is_ready() else 0,
            "trading_bot_ready": 1 if trading_bot is not None else 0,
            "guild_count": len(bot.guilds) if bot.is_ready() else 0,
            "user_count": sum(guild.member_count for guild in bot.guilds) if bot.is_ready() else 0
        }
        
        # Convert to Prometheus format if requested
        if request.headers.get('Accept') == 'text/plain':
            prometheus_format = ""
            for key, value in metrics.items():
                prometheus_format += f"{key} {value}\n"
            return web.Response(text=prometheus_format, content_type='text/plain')
        
        return web.json_response(metrics)
    
    app = web.Application()
    app.router.add_get('/health', health_endpoint)
    app.router.add_get('/metrics', metrics_endpoint)
    app.router.add_get('/healthz', health_endpoint)  # Kubernetes style
    
    # Try multiple ports if the default is in use
    ports_to_try = [8080, 8081, 8082, 8083, 8084]
    for port in ports_to_try:
        try:
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            logger.info(f"Health server started on port {port}")
            return
        except OSError as e:
            if e.errno == 48:  # Address already in use
                logger.warning(f"Port {port} is already in use, trying next port...")
                continue
            else:
                logger.error(f"Failed to start health server on port {port}: {e}")
                break
        except Exception as e:
            logger.error(f"Failed to start health server on port {port}: {e}")
            break
    
    logger.error("Failed to start health server on any available port")

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
    global trading_bot, optimization_manager
    try:
        trading_bot = TradingBot()
        bot.trading_bot = trading_bot
        logger.info("Trading bot initialized successfully")
        
        # Initialize optimization manager
        optimization_manager = OptimizationManager(
            exchange_client=trading_bot.client if hasattr(trading_bot, 'client') else None
        )
        logger.info("Optimization manager initialized successfully")
        
        # Load slash commands cog
        try:
            await bot.load_extension('src.bot.cogs.slash_commands')
            logger.info("Slash commands cog loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load slash commands cog: {e}")
        
        # Load RL commands cog
        try:
            rl_commands_cog = RLCommands(bot)
            await bot.add_cog(rl_commands_cog)
            logger.info("RL commands cog loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load RL commands cog: {e}")
        
        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s)")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
        
        # Start health monitoring and HTTP server
        asyncio.create_task(health_monitor())
        asyncio.create_task(start_health_server())
        
        # Update health status to healthy
        update_health_status(True)
        
        logger.info(f"Bot is ready! Connected to {len(bot.guilds)} guilds")
        logger.info(f"Health monitoring started - Health server will attempt to start on available ports")
        
    except Exception as e:
        logger.error(f"Failed to initialize bot components: {e}")
        traceback.print_exc()
        update_health_status(False)

@bot.event
async def on_command(ctx):
    """Track command usage"""
    if ctx.command:
        bot.command_usage[ctx.command.name] = datetime.now()
        logger.debug(f"Command executed: {ctx.command.name} by {ctx.author}")

@bot.command(name='help')
async def help_menu(ctx):
    """Display help information for the trading bot"""
    embed = discord.Embed(title="Trading Bot", color=0x2F3136)
    embed.set_author(name="Trading Bot", icon_url="https://i.imgur.com/8dQlQAW.png")
    embed.set_footer(text="Page 1/2")
    
    # Meta section
    embed.add_field(name="Meta", value="------------------------", inline=False)
    embed.add_field(name="Meta commands related to the bot", value="------------------------", inline=False)
    
    # Getting Started section
    embed.add_field(name="Getting Started", value="", inline=False)
    
    getting_started_text = (
        "b!help: How to use the trading bot\n"
        "b!tip: Get some tips about Trading Bot\n"
        "b!exchanges: List available exchanges\n"
        "b!test_connection: Test connection to exchanges\n"
        "b!health: Check bot health status\n"
        "b!categories: Show a list of all available categories\n"
    )
    embed.add_field(name="\u200b", value=getting_started_text, inline=False)
    
    # Trading section
    embed.add_field(name="Trading", value="", inline=False)
    
    trading_text = (
        "b!price: Get current price for a cryptocurrency\n"
        "b!balance: Check your account balance\n"
        "b!buy: Execute a buy order\n"
        "b!sell: Execute a sell order\n"
        "b!chart: Display a price chart for a cryptocurrency\n"
        "b!advanced_buy: Execute a buy with risk management\n"
    )
    embed.add_field(name="\u200b", value=trading_text, inline=False)
    
    # Strategy section
    embed.add_field(name="Strategies", value="", inline=False)
    
    strategy_text = (
        "b!strategies: Show available trading strategies\n"
        "b!analyze: Analyze a coin with a specific strategy\n"
        "b!strategy_chart: Generate chart with strategy signals\n"
        "b!add_strategy: Add a new trading strategy\n"
        "b!remove_strategy: Remove an existing strategy\n"
        "b!list_active_strategies: Show your active strategies\n"
    )
    embed.add_field(name="\u200b", value=strategy_text, inline=False)
    
    await ctx.send(embed=embed)
    
    # Create a second embed for additional commands
    embed2 = discord.Embed(title="Trading Bot", color=0x2F3136)
    embed2.set_footer(text="Page 2/2")
    
    # Indicators section
    embed2.add_field(name="Indicators", value="", inline=False)
    
    indicators_text = (
        "b!indicator: Analyze a specific indicator on a coin\n"
        "b!indicator_chart: Generate chart with indicator values\n"
        "b!help_indicators: Show available indicators and usage\n"
        "b!dual_macd_rsi: Advanced dual timeframe MACD+RSI analysis\n"
    )
    embed2.add_field(name="\u200b", value=indicators_text, inline=False)
    
    # Signal section
    embed2.add_field(name="Signals", value="", inline=False)
    
    signals_text = (
        "b!signal: Send a trading signal to the channel\n"
        "b!sc01: Send a SC01 trading signal\n"
        "b!sc_add: Add a new signal configuration\n"
        "b!generate_signal: Auto-generate a trading signal\n"
        "b!market_signals: Show recent market signals\n"
        "b!live_signal: Get live trading signals\n"
    )
    embed2.add_field(name="\u200b", value=signals_text, inline=False)
    
    # Optimization section
    embed2.add_field(name="Optimization", value="", inline=False)
    
    optimization_text = (
        "b!optimize_params: Optimize strategy parameters\n"
        "b!genetic_optimize: Use genetic algorithm for optimization\n"
        "b!market_regime: Detect current market regime\n"
        "b!risk_settings: Update your risk management settings\n"
        "b!position_size: Calculate optimal position size\n"
        "b!position_size_advanced: Advanced position sizing\n"
    )
    embed2.add_field(name="\u200b", value=optimization_text, inline=False)
    
    await ctx.send(embed=embed2)

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
        # Add order to history
        current_price = trading_bot.get_price(symbol)
        bot.order_history.add_order(
            order_id=str(order.get('orderId', '')),
            symbol=symbol,
            side='BUY',
            amount=quantity,
            price=float(current_price) if current_price else 0.0,
            status='placed',
            order_type='market'
        )
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
        # Add order to history
        current_price = trading_bot.get_price(symbol)
        bot.order_history.add_order(
            order_id=str(order.get('orderId', '')),
            symbol=symbol,
            side='SELL',
            amount=quantity,
            price=float(current_price) if current_price else 0.0,
            status='placed',
            order_type='market'
        )
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

@bot.command(name='sync')
async def sync_commands(ctx, guild_id: int = None):
    """Sync slash commands (Admin only)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ You need administrator permissions to sync commands.")
        return
    
    try:
        # If no guild_id provided, use current guild for instant sync
        if guild_id is None:
            guild_id = ctx.guild.id if ctx.guild else None
        
        status_msg = await ctx.send("🔄 Syncing slash commands...")
        
        if guild_id:
            # Sync to specific guild (instant)
            guild = discord.Object(id=guild_id)
            synced = await bot.tree.sync(guild=guild)
            await status_msg.edit(
                embed=discord.Embed(
                    title="✅ Slash Commands Synced",
                    description=f"Synced **{len(synced)} commands** to **{ctx.guild.name}** (instant)",
                    color=0x00ff00
                )
            )
            logger.info(f"Synced {len(synced)} slash commands to guild {guild_id}")
        else:
            # Global sync (takes up to 1 hour)
            synced = await bot.tree.sync()
            await status_msg.edit(
                embed=discord.Embed(
                    title="✅ Slash Commands Synced Globally",
                    description=f"Synced **{len(synced)} commands** globally (takes up to 1 hour)",
                    color=0x00ff00
                )
            )
            logger.info(f"Synced {len(synced)} slash commands globally")
            
    except Exception as e:
        logger.error(f"Error in sync command: {e}")
        await ctx.send(f"❌ Error syncing commands: {str(e)}")

@bot.command(name='health')
async def bot_health(ctx):
    """Check the bot's health status and system information"""
    try:
        uptime = datetime.now() - startup_time
        
        embed = discord.Embed(title="🏥 Bot Health Status", color=0x00ff00 if bot_healthy else 0xff0000)
        
        # Basic status
        embed.add_field(name="Overall Status", value="🟢 Healthy" if bot_healthy else "🔴 Unhealthy", inline=True)
        embed.add_field(name="Discord Connection", value="🟢 Connected" if bot.is_ready() else "🔴 Disconnected", inline=True)
        embed.add_field(name="Trading Bot", value="🟢 Ready" if trading_bot is not None else "🔴 Not Ready", inline=True)
        
        # Uptime and performance
        embed.add_field(name="Uptime", value=f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds%3600)//60}m", inline=True)
        embed.add_field(name="Last Heartbeat", value=last_heartbeat.strftime('%H:%M:%S'), inline=True)
        embed.add_field(name="Environment", value=os.getenv("ENVIRONMENT", "development"), inline=True)
        
        # Guild information
        if bot.is_ready():
            embed.add_field(name="Guilds", value=len(bot.guilds), inline=True)
            embed.add_field(name="Users", value=sum(guild.member_count for guild in bot.guilds), inline=True)
        else:
            embed.add_field(name="Guilds", value="N/A", inline=True)
            embed.add_field(name="Users", value="N/A", inline=True)
        
        # Exchange connection status
        exchange_status = "🟢 Connected" if trading_bot and hasattr(trading_bot, 'client') else "🔴 Disconnected"
        embed.add_field(name="Exchange", value=exchange_status, inline=True)
        
        # Health server info
        embed.add_field(name="Health Endpoint", value="http://localhost:8080/health", inline=False)
        
        embed.set_footer(text=f"Health check by {ctx.author.display_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        error_embed = discord.Embed(title="❌ Health Check Error", color=0xff0000)
        error_embed.add_field(name="Error", value=str(e), inline=False)
        await ctx.send(embed=error_embed)

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

@bot.command(name='risk_settings')
async def update_risk_settings(ctx, risk_per_trade: float = None, max_daily_loss: float = None, trailing_stop: float = None):
    """Update risk management settings
    
    Parameters:
    - risk_per_trade: Risk per trade as percentage (e.g., 2 for 2%)
    - max_daily_loss: Maximum daily loss as percentage (e.g., 5 for 5%)
    - trailing_stop: Trailing stop percentage (e.g., 1.5 for 1.5%)
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    # Convert percentages to decimals
    if risk_per_trade is not None:
        risk_per_trade = risk_per_trade / 100
    if max_daily_loss is not None:
        max_daily_loss = max_daily_loss / 100
    if trailing_stop is not None:
        trailing_stop = trailing_stop / 100
    
    # Update risk parameters
    trading_bot.update_risk_parameters(
        max_risk_per_trade=risk_per_trade,
        max_daily_loss=max_daily_loss,
        trailing_stop_percent=trailing_stop
    )
    
    # Prepare response message
    response = "Risk settings updated:\n"
    if risk_per_trade is not None:
        response += f"• Risk per trade: {risk_per_trade * 100}%\n"
    if max_daily_loss is not None:
        response += f"• Max daily loss: {max_daily_loss * 100}%\n"
    if trailing_stop is not None:
        response += f"• Trailing stop: {trailing_stop * 100}%\n"
    
    await ctx.send(response)

@bot.command(name='position_size')
async def calculate_position_size(ctx, symbol: str, entry_price: float, stop_loss: float):
    """Calculate the optimal position size based on risk management
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - entry_price: The planned entry price
    - stop_loss: The stop loss price
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    position_size = trading_bot.calculate_position_size(symbol, stop_loss)
    
    if position_size > 0:
        current_price = trading_bot.get_price(symbol)
        risk_amount = abs(float(current_price) - stop_loss) * position_size
        
        await ctx.send(f"**Position Size Calculation for {symbol}**\n"
                      f"• Entry Price: {entry_price}\n"
                      f"• Stop Loss: {stop_loss}\n"
                      f"• Current Price: {current_price}\n"
                      f"• Position Size: {position_size:.6f} units\n"
                      f"• Risk Amount: ${risk_amount:.2f} USDT\n"
                      f"• Risk per Trade: {trading_bot.max_risk_per_trade * 100:.1f}%")
    else:
        await ctx.send(f"Failed to calculate position size for {symbol}. Check if daily loss limit has been reached.")

@bot.command(name='advanced_buy')
async def advanced_buy(ctx, symbol: str, quantity: float, take_profit: float = None, stop_loss: float = None):
    """Buy a cryptocurrency with take profit and stop loss orders
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - quantity: Amount to buy
    - take_profit: Optional take profit price
    - stop_loss: Optional stop loss price
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    await ctx.send(f"Placing advanced buy order for {quantity} {symbol}...")
    
    orders = trading_bot.place_advanced_order(symbol, 'BUY', quantity, take_profit, stop_loss)
    
    if orders and len(orders) > 0:
        main_order = orders[0]
        response = f"**Order placed successfully**\n"
        response += f"• Symbol: {symbol}\n"
        response += f"• Quantity: {quantity}\n"
        response += f"• Type: {main_order['type']}\n"
        response += f"• Status: {main_order['status']}\n"
        
        if len(orders) > 1:
            response += f"• Take Profit/Stop Loss orders: {len(orders) - 1} placed\n"
        
        await ctx.send(response)
    else:
        await ctx.send(f"Failed to place order for {symbol}.")

@bot.command(name='dual_macd_rsi')
async def dual_macd_rsi(ctx, symbol: str, interval: str = '1h', higher_tf: str = '4h'):
    """Analyze a symbol using dual timeframe MACD+RSI strategy
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - interval: Time interval for analysis (default: 1h)
    - higher_tf: Higher timeframe for confirmation (default: 4h)
    """
    if not trading_bot:
        await ctx.send("Trading bot is not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    if interval not in valid_intervals or higher_tf not in valid_intervals:
        await ctx.send(f"Invalid interval. Please use one of: {', '.join(valid_intervals)}")
        return
    
    await ctx.send(f"Analyzing {symbol} with dual timeframe MACD+RSI strategy ({interval} + {higher_tf})...")
    
    try:
        # Get data for both timeframes
        df = trading_bot.get_market_data(symbol, interval, limit=100)
        higher_tf_data = trading_bot.get_market_data(symbol, higher_tf, limit=100)
        
        if df is None or higher_tf_data is None:
            await ctx.send(f"Failed to get market data for {symbol}.")
            return
        
        # Get the indicator
        factory = IndicatorFactory()
        indicator = factory.get_indicator('dual_macd_rsi')
        
        # Run analysis
        result = indicator.get_signal(df, higher_tf_data)
        
        if result is None:
            await ctx.send(f"Failed to analyze {symbol} with dual timeframe strategy.")
            return
        
        # Get the latest signal
        latest = result.iloc[-1]
        signal_value = latest['signal']
        
        # Prepare response
        response = f"**Dual Timeframe MACD+RSI Analysis for {symbol}**\n"
        response += f"• Timeframes: {interval} + {higher_tf}\n"
        response += f"• RSI: {latest['rsi']:.2f}\n"
        response += f"• MACD: {latest['macd']:.6f}\n"
        response += f"• Signal Line: {latest['signal_line']:.6f}\n"
        response += f"• Histogram: {latest['histogram']:.6f}\n"
        
        if signal_value == 1.0:
            response += f"• **Signal: BUY** 🟢\n"
            
            # Calculate entry, take profit and stop loss
            current_price = float(trading_bot.get_price(symbol))
            atr = df['high'].rolling(14).max() - df['low'].rolling(14).min()
            last_atr = atr.iloc[-1]
            
            stop_loss = current_price - (last_atr * 1.5)
            take_profit = current_price + (last_atr * 3.0)
            
            response += f"• Entry: {current_price:.4f}\n"
            response += f"• Take Profit: {take_profit:.4f}\n"
            response += f"• Stop Loss: {stop_loss:.4f}\n"
            response += f"• Risk/Reward: 1:2\n"
            
        elif signal_value == -1.0:
            response += f"• **Signal: SELL** 🔴\n"
        else:
            response += f"• **Signal: NEUTRAL** ⚪\n"
            
        await ctx.send(response)
        
        # Generate chart with indicators
        chart_data = trading_bot.generate_chart(symbol, interval, limit=100, with_indicators=True)
        if chart_data:
            await ctx.send(file=File(chart_data, filename=f"{symbol}_{interval}_analysis.png"))
            
    except Exception as e:
        logger.error(f"Error in dual_macd_rsi command: {str(e)}")
        await ctx.send(f"An error occurred while analyzing {symbol}: {str(e)}")

@bot.command(name='exchanges')
async def list_exchanges(ctx):
    """List all available exchanges through CCXT"""
    try:
        # Get all exchange IDs from CCXT
        exchange_ids = ccxt.exchanges
        
        # Format the response
        response = "**Available Exchanges**\n"
        
        # Group exchanges by starting letter for cleaner output
        grouped = {}
        for ex_id in sorted(exchange_ids):
            first_letter = ex_id[0].upper()
            if first_letter not in grouped:
                grouped[first_letter] = []
            grouped[first_letter].append(ex_id)
        
        # Format the output
        for letter, exchanges in grouped.items():
            response += f"\n**{letter}**\n"
            # Create chunks of exchanges for better formatting
            chunks = [exchanges[i:i + 5] for i in range(0, len(exchanges), 5)]
            for chunk in chunks:
                response += "• " + ", ".join(chunk) + "\n"
        
        # Send the response in chunks if needed to avoid Discord's character limit
        if len(response) > 2000:
            parts = [response[i:i + 1900] for i in range(0, len(response), 1900)]
            for part in parts:
                await ctx.send(part)
        else:
            await ctx.send(response)
    except Exception as e:
        logger.error(f"Error in list_exchanges command: {str(e)}")
        await ctx.send(f"An error occurred while listing exchanges: {str(e)}")

@bot.command(name='optimize_params')
@cooldown(1, 60, BucketType.user)  # Limit to once per minute per user
async def optimize_parameters(ctx, symbol: str = None, timeframe: str = '1h'):
    """
    Optimize strategy parameters using grid search.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH) (optional)
    - timeframe: Time interval (default: 1h)
    """
    if not optimization_manager:
        await ctx.send("Optimization manager is not initialized. Check logs for details.")
        return
    
    # Prevent concurrent executions
    if is_command_running(ctx.author.id, "optimize"):
        await ctx.send("Another optimization command is already running. Please wait for it to complete.")
        return
    
    try:
        set_command_running(ctx.author.id, "optimize")
        
        # Format symbol
        symbols = []
        if symbol:
            symbol = symbol.upper()
            if not symbol.endswith('/USDT'):
                symbol = f"{symbol}/USDT"
            symbols = [symbol]
        else:
            # Use default symbols
            symbols = ['BTC/USDT', 'ETH/USDT']
        
        # Send initial message
        status_msg = await ctx.send(f"⏳ Optimizing strategy parameters for {symbols} on {timeframe} timeframe... This may take a moment.")
        
        # Run the optimization
        params = optimization_manager.run_parameter_optimization(symbols, timeframe)
        
        # Format results
        embed = discord.Embed(title="Parameter Optimization Results", color=0x00ff00)
        embed.add_field(name="Symbols", value=", ".join(symbols), inline=False)
        embed.add_field(name="Timeframe", value=timeframe, inline=False)
        
        # Add parameters
        for param_name, param_value in params.items():
            embed.add_field(name=param_name, value=str(param_value), inline=True)
        
        embed.set_footer(text=f"Optimized by {ctx.author.display_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Edit the message with results
        await status_msg.edit(content=None, embed=embed)
        
    except Exception as e:
        await ctx.send(f"Error during parameter optimization: {str(e)}")
        logger.error(f"Parameter optimization error: {e}")
        traceback.print_exc()
    finally:
        clear_command_running(ctx.author.id, "optimize")

@bot.command(name='genetic_optimize')
@cooldown(1, 300, BucketType.user)  # Limit to once per 5 minutes per user
async def genetic_optimization(ctx, symbol: str, timeframe: str = '1h', generations: int = 20):
    """
    Optimize strategy using genetic algorithm.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - timeframe: Time interval (default: 1h)
    - generations: Number of generations (default: 20)
    """
    if not optimization_manager:
        await ctx.send("Optimization manager is not initialized. Check logs for details.")
        return
    
    # Prevent concurrent executions
    if is_command_running(ctx.author.id, "genetic"):
        await ctx.send("Another optimization command is already running. Please wait for it to complete.")
        return
    
    try:
        set_command_running(ctx.author.id, "genetic")
        
        # Format symbol
        symbol = symbol.upper()
        if not symbol.endswith('/USDT'):
            symbol = f"{symbol}/USDT"
        
        # Limit generations to prevent abuse
        generations = min(generations, 50)
        
        # Send initial message
        status_msg = await ctx.send(f"⏳ Running genetic optimization for {symbol} on {timeframe} timeframe with {generations} generations... This may take several minutes.")
        
        # Configure the genetic optimizer
        optimization_manager.genetic_optimizer.generations = generations
        
        # Run the optimization
        result = optimization_manager.run_genetic_optimization(symbol, timeframe)
        
        # Format results
        embed = discord.Embed(title="Genetic Algorithm Optimization Results", color=0x00ff00)
        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Timeframe", value=timeframe, inline=True)
        embed.add_field(name="Generations", value=generations, inline=True)
        embed.add_field(name="Best Fitness", value=f"{result['best_fitness']:.4f}", inline=True)
        embed.add_field(name="Elapsed Time", value=f"{result['elapsed_time']:.2f}s", inline=True)
        
        # Add best parameters
        embed.add_field(name="Best Parameters", value="", inline=False)
        for param_name, param_value in result['best_params'].items():
            embed.add_field(name=param_name, value=str(param_value), inline=True)
        
        embed.set_footer(text=f"Optimized by {ctx.author.display_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Edit the message with results
        await status_msg.edit(content=None, embed=embed)
        
    except Exception as e:
        await ctx.send(f"Error during genetic optimization: {str(e)}")
        logger.error(f"Genetic optimization error: {e}")
        traceback.print_exc()
    finally:
        clear_command_running(ctx.author.id, "genetic")

@bot.command(name='market_regime')
@cooldown(1, 30, BucketType.user)
async def detect_market_regime(ctx, symbol: str, timeframe: str = '1h'):
    """
    Detect the current market regime and get optimized parameters.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - timeframe: Time interval (default: 1h)
    """
    if not optimization_manager:
        await ctx.send("Optimization manager is not initialized. Check logs for details.")
        return
    
    try:
        # Format symbol
        symbol = symbol.upper()
        if not symbol.endswith('/USDT'):
            symbol = f"{symbol}/USDT"
        
        # Send initial message
        status_msg = await ctx.send(f"⏳ Analyzing market regime for {symbol} on {timeframe} timeframe...")
        
        # Get market regime
        regime_info = optimization_manager.get_market_regime(symbol, timeframe)
        
        # Format results
        embed = discord.Embed(title=f"Market Regime Analysis: {symbol}", color=0x00ff00)
        
        # Add regime details
        regime_name = regime_info.get('regime_name', 'Unknown')
        color = {
            'Ranging': 0xffff00,  # Yellow
            'Trending Up': 0x00ff00,  # Green 
            'Trending Down': 0xff0000,  # Red
            'Volatile': 0xffa500   # Orange
        }.get(regime_name, 0x808080)  # Default gray
        
        embed.color = color
        embed.add_field(name="Market Regime", value=regime_name, inline=False)
        
        # Add technical indicators
        embed.add_field(name="Volatility", value=f"{regime_info.get('volatility', 0):.4f}", inline=True)
        embed.add_field(name="Trend Strength", value=f"{regime_info.get('trend_strength', 0):.4f}", inline=True)
        embed.add_field(name="Volume Ratio", value=f"{regime_info.get('volume_ratio', 0):.2f}", inline=True)
        embed.add_field(name="RSI", value=f"{regime_info.get('rsi', 0):.2f}", inline=True)
        embed.add_field(name="MACD", value=f"{regime_info.get('macd', 0):.4f}", inline=True)
        embed.add_field(name="EMA Ratio", value=f"{regime_info.get('ema_ratio', 0):.4f}", inline=True)
        
        embed.set_footer(text=f"Analyzed by {ctx.author.display_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Edit the message with results
        await status_msg.edit(content=None, embed=embed)
        
        # Now optimize for current regime
        await status_msg.edit(content="⏳ Optimizing parameters for current market conditions...", embed=embed)
        
        # Get optimized parameters
        params_result = optimization_manager.optimize_for_market_conditions(symbol, timeframe)
        
        # Create parameters embed
        params_embed = discord.Embed(title=f"Optimized Parameters for {symbol} ({regime_name})", color=color)
        
        if 'parameters' in params_result:
            for param_name, param_value in params_result['parameters'].items():
                params_embed.add_field(name=param_name, value=str(param_value), inline=True)
        else:
            params_embed.add_field(name="Error", value="Could not optimize parameters", inline=False)
        
        params_embed.set_footer(text=f"Optimized by {ctx.author.display_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Send optimized parameters
        await ctx.send(embed=params_embed)
        
    except Exception as e:
        await ctx.send(f"Error analyzing market regime: {str(e)}")
        logger.error(f"Market regime analysis error: {e}")
        traceback.print_exc()

@bot.command(name='position_size_advanced')
@cooldown(1, 10, BucketType.user)
async def advanced_position_size(ctx, symbol: str, account_balance: float = 1000.0, risk_percent: float = 2.0):
    """
    Calculate optimal position size using dynamic risk management.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - account_balance: Your account balance in USDT (default: 1000.0)
    - risk_percent: Risk percentage (default: 2.0)
    """
    if not optimization_manager:
        await ctx.send("Optimization manager is not initialized. Check logs for details.")
        return
    
    try:
        # Format symbol
        symbol = symbol.upper()
        if not symbol.endswith('/USDT'):
            symbol = f"{symbol}/USDT"
        
        # Send initial message
        status_msg = await ctx.send(f"⏳ Calculating optimal position size for {symbol} with {risk_percent}% risk...")
        
        # Calculate position size with advanced risk management
        position = optimization_manager.calculate_position_size(symbol, account_balance, risk_percent)
        
        # Format results
        embed = discord.Embed(title=f"Advanced Position Size: {symbol}", color=0x00ff00)
        
        if 'error' in position:
            embed.color = 0xff0000  # Red for error
            embed.add_field(name="Error", value=position['error'], inline=False)
        else:
            # Add position details
            embed.add_field(name="Account Balance", value=f"${account_balance:.2f}", inline=True)
            embed.add_field(name="Risk Percentage", value=f"{position['risk_percent']:.2f}%", inline=True)
            embed.add_field(name="Risk Amount", value=f"${position['risk_amount']:.2f}", inline=True)
            
            embed.add_field(name="Current Price", value=f"${position['current_price']:.2f}", inline=True)
            embed.add_field(name="Entry Price", value=f"${position['entry_price']:.2f}", inline=True)
            
            embed.add_field(name="Stop Loss", value=f"${position['stop_loss']:.2f}", inline=True)
            embed.add_field(name="Take Profit", value=f"${position['take_profit']:.2f}", inline=True)
            embed.add_field(name="Risk/Reward Ratio", value=f"{position['risk_reward']:.2f}", inline=True)
            
            embed.add_field(name="Position Size", value=f"{position['size']:.6f} {symbol.split('/')[0]}", inline=False)
            embed.add_field(name="Position Value", value=f"${position['value']:.2f}", inline=True)
            
            embed.add_field(name="Signal", value=position['signal'], inline=True)
        
        embed.set_footer(text=f"Calculated by {ctx.author.display_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Edit the message with results
        await status_msg.edit(content=None, embed=embed)
        
    except Exception as e:
        await ctx.send(f"Error calculating position size: {str(e)}")
        logger.error(f"Position size calculation error: {e}")
        traceback.print_exc()

@bot.command(name='cmdsta')
async def command_status(ctx):
    """Show all commands grouped by active and inactive"""
    await status_commands(ctx)

@bot.command(name='actcmd')
async def active_commands_cmd(ctx):
    """Show commands that have been used"""
    await active_commands(ctx)

@bot.command(name='inactcmd')
async def inactive_commands_cmd(ctx):
    """Show commands that exist but haven't been used"""
    await inactive_commands(ctx)

@bot.command(name='orders')
async def order_history_cmd(ctx):
    """Display recent order history"""
    await order_history(ctx)

@bot.command(name='slashinfo')
async def slash_info(ctx):
    """Check slash commands status and provide troubleshooting info"""
    try:
        embed = discord.Embed(
            title="🔍 Slash Commands Diagnostic",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        # Check registered commands
        app_commands = bot.tree.get_commands()
        embed.add_field(
            name="📝 Registered Commands",
            value=f"**{len(app_commands)} commands** registered:\n" + 
                  "\n".join([f"• `/{cmd.name}` - {cmd.description[:50]}..." for cmd in app_commands[:5]]),
            inline=False
        )
        
        # Bot permissions info
        if ctx.guild:
            bot_member = ctx.guild.get_member(bot.user.id)
            permissions = bot_member.guild_permissions
            
            required_perms = [
                ("Use Slash Commands", permissions.use_slash_commands),
                ("Send Messages", permissions.send_messages),
                ("Embed Links", permissions.embed_links),
                ("View Channel", permissions.view_channel)
            ]
            
            perms_text = "\n".join([
                f"{'✅' if has_perm else '❌'} {perm_name}" 
                for perm_name, has_perm in required_perms
            ])
            
            embed.add_field(
                name="🔐 Bot Permissions",
                value=perms_text,
                inline=True
            )
        
        # Troubleshooting steps
        troubleshooting = (
            "**If slash commands don't appear:**\n"
            "1. Check bot has `applications.commands` scope\n"
            "2. Use `b!sync` to sync to this server\n"
            "3. Wait up to 1 hour for global commands\n"
            "4. Try kicking and re-inviting the bot\n"
            "5. Restart Discord app completely"
        )
        
        embed.add_field(
            name="🛠️ Troubleshooting",
            value=troubleshooting,
            inline=False
        )
        
        embed.add_field(
            name="📱 Quick Fix",
            value="Run `b!sync` to instantly sync commands to this server!",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in slashinfo command: {e}")
        await ctx.send(f"❌ Error getting slash command info: {str(e)}")

def run_bot():
    """Run the Discord bot"""
    bot.run(token)

if __name__ == "__main__":
    run_bot()    