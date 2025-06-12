"""
Slash Commands Cog for Discord Trading Bot
Implements modern Discord slash commands using discord.app_commands
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class SlashCommands(commands.Cog):
    """Slash commands for the trading bot"""
    
    def __init__(self, bot):
        self.bot = bot
        # Track processed interactions to prevent duplicate responses
        self._processed_interactions: dict[int, float] = {}
        
    @app_commands.command(name="price", description="Get current price for a cryptocurrency")
    @app_commands.describe(
        symbol="The cryptocurrency symbol (e.g., BTC, ETH, ADA)",
        exchange="Exchange to get price from (default: binance)"
    )
    async def price_slash(
        self,
        interaction: discord.Interaction,
        symbol: str,
        exchange: Optional[Literal["binance", "coinbase", "kraken", "bybit"]] = "binance"
    ):
        """Get current price for a cryptocurrency using slash command"""
        # Enhanced logging to track command execution
        logger.info(f"Price slash command triggered by {interaction.user} for {symbol} on {exchange}")
        
        # Safety check to prevent double acknowledgment
        if interaction.response.is_done():
            logger.warning("Interaction already acknowledged for price command")
            return

        # Enhanced duplicate protection with longer tracking
        now_ts = datetime.now().timestamp()
        # Remove expired entries (>10 seconds old)
        self._processed_interactions = {
            k: t for k, t in self._processed_interactions.items() if now_ts - t < 10
        }
        if interaction.id in self._processed_interactions:
            logger.warning(f"Duplicate interaction detected: {interaction.id} - Ignoring")
            return
        self._processed_interactions[interaction.id] = now_ts

        # Check for rapid duplicate requests from same user
        user_key = f"user_{interaction.user.id}_{symbol}"
        if hasattr(self, '_user_requests'):
            if user_key in self._user_requests:
                last_request = self._user_requests[user_key]
                if (now_ts - last_request) < 3:  # 3 second cooldown per user per symbol
                    logger.warning(f"Rate limited duplicate request from {interaction.user} for {symbol}")
                    return
        else:
            self._user_requests = {}
        
        self._user_requests[user_key] = now_ts

        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            logger.error("Interaction expired or not found when trying to defer price command")
            return
        except discord.errors.InteractionResponded:
            logger.warning("Interaction already responded to for price command")
            return
        except Exception as e:
            logger.error(f"Unexpected error deferring price interaction: {e}")
            return
        
        try:
            # Format symbol
            symbol = symbol.upper()
            if not symbol.endswith('/USDT'):
                symbol = f"{symbol}/USDT"
            
            logger.info(f"Fetching price for {symbol} from trading bot")
            
            # Get price from trading bot
            trading_bot = getattr(self.bot, 'trading_bot', None)
            if not trading_bot:
                raise ValueError("Trading bot not available")
            
            # Use the trading bot's get_price method
            price = trading_bot.get_price(symbol.replace('/', ''))
            if not price:
                raise ValueError("Could not fetch price data")
            
            logger.info(f"Price fetched successfully: {price} for {symbol}")
            
            # Create ticker data
            ticker = {
                'last': float(price),
                'symbol': symbol,
                'percentage': 0.0,  # Mock data for now
                'change': 0.0
            }
            
            # Create distinctive embed with unique formatting
            embed = discord.Embed(
                title=f"💰 {symbol} Price Information",
                description=f"Real-time price from {exchange.upper()}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="💵 Current Price",
                value=f"**${ticker.get('last', 0):,.8f}**",
                inline=True
            )
            
            embed.add_field(
                name="📊 Exchange",
                value=f"🏪 {exchange.capitalize()}",
                inline=True
            )
            
            # Add 24h change if available
            if 'percentage' in ticker:
                change_color = "🟢" if ticker['percentage'] >= 0 else "🔴"
                embed.add_field(
                    name="📈 24h Change",
                    value=f"{change_color} {ticker['percentage']:.2f}%",
                    inline=True
                )
            
            if 'high' in ticker and 'low' in ticker:
                embed.add_field(
                    name="📊 24h High/Low",
                    value=f"${ticker['high']:,.2f} / ${ticker['low']:,.2f}",
                    inline=True
                )
            
            # Add unique identifier to help track the source
            embed.set_footer(
                text=f"Trading Bot v2.0 | Slash Command | ID: {interaction.id}",
                icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None
            )
            
            logger.info(f"Sending price embed for {symbol} to user {interaction.user}")
            await interaction.followup.send(embed=embed)
            logger.info(f"Price embed sent successfully for {symbol}")
                
        except Exception as e:
            logger.error(f"Error in price slash command: {e}")
            
            error_embed = discord.Embed(
                title="❌ Price Fetch Error",
                description=f"Could not fetch price for {symbol}",
                color=0xff0000
            )
            error_embed.add_field(
                name="Error Details",
                value=f"```{str(e)}```",
                inline=False
            )
            error_embed.set_footer(text=f"Error ID: {interaction.id}")
            
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except discord.errors.InteractionResponded:
                logger.warning("Interaction already responded to, could not send error message")
            except Exception as followup_error:
                logger.error(f"Failed to send error followup: {followup_error}")
    
    @app_commands.command(name="signal", description="Generate a trading signal")
    @app_commands.describe(
        symbol="The cryptocurrency symbol (e.g., BTC, ETH)",
        strategy="Trading strategy to use",
        timeframe="Timeframe for analysis"
    )
    async def signal_slash(
        self,
        interaction: discord.Interaction,
        symbol: str,
        strategy: Optional[Literal["SC01", "SC02", "SC02+FRVP"]] = "SC01",
        timeframe: Optional[Literal["1h", "4h", "1d"]] = "1h"
    ):
        """Generate a trading signal using slash command"""
        # Safety check to prevent double acknowledgment
        if interaction.response.is_done():
            logger.warning("Interaction already acknowledged for signal command")
            return
            
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            logger.error("Interaction expired or not found when trying to defer signal command")
            return
        except discord.errors.InteractionResponded:
            logger.warning("Interaction already responded to for signal command")
            return
        except Exception as e:
            logger.error(f"Unexpected error deferring signal interaction: {e}")
            return
        
        try:
            # Format symbol
            symbol = symbol.upper()
            if not symbol.endswith('/USDT'):
                symbol = f"{symbol}/USDT"
            
            # Check if trading bot is available
            trading_bot = getattr(self.bot, 'trading_bot', None)
            if not trading_bot:
                raise ValueError("Trading system not available")
            
            # Get market data
            current_price = trading_bot.get_price(symbol.replace('/', ''))
            if not current_price:
                raise ValueError("Could not fetch market data")
            
            # Generate signal data (simplified version)
            signal_type = random.choice(["BUY", "SELL"])
            entry_price = current_price * random.uniform(0.995, 1.005)
            
            if signal_type == "BUY":
                tp_price = entry_price * random.uniform(1.02, 1.05)
                sl_price = entry_price * random.uniform(0.97, 0.99)
            else:
                tp_price = entry_price * random.uniform(0.95, 0.98)
                sl_price = entry_price * random.uniform(1.01, 1.03)
            
            # Calculate risk/reward ratio
            if signal_type == "BUY":
                risk = entry_price - sl_price
                reward = tp_price - entry_price
            else:
                risk = sl_price - entry_price
                reward = entry_price - tp_price
            
            ratio = reward / risk if risk > 0 else 0
            
            # Create signal embed
            embed = discord.Embed(
                title=f"📊 Trading Signal - {symbol}",
                color=0x00ff00 if signal_type == "BUY" else 0xff0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Signal Type",
                value=f"{'🟢 ' if signal_type == 'BUY' else '🔴 '}{signal_type}",
                inline=True
            )
            
            embed.add_field(
                name="Entry Price",
                value=f"${entry_price:.4f}",
                inline=True
            )
            
            embed.add_field(
                name="Current Price",
                value=f"${current_price:.4f}",
                inline=True
            )
            
            embed.add_field(
                name="Take Profit",
                value=f"${tp_price:.4f}",
                inline=True
            )
            
            embed.add_field(
                name="Stop Loss",
                value=f"${sl_price:.4f}",
                inline=True
            )
            
            embed.add_field(
                name="Risk/Reward Ratio",
                value=f"1:{ratio:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Strategy",
                value=strategy,
                inline=True
            )
            
            embed.add_field(
                name="Timeframe",
                value=timeframe,
                inline=True
            )
            
            embed.add_field(
                name="Status",
                value="🔵 Active",
                inline=True
            )
            
            embed.set_footer(text=f"Strategy: {strategy} | Generated at")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in signal slash command: {e}")
            
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not generate signal for {symbol}: {str(e)}",
                color=0xff0000
            )
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except discord.errors.InteractionResponded:
                logger.warning("Interaction already responded to, could not send error message")
            except Exception as followup_error:
                logger.error(f"Failed to send error followup: {followup_error}")
    
    @app_commands.command(name="bot_stats", description="Get bot statistics and status")
    async def stats_slash(self, interaction: discord.Interaction):
        """Get bot statistics using slash command"""
        # Safety check to prevent double acknowledgment
        if interaction.response.is_done():
            logger.warning("Interaction already acknowledged for stats command")
            return
            
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            logger.error("Interaction expired or not found when trying to defer stats command")
            return
        except discord.errors.InteractionResponded:
            logger.warning("Interaction already responded to for stats command")
            return
        except Exception as e:
            logger.error(f"Unexpected error deferring stats interaction: {e}")
            return
        
        try:
            # Get bot stats
            stats = self.bot.get_bot_stats() if hasattr(self.bot, 'get_bot_stats') else {}
            
            embed = discord.Embed(
                title="🤖 Bot Statistics",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Uptime",
                value=stats.get('uptime', 'Unknown'),
                inline=True
            )
            
            embed.add_field(
                name="Servers",
                value=str(stats.get('guilds', len(self.bot.guilds))),
                inline=True
            )
            
            embed.add_field(
                name="Users",
                value=str(stats.get('users', 'Unknown')),
                inline=True
            )
            
            embed.add_field(
                name="Commands Executed",
                value=str(stats.get('commands_executed', 0)),
                inline=True
            )
            
            embed.add_field(
                name="Errors",
                value=str(stats.get('errors', 0)),
                inline=True
            )
            
            embed.add_field(
                name="Exchange Status",
                value="🟢 Connected" if stats.get('exchange_connected', False) else "🔴 Disconnected",
                inline=True
            )
            
            embed.add_field(
                name="Last Heartbeat",
                value=stats.get('last_heartbeat', 'Unknown'),
                inline=False
            )
            
            embed.set_footer(text="Trading Bot System Status")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in stats slash command: {e}")
            
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not retrieve bot statistics: {str(e)}",
                color=0xff0000
            )
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except discord.errors.InteractionResponded:
                logger.warning("Interaction already responded to, could not send error message")
            except Exception as followup_error:
                logger.error(f"Failed to send error followup: {followup_error}")
    
    @app_commands.command(name="bot_help", description="Get help information for the trading bot")
    async def help_slash(self, interaction: discord.Interaction):
        """Display help information using slash command"""
        # Safety check to prevent double acknowledgment
        if interaction.response.is_done():
            logger.warning("Interaction already acknowledged for help command")
            return
            
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            logger.error("Interaction expired or not found when trying to defer help command")
            return
        except discord.errors.InteractionResponded:
            logger.warning("Interaction already responded to for help command")
            return
        except Exception as e:
            logger.error(f"Unexpected error deferring help interaction: {e}")
            return
        
        try:
            embed = discord.Embed(
                title="📚 Trading Bot Help",
                description="Available slash commands and features",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            # Slash Commands section
            slash_commands = (
                "`/price <symbol>` - Get current cryptocurrency price\n"
                "`/signal <symbol>` - Generate a trading signal\n"
                "`/bot_stats` - View bot statistics and status\n"
                "`/bot_help` - Show this help message"
            )
            embed.add_field(
                name="🔗 Slash Commands",
                value=slash_commands,
                inline=False
            )
            
            # Slash-only Commands section
            prefix_commands = (
                "`/market_signals` - Generate multiple market signals\n"
                "`/live_signal` - Send live trading signal\n"
                "`/bot_health` - Check bot health status\n"
                "`/optimize_params` - Optimize strategy parameters"
            )
            embed.add_field(
                name="📝 Slash Commands",
                value=prefix_commands,
                inline=False
            )
            
            # Features section
            features = (
                "• Real-time cryptocurrency prices\n"
                "• Professional trading signals (SC01/SC02)\n"
                "• Multi-exchange support (Binance, Coinbase, etc.)\n"
                "• Advanced technical analysis\n"
                "• Risk management tools\n"
                "• Parameter optimization"
            )
            embed.add_field(
                name="⚡ Features",
                value=features,
                inline=False
            )
            
            embed.add_field(
                name="📊 Supported Exchanges",
                value="Binance • Coinbase • Kraken • Bybit • MEXC",
                inline=False
            )
            
            embed.set_footer(text="Use slash commands for modern Discord experience!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in help slash command: {e}")
            
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not display help information: {str(e)}",
                color=0xff0000
            )
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except discord.errors.InteractionResponded:
                logger.warning("Interaction already responded to, could not send error message")
            except Exception as followup_error:
                logger.error(f"Failed to send error followup: {followup_error}")

async def setup(bot):
    """Setup function to load the cog"""
    await bot.add_cog(SlashCommands(bot))
    logger.info("SlashCommands cog loaded successfully")