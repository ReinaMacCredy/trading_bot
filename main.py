import discord
from discord.ext import commands
import logging
from typing import List, Optional
from dotenv import load_dotenv
import os
import traceback
from discord import File
from datetime import datetime
import random
import ccxt
import json
import asyncio
import aiohttp
from pathlib import Path
import pandas as pd

# Import new bot core
from src.bot.bot_core import create_bot

# Import optimization components
from src.trading.optimization import OptimizationManager
from src.trading.optimization import ParameterOptimizer
from src.trading.strategies import MultiIndicatorStrategy
from src.trading.optimization import GeneticOptimizer
from src.trading.optimization import MLOptimizer
from src.trading.core import DynamicRiskManager

# Import command functions
from src.bot.commands.history_commands import status_commands, active_commands, inactive_commands
from src.trading.core import OrderHistory

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
health_server_port = 8080  # Default port, will be updated if a different port is used

# If token is not found, prompt for it
if not token:
    print("Discord token not found in environment variables.")
    token = input("Please enter your Discord bot token: ")
    if not token:
        raise ValueError("Discord token is required to run the bot.")

# Setup bot
bot = create_bot()

# trading_bot = None
optimization_manager = None

# Add command usage tracking for the bot
# bot.command_usage = {}

# Add order history functionality
# bot.order_history = OrderHistory()

# Create a simple exchange client mock that provides order history
# class ExchangeClientMock:
#     def __init__(self, order_history):
#         self.order_history_obj = order_history
#
#     def get_order_history(self):
#         return self.order_history_obj.get_all_orders()
#
#     async def fetch_ticker(self, symbol):
#         """Mock async method for slash commands that need ticker data"""
#         return {
#             'symbol': symbol,
#             'last': 50000.0,
#             'percentage': 2.5,
#             'change': 1200.0,
#             'bid': 49950.0,
#             'ask': 50050.0,
#             'baseVolume': 1000.0,
#             'timestamp': int(datetime.now().timestamp() * 1000)
#         }
#
#     def get_price(self, symbol):
#         """Mock method for price queries"""
#         return 50000.0
#
#     async def fetch_ohlcv(self, symbol, timeframe='1h', limit=100, since=None):
#         """Mock async method for OHLCV data"""
#         # Generate mock OHLCV data
#         import random
#         base_price = 50000.0
#         data = []
#         for i in range(limit):
#             timestamp = int((datetime.now().timestamp() - (limit - i) * 3600) * 1000)
#             open_price = base_price + random.uniform(-1000, 1000)
#             high_price = open_price + random.uniform(0, 500)
#             low_price = open_price - random.uniform(0, 500)
#             close_price = open_price + random.uniform(-300, 300)
#             volume = random.uniform(100, 1000)
#             data.append([timestamp, open_price, high_price, low_price, close_price, volume])
#         return data
#
#     async def fetch_balance(self):
#         """Mock async method for balance queries"""
#         return {
#             'total': {'BTC': 0.1, 'ETH': 2.5, 'USDT': 1000.0},
#             'free': {'BTC': 0.1, 'ETH': 2.5, 'USDT': 1000.0},
#             'used': {'BTC': 0.0, 'ETH': 0.0, 'USDT': 0.0}
#         }
#
#     async def test_connection(self):
#         """Mock async method for connection testing"""
#         return True
#
#     def get_exchange_name(self):
#         """Mock method to get exchange name"""
#         return "mock_exchange"
#
#     def is_sandbox(self):
#         """Mock method to check if sandbox mode"""
#         return True

# bot.exchange_client = ExchangeClientMock(bot.order_history)

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
            # The is_ready() method should be available now
            update_health_status(bot.is_ready())
                
            # Log health status every 5 minutes
            uptime = datetime.now() - startup_time
            if uptime.total_seconds() % 300 < 10:  # Every 5 minutes
                logger.info(f"Bot health check - Uptime: {uptime}, Connected: {bot.is_ready()}, Exchange Client: {bot.exchange_client is not None}")
                
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
            update_health_status(False)
            await asyncio.sleep(30)

