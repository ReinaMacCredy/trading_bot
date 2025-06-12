"""
Enhanced Discord Trading Bot Core
Implements professional Discord bot architecture with cogs and commands
"""

import discord
from discord.ext import commands, tasks
import asyncio
import logging
from typing import Dict, List, Optional
import os
from datetime import datetime, timedelta
import traceback
import pandas as pd

from src.config.config_loader import get_config
from src.trading.clients.exchange_client import ExchangeClient
from src.trading.strategies import StrategyManager
from src.trading.indicators import TechnicalIndicators, IndicatorFactory
from src.trading.core.risk_manager import DynamicRiskManager
from src.trading.core.order_history import OrderHistory

logger = logging.getLogger(__name__)

class TradingBotCore(commands.Bot):
    """
    Enhanced Discord Trading Bot with professional architecture
    """
    
    def __init__(self):
        # Load configuration
        self.config = get_config()
        
        # Setup bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        # Initialize bot
        super().__init__(
            command_prefix=self.config.discord.command_prefix,
            help_command=None,  # We'll implement our own
            intents=intents,
            case_insensitive=True
        )
        
        # Initialize trading components
        self.exchange_client = None
        self.strategy_manager = None
        self.indicators = None
        self.risk_manager = None
        
        # Bot state
        self._is_ready = False
        self.start_time = None
        self.last_heartbeat = None
        self.active_signals = {}
        self.monitoring_enabled = False
        
        # Performance tracking
        self.command_count = 0
        self.error_count = 0
        self.uptime_start = None
        self.command_usage: Dict[str, datetime] = {}
        self.order_history = OrderHistory()
        
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.logging_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('discord_bot.log'),
                logging.StreamHandler()
            ]
        )
        
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        logger.info("Setting up Discord Trading Bot...")
        
        try:
            # Initialize trading components
            await self._initialize_trading_components()
            
            # Load cogs
            await self._load_cogs()
            
            # Initialize command handler
            from src.bot.commands.command_handler import setup_command_handler
            self.command_handler = setup_command_handler(self)
            logger.info("Command handler initialized")
            
            # Start background tasks
            self._start_background_tasks()
            
            logger.info("Bot setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during bot setup: {e}")
            logger.error(traceback.format_exc())
            
    async def _initialize_trading_components(self):
        """Initialize trading-related components"""
        try:
            # Initialize exchange client
            self.exchange_client = ExchangeClient(
                exchange_name=self.config.exchange.name,
                sandbox=self.config.exchange.sandbox,
                config=self.config,
                order_history=self.order_history
            )
            
            # Test exchange connection
            connection_ok = await self.exchange_client.test_connection()
            if connection_ok:
                logger.info("Exchange connection established successfully")
            else:
                logger.warning("Exchange connection test failed - running in demo mode")
            
            # Initialize strategy manager
            self.strategy_manager = StrategyManager(
                config=self.config,
                exchange_client=self.exchange_client
            )
            
            # Initialize indicators
            self.indicators = TechnicalIndicators(config=self.config)
            
            # Initialize risk manager
            risk_trading_settings = self.config.trading
            risk_indicator_settings = self.config.indicators
            
            self.risk_manager = DynamicRiskManager(
                max_risk_per_trade=risk_trading_settings.max_risk_per_trade,
                max_daily_risk=risk_trading_settings.max_daily_loss,
                max_open_trades=risk_trading_settings.max_positions,
                atr_period=risk_indicator_settings.atr_period
            )
            
            logger.info("Trading components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing trading components: {e}")
            logger.error(traceback.format_exc())
            raise
            
    async def _load_cogs(self):
        """Load available cogs"""
        try:
            cog_modules = [
                "src.bot.cogs.slash_commands",
                "src.bot.cogs.trading_commands",
                "src.bot.cogs.strategy_commands",
                "src.bot.cogs.analysis_commands",
                "src.bot.cogs.portfolio_commands",
                "src.bot.cogs.admin_commands",
                "src.bot.cogs.help_commands"
            ]
            
            # Import the command resolver once at the start
            try:
                from src.bot.commands.command_resolver import CONFLICTING_COMMANDS
                logger.info(f"Command conflict resolution enabled. {len(CONFLICTING_COMMANDS)} potential conflicts identified.")
            except ImportError:
                logger.warning("Command resolver module not available.")
            
            # Track which cogs were successfully loaded
            loaded_cogs = []
            
            for cog in cog_modules:
                try:
                    await self.load_extension(cog)
                    logger.info(f"Loaded cog: {cog}")
                    loaded_cogs.append(cog)
                except discord.errors.ClientException as e:
                    logger.error(f"Failed to load cog {cog}: {e}")
                    if "already an existing command" in str(e):
                        # Command conflict - log this but continue with other cogs
                        conflicting_command = str(e).split('The command ')[1].split(' is already')[0]
                        logger.warning(f"Command conflict detected: '{conflicting_command}' in {cog}")
                    else:
                        # Other client exception - raise it
                        raise
                except Exception as e:
                    logger.error(f"Error loading cog {cog}: {e}")
                    raise
                    
            if loaded_cogs:
                logger.info(f"Successfully loaded {len(loaded_cogs)} cog(s): {', '.join(loaded_cogs)}")
                
                # Attempt to resolve any command conflicts
                try:
                    from src.bot.commands.command_resolver import resolve_command_conflicts
                    resolve_command_conflicts(self)
                except ImportError:
                    pass
            else:
                logger.warning("No cogs were loaded successfully.")
                    
            # Sync slash commands
            try:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} slash commands")
            except Exception as e:
                logger.error(f"Failed to sync slash commands: {e}")
        except Exception as e:
            logger.error(f"Error loading cogs: {e}")
            logger.error(traceback.format_exc())
                
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        if not self.heartbeat_task.is_running():
            self.heartbeat_task.start()
            
        if not self.market_monitor_task.is_running() and self.config.monitoring.enable_alerts:
            self.market_monitor_task.start()
            
        logger.info("Background tasks started")
        
    async def on_ready(self):
        """Called when bot is ready"""
        self._is_ready = True
        self.start_time = datetime.now()
        self.uptime_start = datetime.now()
        self.last_heartbeat = datetime.now()
        
        logger.info(f"Bot is ready! Logged in as {self.user}")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"📈 Markets | {self.config.discord.command_prefix}help"
        )
        await self.change_presence(activity=activity)
        
    async def on_command(self, ctx):
        """Called before every command"""
        self.command_count += 1
        command_name = ctx.command.name if ctx.command else 'unknown'
        self.command_usage[command_name] = datetime.now()
        logger.info(f"Command executed: {ctx.command} by {ctx.author}")
        
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        self.error_count += 1
        
        # Command not found
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore silently
            
        # Command on cooldown
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"Try again in {error.retry_after:.1f} seconds",
                color=0xff9900
            )
            await ctx.send(embed=embed, delete_after=10)
            
        # Missing permissions
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You don't have permission to use this command",
                color=0xff0000
            )
            await ctx.send(embed=embed, delete_after=10)
            
        # Missing required argument
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Argument",
                description=f"Missing required argument: `{error.param.name}`",
                color=0xff0000
            )
            embed.add_field(
                name="Usage",
                value=f"`{self.config.discord.command_prefix}{ctx.command} {ctx.command.signature}`",
                inline=False
            )
            await ctx.send(embed=embed, delete_after=15)
            
        # Bad argument
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Argument",
                description=str(error),
                color=0xff0000
            )
            await ctx.send(embed=embed, delete_after=10)
            
        # Unknown error
        else:
            logger.error(f"Unhandled command error: {error}")
            logger.error(traceback.format_exc())
            
            embed = discord.Embed(
                title="❌ An Error Occurred",
                description="An unexpected error occurred while processing your command.",
                color=0xff0000
            )
            await ctx.send(embed=embed, delete_after=10)
            
    @tasks.loop(minutes=1)
    async def heartbeat_task(self):
        """Heartbeat task to monitor bot health"""
        try:
            self.last_heartbeat = datetime.now()
            
            # Log heartbeat periodically
            if self.last_heartbeat.minute % 5 == 0:
                uptime = self.last_heartbeat - self.uptime_start if self.uptime_start else timedelta(0)
                logger.debug(f"Bot heartbeat - Uptime: {uptime}, Commands: {self.command_count}")
                
        except Exception as e:
            logger.error(f"Error in heartbeat task: {e}")
            
    @tasks.loop(minutes=5)
    async def market_monitor_task(self):
        """Monitor market conditions and send alerts"""
        if not self.monitoring_enabled:
            return
            
        try:
            # Get market data for configured symbols
            for symbol in self.config.symbols[:3]:  # Monitor top 3 symbols
                ticker = await self.exchange_client.fetch_ticker(symbol)
                if not ticker:
                    continue
                    
                # Check for significant price movements
                await self._check_price_alerts(symbol, ticker)
                
        except Exception as e:
            logger.error(f"Error in market monitor task: {e}")
            
    async def _check_price_alerts(self, symbol: str, ticker: dict):
        """Check for price alerts and significant movements"""
        try:
            current_price = ticker['last']
            price_change_24h = ticker.get('percentage', 0)
            
            # Alert for significant movements (>5%)
            if abs(price_change_24h) > 5:
                embed = discord.Embed(
                    title="🚨 Significant Price Movement",
                    color=0x00ff00 if price_change_24h > 0 else 0xff0000
                )
                embed.add_field(name="Symbol", value=symbol, inline=True)
                embed.add_field(name="Price", value=f"${current_price:,.2f}", inline=True)
                embed.add_field(name="24h Change", value=f"{price_change_24h:+.2f}%", inline=True)
                embed.timestamp = datetime.now()
                
                # Send to alerts channel
                for guild in self.guilds:
                    alerts_channel = discord.utils.get(
                        guild.channels,
                        name=self.config.discord.alerts_channel
                    )
                    if alerts_channel:
                        await alerts_channel.send(embed=embed)
                        
        except Exception as e:
            logger.error(f"Error checking price alerts: {e}")
            
    async def create_signal_embed(self, signal_data: dict, author: str = "Trading Bot") -> discord.Embed:
        """Create a professional trading signal embed"""
        try:
            # Determine embed color based on signal
            signal_type = signal_data.get('signal', 'HOLD').upper()
            if signal_type == 'BUY':
                color = 0x00ff00  # Green
                emoji = "🟢"
            elif signal_type == 'SELL':
                color = 0xff0000  # Red
                emoji = "🔴"
            else:
                color = 0xffff00  # Yellow
                emoji = "🟡"
                
            # Create embed
            embed = discord.Embed(
                title=f"{emoji} {signal_data.get('symbol', 'Unknown')} Trading Signal",
                color=color,
                timestamp=datetime.now()
            )
            
            # Add signal details
            embed.add_field(
                name="📊 Signal Type",
                value=f"**{signal_type}**",
                inline=True
            )
            
            embed.add_field(
                name="💰 Entry Price",
                value=f"${signal_data.get('entry_price', 0):,.4f}",
                inline=True
            )
            
            embed.add_field(
                name="📈 Confidence",
                value=f"{signal_data.get('confidence', 0)*100:.1f}%",
                inline=True
            )
            
            if signal_data.get('take_profit'):
                embed.add_field(
                    name="🎯 Take Profit",
                    value=f"${signal_data.get('take_profit'):,.4f}",
                    inline=True
                )
                
            if signal_data.get('stop_loss'):
                embed.add_field(
                    name="🛡️ Stop Loss",
                    value=f"${signal_data.get('stop_loss'):,.4f}",
                    inline=True
                )
                
            if signal_data.get('strategy_name'):
                embed.add_field(
                    name="⚙️ Strategy",
                    value=signal_data.get('strategy_name'),
                    inline=True
                )
                
            # Add footer
            embed.set_footer(
                text=f"By {author} • Timeframe: {signal_data.get('timeframe', '1h')}",
                icon_url=self.user.avatar.url if self.user.avatar else None
            )
            
            return embed
            
        except Exception as e:
            logger.error(f"Error creating signal embed: {e}")
            # Return basic embed
            return discord.Embed(
                title="❌ Signal Error",
                description="Failed to create signal embed",
                color=0xff0000
            )
            
    async def send_signal_to_channel(self, signal_data: dict, channel_name: str = None):
        """Send trading signal to specified channel"""
        try:
            channel_name = channel_name or self.config.discord.signals_channel
            embed = await self.create_signal_embed(signal_data)
            
            for guild in self.guilds:
                channel = discord.utils.get(guild.channels, name=channel_name)
                if channel:
                    await channel.send(embed=embed)
                    logger.info(f"Signal sent to {guild.name}#{channel_name}")
                    
        except Exception as e:
            logger.error(f"Error sending signal to channel: {e}")
            
    def get_bot_stats(self) -> dict:
        """Get bot statistics"""
        uptime = datetime.now() - self.uptime_start if self.uptime_start else timedelta(0)
        
        return {
            'uptime': str(uptime).split('.')[0],
            'guilds': len(self.guilds),
            'users': sum(guild.member_count for guild in self.guilds),
            'commands_executed': self.command_count,
            'errors': self.error_count,
            'last_heartbeat': self.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S') if self.last_heartbeat else 'N/A',
            'exchange_connected': self.exchange_client is not None,
            'monitoring_enabled': self.monitoring_enabled
        }

    def get_command_status(self) -> tuple[list[str], list[str]]:
        """Return lists of active and inactive commands"""
        all_commands = [cmd.name for cmd in self.commands]
        active = list(self.command_usage.keys())
        inactive = [c for c in all_commands if c not in active]
        return active, inactive
        
    async def sync_slash_commands(self, guild_id: int = None):
        """Manually sync slash commands"""
        try:
            if guild_id:
                # Sync to specific guild (faster)
                guild = discord.Object(id=guild_id)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} slash commands to guild {guild_id}")
            else:
                # Global sync (takes up to 1 hour)
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} slash commands globally")
            return True
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
            return False

    async def shutdown(self):
        """Gracefully shutdown the bot"""
        logger.info("Shutting down bot...")
        
        # Cancel background tasks
        if self.heartbeat_task.is_running():
            self.heartbeat_task.cancel()
            
        if self.market_monitor_task.is_running():
            self.market_monitor_task.cancel()
            
        # Close exchange client
        if self.exchange_client:
            # Any cleanup needed for exchange client
            pass
            
        # Close bot
        await self.close()
        logger.info("Bot shutdown complete")

    async def generate_chart(self, symbol: str, interval: str = '1d', limit: int = 30):
        """Generate a price chart for a symbol"""
        try:
            logger.info(f"Generating chart for {symbol} on {interval} timeframe (limit: {limit})")
            
            # This is a placeholder implementation that returns None
            # In a real implementation, this would fetch data and generate a chart
            
            # Demo data - this would be replaced with actual chart generation
            import matplotlib.pyplot as plt
            import numpy as np
            import io
            
            # Create a simple chart (this is a placeholder)
            plt.figure(figsize=(10, 6))
            
            # Generate some random price data as placeholder
            x = np.arange(limit)
            base_price = 100 + (hash(symbol) % 900)  # Random starting price based on symbol name
            volatility = 0.01 + (hash(interval) % 10) * 0.01  # Random volatility based on interval
            
            # Generate a somewhat realistic price movement
            y = [base_price]
            for i in range(1, limit):
                price_change = y[-1] * np.random.normal(0, volatility)
                y.append(y[-1] + price_change)
            
            plt.plot(x, y, linewidth=2)
            plt.title(f"{symbol} Price Chart ({interval})")
            plt.xlabel("Time")
            plt.ylabel("Price (USD)")
            plt.grid(True)
            
            # Save chart to a buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            
            return buf
            
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            return None
            
    async def generate_strategy_chart(self, strategy: str, symbol: str, interval: str = '1d', limit: int = 30):
        """Generate a strategy chart with indicators"""
        try:
            logger.info(f"Generating strategy chart for {symbol} with {strategy} strategy on {interval} timeframe")
            
            # This is similar to generate_chart but would add strategy indicators
            # For now, we'll use the same implementation with a different title
            
            import matplotlib.pyplot as plt
            import numpy as np
            import io
            
            plt.figure(figsize=(10, 6))
            
            # Generate some random price data as placeholder
            x = np.arange(limit)
            base_price = 100 + (hash(symbol) % 900)
            volatility = 0.01 + (hash(interval) % 10) * 0.01
            
            # Generate a somewhat realistic price movement
            y = [base_price]
            for i in range(1, limit):
                price_change = y[-1] * np.random.normal(0, volatility)
                y.append(y[-1] + price_change)
            
            # Plot main price chart
            plt.plot(x, y, linewidth=2, label="Price")
            
            # Add a simple moving average as demo indicator
            window = 5
            if limit > window:
                sma = np.convolve(y, np.ones(window)/window, mode='valid')
                plt.plot(range(window-1, limit), sma, linewidth=1.5, label=f"SMA-{window}")
            
            plt.title(f"{symbol} with {strategy} Strategy ({interval})")
            plt.xlabel("Time")
            plt.ylabel("Price (USD)")
            plt.grid(True)
            plt.legend()
            
            # Save chart to a buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            
            return buf
            
        except Exception as e:
            logger.error(f"Error generating strategy chart: {e}")
            return None

    async def get_market_data(self, symbol, interval, limit=100, exchange=None):
        logger.info(f"CORE_GM_DATA_ENTER: Attempting for {symbol}/{interval}. Bot instance ID: {id(self)}")
        """
        Get historical market data for a symbol
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            interval: Time interval (e.g., 1h, 4h, 1d)
            limit: Number of candles to fetch
            exchange: Optional exchange name (defaults to configured exchange)
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            logger.info(f"Fetching market data for {symbol} on {interval} timeframe")
            
            # If exchange client isn't initialized, return None
            if not self.exchange_client:
                logger.error("Exchange client not initialized")
                return None
                
            # Use exchange client to fetch OHLCV data
            df = await self.exchange_client.fetch_ohlcv(
                symbol=symbol,
                timeframe=interval,
                limit=limit
            )
            
            if df is None or len(df) == 0:
                logger.error(f"Failed to fetch market data for {symbol}")
                return None
                
            # Reset index to have timestamp as a column rather than index
            # This is to match the format expected by the dual_macd_rsi command
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
            logger.error(f"CORE_GM_DATA_ERROR: Error for {symbol}/{interval}: {str(e)}. Bot instance ID: {id(self)}")
            logger.error(traceback.format_exc())
            return None
        finally:
            logger.info(f"CORE_GM_DATA_EXIT: Exiting for {symbol}/{interval}. Bot instance ID: {id(self)}")
            
    async def get_price(self, symbol, exchange=None):
        """
        Get current price for a symbol
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            exchange: Optional exchange name
            
        Returns:
            Current price as float or None if error
        """
        try:
            # If exchange client isn't initialized, return None
            if not self.exchange_client:
                logger.error("Exchange client not initialized")
                return None
                
            # Use exchange client to fetch ticker
            ticker = await self.exchange_client.fetch_ticker(symbol)
            
            if ticker and 'last' in ticker:
                return float(ticker['last'])
            else:
                logger.error(f"Failed to fetch price for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None

    # Add compatibility method for standard discord.py is_ready() method
    def is_ready(self) -> bool:
        """Return the is_ready property for compatibility with standard discord.py Bot"""
        return self._is_ready

# Factory function to create and configure bot
def create_bot() -> TradingBotCore:
    """Create and configure the trading bot"""
    bot = TradingBotCore()
    return bot 