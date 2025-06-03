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

from src.config.config_loader import get_config
from src.trading.exchange_client import ExchangeClient
from src.trading.strategies import StrategyManager
from src.trading.indicators import TechnicalIndicators
from src.trading.risk_manager import RiskManager

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
        self.is_ready = False
        self.start_time = None
        self.last_heartbeat = None
        self.active_signals = {}
        self.monitoring_enabled = False
        
        # Performance tracking
        self.command_count = 0
        self.error_count = 0
        self.uptime_start = None
        
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.monitoring.log_level),
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
                config=self.config
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
            self.risk_manager = RiskManager(
                config=self.config,
                exchange_client=self.exchange_client
            )
            
            logger.info("Trading components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing trading components: {e}")
            raise
            
    async def _load_cogs(self):
        """Load all bot cogs"""
        cogs_to_load = [
            'src.bot.cogs.trading_commands',
            'src.bot.cogs.strategy_commands', 
            'src.bot.cogs.analysis_commands',
            'src.bot.cogs.portfolio_commands',
            'src.bot.cogs.admin_commands',
            'src.bot.cogs.help_commands'
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")
                
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        if not self.heartbeat_task.is_running():
            self.heartbeat_task.start()
            
        if not self.market_monitor_task.is_running() and self.config.monitoring.enable_alerts:
            self.market_monitor_task.start()
            
        logger.info("Background tasks started")
        
    async def on_ready(self):
        """Called when bot is ready"""
        self.is_ready = True
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

# Factory function to create and configure bot
def create_bot() -> TradingBotCore:
    """Create and configure the trading bot"""
    bot = TradingBotCore()
    return bot 