async def start_health_server():
    """Start a simple HTTP health server for monitoring"""
    from aiohttp import web
    global health_server_port
    
    async def health_endpoint(request):
        """Health check endpoint"""
        uptime = datetime.now() - startup_time
        
        # Use the is_ready() method
        health_data = {
            "status": "healthy" if bot_healthy else "unhealthy",
            "uptime_seconds": int(uptime.total_seconds()),
            "bot_ready": bot.is_ready(),
            "trading_components_ready": bot.exchange_client is not None,
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
            "trading_bot_ready": 1 if bot.exchange_client is not None else 0,
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
            health_server_port = port  # Update the global port variable
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
    global optimization_manager
    try:
        # trading_bot = TradingBot()
        # bot.trading_bot = trading_bot
        # logger.info("Trading bot initialized successfully")
        
        # Initialize optimization manager
        if bot.exchange_client:
            optimization_manager = OptimizationManager(
                exchange_client=bot.exchange_client
            )
            logger.info("Optimization manager initialized successfully using bot.exchange_client")
        else:
            logger.warning("Optimization manager NOT initialized: bot.exchange_client not available at on_ready. Using None.")
            optimization_manager = OptimizationManager(exchange_client=None)
        
        # Load slash commands cog
        # try:
        #     await bot.load_extension('src.bot.cogs.slash_commands')
        #     logger.info("Slash commands cog loaded successfully from main.py on_ready")
        # except Exception as e:
        #     logger.error(f"Failed to load slash commands cog from main.py on_ready: {e}")
        
        # Load RL commands cog
        try:
            rl_commands_cog = RLCommands(bot)
            await bot.add_cog(rl_commands_cog)
            logger.info("RL commands cog loaded successfully from main.py")
        except Exception as e:
            logger.error(f"Failed to load RL commands cog from main.py: {e}")
        
        # Sync slash commands
        # try:
        #     synced = await bot.tree.sync()
        #     logger.info(f"Synced {len(synced)} slash command(s) from main.py on_ready")
        # except Exception as e:
        #     logger.error(f"Failed to sync slash commands from main.py on_ready: {e}")
        
        # Add missing method for dual_macd_rsi command
        if not hasattr(bot, 'get_market_data'):
            async def get_market_data_wrapper(symbol, interval, limit=100, exchange=None):
                """Wrapper for get_market_data"""
                try:
                    logger.info(f"Fetching market data for {symbol} on {interval} timeframe")
                    
                    # If exchange client isn't initialized, return None
                    if not bot.exchange_client:
                        logger.error("Exchange client not initialized")
                        return None
                        
                    # Use exchange client to fetch OHLCV data
                    ohlcv_data = await bot.exchange_client.fetch_ohlcv(
                        symbol=symbol,
                        timeframe=interval,
                        limit=limit
                    )
                    
                    if not ohlcv_data or len(ohlcv_data) == 0:
                        logger.error(f"Failed to fetch market data for {symbol}")
                        return None
                    
                    # Convert to pandas DataFrame if it's not already
                    if not isinstance(ohlcv_data, pd.DataFrame):
                        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df.set_index('timestamp', inplace=True)
                    else:
                        df = ohlcv_data
                        
                    # Reset index to have timestamp as a column rather than index
                    if df.index.name == 'timestamp':
                        df = df.reset_index()
                    
                    # Ensure we have all required columns
                    required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    for col in required_columns:
                        if col not in df.columns:
                            logger.error(f"Missing required column {col} in market data")
                            return None
                    
                    return df
                    
                except Exception as e:
                    logger.error(f"Error getting market data for {symbol}: {str(e)}")
                    return None
            
            # Attach the method to the bot
            bot.get_market_data = get_market_data_wrapper
            logger.info("Added get_market_data method to bot for compatibility")
        
        # Start health monitoring and HTTP server (local to main.py)
        asyncio.create_task(health_monitor())
        asyncio.create_task(start_health_server())
        
        # Update health status to healthy
        update_health_status(True)
        
        logger.info(f"Main.py on_ready: Custom initializations (RL Cog, health monitor/server) complete.")
        
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
        "/price: Get current price for a cryptocurrency (slash command)\n"
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

# Removed traditional price command to prevent conflicts with slash command
# Use /price instead of b!price for price queries

@bot.command(name='balance')
async def get_balance(ctx):
    """Get your account balance"""
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    try:
        balances = await bot.exchange_client.fetch_balance()
        if not balances:
            await ctx.send("Failed to get account balance or no balance available.")
            return
        
        response = "**Your Account Balance:**\n"
        if 'free' in balances and isinstance(balances['free'], dict):
            for currency, amount in balances['free'].items():
                if amount > 0:
                    response += f"- {currency}: {amount:.8f}\n"
        elif isinstance(balances, dict):
            for currency, amount in balances.items():
                if isinstance(amount, (int,float)) and amount > 0 :
                     response += f"- {currency}: {amount}\n"
        else:
            response += "Could not parse balance data.\n"

        if len(response) == len("**Your Account Balance:**\n"):
            response += "No balances to display or unable to fetch details."
            
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        await ctx.send(f"An error occurred while fetching balance: {e}")
        return

    await ctx.send(response)

@bot.command(name='chart')
async def get_chart(ctx, symbol: str, interval: str = '1d', limit: int = 30):
    """Generate a price chart for a cryptocurrency.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - interval: Time interval (default: 1d)
    - limit: Number of data points (default: 30)
    """
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    if interval not in valid_intervals:
        await ctx.send(f"Invalid interval. Please use one of: {', '.join(valid_intervals)}")
        return
    
    await ctx.send(f"Generating chart for {symbol} ({interval})...")
    chart_data = await bot.generate_chart(symbol, interval, limit)
    
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
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    await ctx.send(f"Placing market buy order for {quantity} {symbol}...")
    try:
        order_result = await bot.exchange_client.create_market_buy_order(symbol, quantity)
        
        if order_result and order_result.success:
            response = f"Buy order for {quantity} {symbol} placed successfully. Order ID: {order_result.order_id}"
            if hasattr(bot, 'order_history') and hasattr(bot.order_history, 'add_order_from_result'):
                bot.order_history.add_order_from_result(order_result)
            elif hasattr(bot.exchange_client, 'order_history'):
                 bot.exchange_client.order_history.add_order_from_result(order_result)
        else:
            error_msg = order_result.error_message if order_result else "Unknown error creating order."
            response = f"Failed to place buy order for {quantity} {symbol}. Error: {error_msg}"
    except AttributeError as e:
        logger.error(f"Missing method for buy order: {e}")
        response = f"Buy command is not fully implemented with the new trading core: {e}"
    except Exception as e:
        logger.error(f"Error executing buy command: {e}")
        response = f"An error occurred: {e}"
        
    await ctx.send(response)

@bot.command(name='sell')
async def sell(ctx, symbol: str, quantity: float):
    """Sell a cryptocurrency at market price.
    
    Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    - quantity: Amount to sell
    """
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    await ctx.send(f"Placing market sell order for {quantity} {symbol}...")
    try:
        order_result = await bot.exchange_client.create_market_sell_order(symbol, quantity)
        
        if order_result and order_result.success:
            response = f"Sell order for {quantity} {symbol} placed successfully. Order ID: {order_result.order_id}"
            if hasattr(bot, 'order_history') and hasattr(bot.order_history, 'add_order_from_result'):
                bot.order_history.add_order_from_result(order_result)
            elif hasattr(bot.exchange_client, 'order_history'):
                 bot.exchange_client.order_history.add_order_from_result(order_result)
        else:
            error_msg = order_result.error_message if order_result else "Unknown error creating order."
            response = f"Failed to place sell order for {quantity} {symbol}. Error: {error_msg}"
    except AttributeError as e:
        logger.error(f"Missing method for sell order: {e}")
        response = f"Sell command is not fully implemented with the new trading core: {e}"
    except Exception as e:
        logger.error(f"Error executing sell command: {e}")
        response = f"An error occurred: {e}"

    await ctx.send(response)

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
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    if interval not in valid_intervals:
        await ctx.send(f"Invalid interval. Please use one of: {', '.join(valid_intervals)}")
        return
    
    await ctx.send(f"Analyzing {symbol} with {strategy} strategy ({interval})...")
    result = bot.analyze_symbol(strategy, symbol, interval)
    
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
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    if interval not in valid_intervals:
        await ctx.send(f"Invalid interval. Please use one of: {', '.join(valid_intervals)}")
        return
    
    await ctx.send(f"Generating strategy chart for {symbol} with {strategy} strategy ({interval})...")
    chart_data = await bot.generate_strategy_chart(strategy, symbol, interval, limit)
    
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
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    if interval not in valid_intervals:
        await ctx.send(f"Invalid interval. Please use one of: {', '.join(valid_intervals)}")
        return
    
    success = bot.add_strategy(strategy, symbol, interval)
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
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    success = bot.remove_strategy(strategy, symbol, interval)
    if success:
        await ctx.send(f"Removed {strategy} strategy for {symbol} ({interval})")
    else:
        await ctx.send(f"Strategy not found: {strategy} for {symbol} ({interval})")

@bot.command(name='list_active_strategies')
async def list_active_strategies(ctx):
    """List all active trading strategies"""
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    strategies = bot.list_strategies()
    if not strategies:
        await ctx.send("No active strategies")
        return
    
    response = "**Active Trading Strategies:**\n"
    for i, strategy in enumerate(strategies, 1):
        response += f"{i}. {strategy['name']} - {strategy['symbol']} ({strategy['interval']})\n"
    
    await ctx.send(response)

@bot.command(name='test_connection')
async def test_binance_connection(ctx):
    """Test connection to the configured exchange"""
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized.")
        return
    
    connected = await bot.exchange_client.test_connection()
    exchange_name = bot.exchange_client.exchange_name if hasattr(bot.exchange_client, 'exchange_name') else "configured exchange"
    
    if connected:
        await ctx.send(f"Connection to {exchange_name} API successful! ✅")
    else:
        await ctx.send(f"Failed to connect to {exchange_name} API. Check logs for details. ❌")

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
        embed.add_field(name="Trading Bot", value="🟢 Ready" if bot.exchange_client is not None else "🔴 Not Ready", inline=True)
        
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
        exchange_status = "🟢 Connected" if bot.exchange_client and hasattr(bot.exchange_client, 'exchange_name') else "🔴 Disconnected"
        embed.add_field(name="Exchange", value=exchange_status, inline=True)
        
        # Health server info
        embed.add_field(name="Health Endpoint", value=f"http://localhost:{health_server_port}/health", inline=False)
        
        embed.set_footer(text=f"Health check by {ctx.author.display_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        error_embed = discord.Embed(title="❌ Health Check Error", color=0xff0000)
        error_embed.add_field(name="Error", value=str(e), inline=False)
        await ctx.send(embed=error_embed)

@bot.command(name='indicator')
async def analyze_indicator(ctx, indicator_name: str, symbol: str, interval: str = "1h", *args):
    """Analyze a specific indicator on a coin. TODO: Refactor with new TechnicalIndicators service."""
    await ctx.send("The 'indicator' command is temporarily disabled for refactoring. Please use specific analysis commands or strategy features.")
    return
    # This command needs significant refactoring to use bot.indicators (TechnicalIndicators service)
    # Original code used IndicatorFactory which is removed.
    # Example of how it might work (conceptual):
    # if not bot.exchange_client or not bot.indicators:
    #     await ctx.send("Trading or indicator services not ready.")
    #     return
    # try:
    #     ohlcv = await bot.exchange_client.fetch_ohlcv(symbol.upper().replace('/', ''), timeframe=interval, limit=200) # Adjust limit as needed
    #     if not ohlcv:
    #         await ctx.send(f"Could not fetch data for {symbol}.")
    #         return
    #     df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    #     df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    #     df.set_index('timestamp', inplace=True)

    #     indicator_method_name = f"calculate_{indicator_name.lower()}"
    #     if hasattr(bot.indicators, indicator_method_name):
    #         indicator_calc_method = getattr(bot.indicators, indicator_method_name)
    #         # Need to parse *args to pass correct parameters to specific calculate_... methods
    #         # For now, this is a placeholder
    #         indicator_result = indicator_calc_method(df) # This needs proper arg handling

    #         embed = discord.Embed(title=f"{indicator_result.name} Analysis for {symbol.upper()}", color=0x00ff00)
    #         embed.add_field(name="Current Value", value=f"{indicator_result.metadata.get('current_value', 'N/A')}", inline=True)
    #         embed.add_field(name="Signal", value=f"{indicator_result.signal}", inline=True)
    #         embed.add_field(name="Strength", value=f"{indicator_result.strength:.2f}" if indicator_result.strength is not None else "N/A", inline=True)
    #         # Add more details from indicator_result.metadata
    #         await ctx.send(embed=embed)
    #     else:
    #         await ctx.send(f"Indicator '{indicator_name}' is not supported by the new system or calculation method not found.")
    # except Exception as e:
    #     logger.error(f"Error in analyze_indicator: {e}")
    #     await ctx.send(f"An error occurred: {str(e)}")

@bot.command(name='indicator_chart')
async def generate_indicator_chart(ctx, indicator_name: str, symbol: str, interval: str = "1h", *args):
    """Generate a chart with indicator values. TODO: Refactor with new TechnicalIndicators service."""
    await ctx.send("The 'indicator_chart' command is temporarily disabled for refactoring.")
    return
    # This command also needs significant refactoring similar to analyze_indicator

@bot.command(name='help_indicators')
async def help_indicators(ctx):
    """Show available indicators and usage. TODO: Update for new TechnicalIndicators service."""
    await ctx.send("Indicator help is temporarily disabled for refactoring. Standard indicators like RSI, MACD, BB, ATR are available via analysis commands when re-enabled.")
    return
    # This needs to list indicators available from bot.indicators (TechnicalIndicators)

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
    signal_data = {
        "symbol": symbol,
        "strategy_code": strategy_code,
        "entry_price": entry_price,
        "tp_price": tp_price,
        "sl_price": sl_price,
        "ratio": ratio,
        "status": status,
        "imminent": imminent,
        "author": str(ctx.author)
    }
    
    embed = await bot.create_signal_embed(signal_data=signal_data, author=str(ctx.author))
    
    target_channel_id = os.getenv('DISCORD_SIGNAL_CHANNEL_ID', ctx.channel.id)
    if not target_channel_id:
        await ctx.send("No signal channel configured. Please set DISCORD_SIGNAL_CHANNEL_ID in environment variables.")
        return
    
    target_channel = bot.get_channel(int(target_channel_id))
    if not target_channel:
        await ctx.send(f"Could not find channel with ID {target_channel_id}")
        return
    
    await target_channel.send(embed=embed)

@bot.command(name='sc01')
async def sc01_signal(ctx, symbol: str, strategy_code: str, entry_price: float, tp_price: float, sl_price: float, ratio: str = "0.0%", status: str = "takeprofit", imminent: int = 1):
    """Send an SC01 trading signal.
    
    Parameters as in //signal command
    """
    signal_data = {
        "symbol": symbol,
        "strategy_code": strategy_code,
        "entry_price": entry_price,
        "tp_price": tp_price,
        "sl_price": sl_price,
        "ratio": ratio,
        "status": status,
        "imminent": imminent,
        "author": str(ctx.author)
    }
    
    embed = await bot.create_signal_embed(signal_data=signal_data, author=str(ctx.author))
    
    await ctx.send(embed=embed)

@bot.command(name='sc_add')
async def add_sc_signal(ctx, symbol: str, strategy_code: str, entry_price: float, tp_price: float, sl_price: float, ratio: str = "0.0%"):
    """Add an SC trading signal to the bot's database.
    
    Parameters similar to //signal command
    """
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    try:
        # Create an SC strategy instance
        sc_strategy = bot.get_strategy('sc_signal', version="SC01", author="Reina")
        
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
        if hasattr(bot, 'store_signal'):
            bot.store_signal(signal)
            await ctx.send(f"Added SC signal for {symbol}-{strategy_code}")
        else:
            signal_data = {
                "symbol": symbol,
                "strategy_code": strategy_code,
                "entry_price": entry_price,
                "tp_price": tp_price,
                "sl_price": sl_price,
                "ratio": ratio,
                "status": "takeprofit",
                "imminent": 1,
                "author": str(ctx.author)
            }
            embed = await bot.create_signal_embed(signal_data=signal_data, author=str(ctx.author))
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
    """Generate a trading signal using the bot's strategy logic. TODO: Review strategy_manager integration."""
    
    if not bot.strategy_manager or not bot.exchange_client:
        await ctx.send("Trading bot components (strategy manager or exchange client) are not initialized.")
        return

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
        await ctx.defer() # Defer response as signal generation can take time

        # Normalize symbol for CCXT if needed by exchange_client.get_price
        ccxt_symbol = symbol.upper()
        if '/' not in ccxt_symbol: # Assuming default like BTC -> BTC/USDT
            # This might need adjustment based on how exchange_client.get_price expects symbols
             ccxt_symbol = f"{ccxt_symbol}/USDT" 
        
        # current_price = trading_bot.client.get_price(symbol) # OLD
        current_price_data = await bot.exchange_client.get_price(ccxt_symbol) # UPDATED - get_price might return more than just a float
        
        current_price = None
        if isinstance(current_price_data, dict) and 'last' in current_price_data:
            current_price = current_price_data['last']
        elif isinstance(current_price_data, (float, int)):
            current_price = current_price_data
            
        if current_price is None:
            await ctx.followup.send(f"Could not fetch current price for {symbol}.")
            clear_command_running(ctx.author.id, ctx.command.name)
            return
            
        # signal_data = trading_bot.generate_signal_data(symbol, strategy_code, risk_reward) # OLD
        # TradingBotCore has self.strategy_manager.generate_signal(symbol, strategy_name, timeframe)
        # We need a timeframe for the new strategy_manager. Using a default or config.
        # The return is a TradingSignal object, not a dict.
        # This part requires careful adaptation. For now, let's assume a placeholder.
        # TODO: Properly integrate with bot.strategy_manager.generate_signal
        
        timeframe_for_signal = bot.config.timeframes.get('primary', '1h') # Example: get primary timeframe from config
        
        logger.info(f"Attempting to generate signal for {symbol} with strategy {strategy_code} on timeframe {timeframe_for_signal} by {ctx.author}")

        # Placeholder for new strategy manager integration
        # actual_signal_object = await bot.strategy_manager.generate_signal(
        # symbol=ccxt_symbol,
        # strategy_name=strategy_code, # Ensure strategy_code matches a strategy known to StrategyManager
        # timeframe=timeframe_for_signal
        # )
        #
        # if not actual_signal_object or actual_signal_object.signal == 'ERROR' or actual_signal_object.signal == 'HOLD':
        # await ctx.followup.send(f"No clear trading signal generated for {symbol} with strategy {strategy_code} at this time.")
        # clear_command_running(ctx.author.id, ctx.command.name)
        # return
        #
        # # Convert TradingSignal object to the dict format expected by create_signal_embed
        # signal_data_dict = {
        # "symbol": actual_signal_object.symbol,
        # "signal_type": actual_signal_object.signal, # e.g. BUY, SELL
        # "entry_price": actual_signal_object.entry_price,
        # "tp_price": actual_signal_object.take_profit,
        # "sl_price": actual_signal_object.stop_loss,
        # "strategy_code": actual_signal_object.strategy_name,
        # "confidence": actual_signal_object.confidence, # Assuming create_signal_embed can handle this
        # "risk_reward_ratio": risk_reward, # Or calculate from TP/SL if available in actual_signal_object
        # "current_price": current_price,
        # "imminent": 1, # Default
        # "status": "takeprofit", # Default
        # "author": str(ctx.author),
        # "ratio": f"{risk_reward:.1f}:1 R:R" # Example formatting
        # }
        # This is a temporary bypass as strategy integration is complex:
        await ctx.followup.send(f"Signal generation for {symbol} using strategy {strategy_code} is under refactoring due to system updates. Please try again later or use manual signal commands.")
        clear_command_running(ctx.author.id, ctx.command.name)
        return

        # embed = create_signal_embed(signal_data=signal_data, author=str(ctx.author)) # OLD
        # embed = await bot.create_signal_embed(signal_data=signal_data_dict, author=str(ctx.author)) # UPDATED
        # await ctx.followup.send(embed=embed)
        
        # Track signal
        track_signal(symbol, strategy_code)
        
        # Create the embed once with the author explicitly set to "Reina"
        embed = await bot.create_signal_embed(
            f"{symbol}-{strategy_code}", 
            "",
            current_price, 
            current_price + (current_price * float(ratio.strip('%')) / 100), 
            current_price - (current_price * float(ratio.strip('%')) / 100), 
            ratio, 
            status, 
            imminent,
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
            await ctx.followup.send(embed=embed)
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
    """Generate multiple market signals for top configured symbols. TODO: Review strategy_manager integration."""
    if not bot.strategy_manager or not bot.exchange_client:
        await ctx.send("Trading bot components are not initialized.")
        return

    await ctx.defer()
    
    # symbols_to_scan = config.trading.symbols[:count] if hasattr(config, 'trading') and hasattr(config.trading, 'symbols') else ["BTC/USDT", "ETH/USDT", "ADA/USDT"][:count]
    # This should use bot.config
    symbols_to_scan = bot.config.symbols[:count] if bot.config and bot.config.symbols else ["BTCUSDT", "ETHUSDT", "ADAUSDT"][:count]

    generated_signals = 0
    timeframe_for_signals = bot.config.timeframes.get('primary', '1h') # Example

    for symbol_config in symbols_to_scan:
        symbol = symbol_config # Assuming symbols in config are directly usable (e.g. "BTCUSDT")
        strategy_code = "SC02" # Default or make configurable

        try:
            logger.info(f"Market Signals: Generating for {symbol} with {strategy_code} on {timeframe_for_signals}")
            # current_price_data = await trading_bot.client.get_price(symbol) # OLD
            current_price_data = await bot.exchange_client.get_price(symbol) # UPDATED
            
            current_price = None
            if isinstance(current_price_data, dict) and 'last' in current_price_data:
                current_price = current_price_data['last']
            elif isinstance(current_price_data, (float, int)):
                current_price = current_price_data

            if current_price is None:
                logger.warning(f"Market Signals: Could not fetch price for {symbol}")
                continue

            # signal_data = trading_bot.generate_signal_data(symbol, strategy_code) # OLD
            # TODO: Integrate with bot.strategy_manager.generate_signal
            # actual_signal_object = await bot.strategy_manager.generate_signal(symbol, strategy_name=strategy_code, timeframe=timeframe_for_signals)
            # if actual_signal_object and actual_signal_object.signal not in ['ERROR', 'HOLD']:
            #     signal_data_dict = { ... convert actual_signal_object to dict ... }
            #     embed = await bot.create_signal_embed(signal_data=signal_data_dict, author=bot.user.name)
            #     await ctx.followup.send(embed=embed)
            #     generated_signals += 1
            # else:
            #     logger.info(f"Market Signals: No clear signal for {symbol} with {strategy_code}")
            # Temporary message for refactoring:
            await ctx.followup.send(f"Market signal generation for {symbol} ({strategy_code}) is part of ongoing refactoring. Skipping for now.", ephemeral=True)

        except Exception as e:
            logger.error(f"Error generating market signal for {symbol}: {e}")
            await ctx.followup.send(f"Error for {symbol}: {e}", ephemeral=True)

    if generated_signals == 0:
        await ctx.followup.send("No clear trading signals generated for the scanned market symbols at this time (or feature under refactoring).")
    else:
        await ctx.followup.send(f"Finished generating {generated_signals} market signals.")
    
    clear_command_running(ctx.author.id, ctx.command.name)

@bot.command(name='live_signal')
@cooldown(1, 10, BucketType.user)  # Increased cooldown to 10 seconds per user
async def live_signal(ctx, channel_id: str = None):
    """Send live trading signal to specified or default channel. TODO: Review strategy_manager integration."""
    if not bot.strategy_manager or not bot.exchange_client:
        await ctx.send("Trading bot components are not initialized.")
        return

    await ctx.defer()
    
    target_channel_id_int = None
    if channel_id:
        try:
            target_channel_id_int = int(channel_id)
        except ValueError:
            await ctx.send("Invalid channel ID format. Please provide a valid integer channel ID.")
            return
    
    target_channel = bot.get_channel(target_channel_id_int)

    if not target_channel:
        await ctx.followup.send(f"Could not find channel with ID {target_channel_id_int if target_channel_id_int else 'default'}. Please provide a valid channel ID.")
        return

    # For demonstration, pick a symbol and strategy
    # symbol = config.trading.symbols[0] if hasattr(config, 'trading') and config.trading.symbols else "BTC/USDT"
    # This should use bot.config
    symbol = bot.config.symbols[0] if bot.config and bot.config.symbols else "BTCUSDT"
    strategy_code = "SC02" # Example
    timeframe_for_signal = bot.config.timeframes.get('primary', '1h') # Example

    try:
        logger.info(f"Live Signal: Generating for {symbol} with {strategy_code} on {timeframe_for_signal} for channel {target_channel.name}")
        # signal_data = trading_bot.generate_signal_data(symbol, strategy_code) # OLD
        # TODO: Integrate with bot.strategy_manager.generate_signal
        # actual_signal_object = await bot.strategy_manager.generate_signal(symbol, strategy_name=strategy_code, timeframe=timeframe_for_signal)
        # if actual_signal_object and actual_signal_object.signal not in ['ERROR', 'HOLD']:
        #     signal_data_dict = { ... convert ... } # Convert TradingSignal object to dict for create_signal_embed
        #     embed = await bot.create_signal_embed(signal_data=signal_data_dict, author=bot.user.name)
        #     await target_channel.send(embed=embed)
        #     await ctx.followup.send(f"Live signal for {symbol} sent to #{target_channel.name}.")
        # else:
        #     await ctx.followup.send(f"No clear live signal generated for {symbol} with {strategy_code} at this time.")
        # Temporary message for refactoring:
        await ctx.followup.send(f"Live signal for {symbol} ({strategy_code}) is under refactoring. Signal not sent to #{target_channel.name}.")

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
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    # Convert percentages to decimals
    if risk_per_trade is not None:
        risk_per_trade = risk_per_trade / 100
    if max_daily_loss is not None:
        max_daily_loss = max_daily_loss / 100
    if trailing_stop is not None:
        trailing_stop = trailing_stop / 100
    
    # Update risk parameters
    bot.update_risk_parameters(
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
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    position_size = bot.calculate_position_size(symbol, stop_loss)
    
    if position_size > 0:
        current_price = bot.get_price(symbol)
        risk_amount = abs(float(current_price) - stop_loss) * position_size
        
        await ctx.send(f"**Position Size Calculation for {symbol}**\n"
                      f"• Entry Price: {entry_price}\n"
                      f"• Stop Loss: {stop_loss}\n"
                      f"• Current Price: {current_price}\n"
                      f"• Position Size: {position_size:.6f} units\n"
                      f"• Risk Amount: ${risk_amount:.2f} USDT\n"
                      f"• Risk per Trade: {bot.max_risk_per_trade * 100:.1f}%")
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
    if not bot.exchange_client:
        await ctx.send("Trading components (exchange client) are not initialized. Check logs for details.")
        return
    
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    await ctx.send(f"Placing advanced buy order for {quantity} {symbol}...")
    
    orders = bot.place_advanced_order(symbol, 'BUY', quantity, take_profit, stop_loss)
    
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

# Legacy dual_macd_rsi command - this has been moved to analysis_commands.py cog
# This command is now maintained there instead.

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
    """Advanced position sizing based on volatility and account risk. TODO: Refactor with RiskManager."""
    if not bot.exchange_client or not bot.risk_manager or not bot.indicators:
        await ctx.send("Required trading components (client, risk manager, or indicators) not available.")
        return

    await ctx.defer()
    
    try:
        target_symbol = symbol.upper().replace('/', '')
        # Fetch current price and historical data for ATR
        # current_price_data = await trading_bot.client.get_price(target_symbol) # OLD
        current_price_data = await bot.exchange_client.get_price(target_symbol) # UPDATED
        
        current_price = None
        if isinstance(current_price_data, dict) and 'last' in current_price_data:
            current_price = current_price_data['last']
        elif isinstance(current_price_data, (float, int)):
            current_price = current_price_data

        if current_price is None:
            await ctx.followup.send(f"Could not fetch current price for {target_symbol}.")
            return

        # ohlcv = await trading_bot.client.fetch_ohlcv(target_symbol, timeframe='1h', limit=100) # OLD
        ohlcv = await bot.exchange_client.fetch_ohlcv(target_symbol, timeframe='1h', limit=100) # UPDATED (timeframe can be parameter)
        if not ohlcv:
            await ctx.followup.send(f"Could not fetch OHLCV data for {target_symbol} to calculate volatility.")
            return
            
        import pandas as pd # Ensure pandas is imported if not already at top level of file where this is run
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # atr_result = trading_bot.indicators.calculate_atr(df) # OLD - Assuming indicators was part of old trading_bot
        atr_result = bot.indicators.calculate_atr(df) # UPDATED - bot.indicators is TechnicalIndicators
        
        if atr_result.signal == 'ERROR' or not atr_result.metadata or 'current_value' not in atr_result.metadata:
            await ctx.followup.send(f"Could not calculate ATR for {target_symbol}.")
            return
        
        atr_value = atr_result.metadata['current_value']
        
        # position_size = trading_bot.risk_manager.calculate_dynamic_position_size( # OLD
        # account_balance=account_balance,
        # risk_percent=risk_percent / 100, # Convert to decimal
        # entry_price=current_price,
        # volatility=atr_value, # Use ATR as measure of volatility
        # price_per_pip_or_tick=0.01 # Example, might need adjustment per symbol
        # )
        # Using RiskManager's method directly. The old one might have been on TradingBot.
        # This assumes RiskManager has such a method. src/trading/risk_manager.py has DynamicRiskManager
        # DynamicRiskManager does not have calculate_dynamic_position_size. It has calculate_position_size based on fixed % or kelly.
        # This needs to be mapped to available RiskManager methods.
        # For now, using a simplified calculation based on fixed risk:
        stop_loss_distance_atr_multiples = 2 # Example: SL is 2 * ATR away
        stop_loss_price = current_price - (atr_value * stop_loss_distance_atr_multiples) # For a long
        
        if stop_loss_price >= current_price : # Should not happen for long
             await ctx.followup.send(f"Calculated stop loss ({stop_loss_price}) is not valid against entry ({current_price}). Cannot calculate position size.")
             return

        # position_size_coins = bot.risk_manager.calculate_position_size( # Needs to exist on RiskManager
        # account_balance=account_balance,
        # risk_per_trade_percent=risk_percent / 100,
        # entry_price=current_price,
        # stop_loss_price=stop_loss_price,
        # symbol=target_symbol
        # )
        
        # Simplified calculation if direct method is not available:
        risk_amount_per_trade = account_balance * (risk_percent / 100.0)
        amount_to_risk_per_coin = current_price - stop_loss_price
        if amount_to_risk_per_coin <= 0:
            position_size_coins = 0
            await ctx.followup.send(f"Risk per coin is zero or negative. Cannot determine position size based on ATR stop loss.")
        else:
            position_size_coins = risk_amount_per_trade / amount_to_risk_per_coin

        embed = discord.Embed(title=f"Advanced Position Size for {target_symbol}", color=0x1E90FF)
        embed.add_field(name="Account Balance", value=f"${account_balance:.2f}", inline=True)
        embed.add_field(name="Risk Percentage", value=f"{risk_percent:.2f}%", inline=True)
        embed.add_field(name="Risk Amount", value=f"${risk_amount_per_trade:.2f}", inline=True)
        embed.add_field(name="Current Price", value=f"${current_price:.2f}", inline=True)
        embed.add_field(name="Entry Price", value=f"${current_price:.2f}", inline=True)
        embed.add_field(name="Stop Loss", value=f"${stop_loss_price:.2f}", inline=True)
        embed.add_field(name="Take Profit", value=f"${current_price + (current_price * float(ratio.strip('%')) / 100):.2f}", inline=True)
        embed.add_field(name="Risk/Reward Ratio", value=f"{risk_percent:.2f}:1", inline=True)
        embed.add_field(name="Position Size", value=f"{position_size_coins:.6f} {symbol.split('/')[0]}", inline=False)
        embed.add_field(name="Position Value", value=f"${position_size_coins * current_price:.2f}", inline=True)
        embed.add_field(name="Signal", value=f"{status} {ratio}", inline=True)
        embed.add_field(name="Imminent Entry", value=f"{imminent}", inline=True)
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

@bot.command(name='debug_price')
async def debug_price_responses(ctx, symbol: str = "BTC"):
    """Test and debug price responses from exchange client."""
    if not bot.exchange_client:
        await ctx.send("Exchange client not initialized.")
        return

    target_symbol = symbol.upper()
    if "/" not in target_symbol:
        target_symbol += "/USDT" # Assuming default pair

    await ctx.send(f"Fetching price for {target_symbol} using `bot.exchange_client.get_price()`...")
    try:
        # price_data = await trading_bot.client.get_price(target_symbol) # OLD
        price_data = await bot.exchange_client.get_price(target_symbol) # UPDATED
        await ctx.send(f"Raw response from `get_price({target_symbol})`:\n```json\n{json.dumps(price_data, indent=2)}\n```")
    except Exception as e:
        await ctx.send(f"Error calling `get_price({target_symbol})`: {e}")

    await ctx.send(f"Fetching ticker for {target_symbol} using `bot.exchange_client.fetch_ticker()`...")
    try:
        # ticker_data = await trading_bot.client.fetch_ticker(target_symbol) # OLD
        ticker_data = await bot.exchange_client.fetch_ticker(target_symbol) # UPDATED
        await ctx.send(f"Raw response from `fetch_ticker({target_symbol})`:\n```json\n{json.dumps(ticker_data, indent=2)}\n```")
    except Exception as e:
        logger.error(f"Error calling `fetch_ticker({target_symbol})`: {e}")
        await ctx.send(f"❌ Error running debug: {str(e)}")

def run_bot():
    """Run the Discord bot"""
    if token:
        try:
            # bot.run(token) # OLD - TradingBotCore might have its own run method or expect this.
            # TradingBotCore is a commands.Bot, so bot.run(token) is correct.
            # The create_bot() function returns an instance of TradingBotCore.
            bot.run(token)
        except discord.errors.LoginFailure:
            logger.error("Failed to log in: Improper token has been passed.")

if __name__ == "__main__":
    run_bot()    