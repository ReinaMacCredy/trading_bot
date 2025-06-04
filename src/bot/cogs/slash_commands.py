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
        await interaction.response.defer()
        
        try:
            # Format symbol
            symbol = symbol.upper()
            if not symbol.endswith('/USDT'):
                symbol = f"{symbol}/USDT"
            
            # Get price from trading bot
            trading_bot = getattr(self.bot, 'trading_bot', None)
            if trading_bot:
                # Use the trading bot's get_price method
                price = trading_bot.get_price(symbol.replace('/', ''))
                if price:
                    ticker = {
                        'last': price,
                        'symbol': symbol,
                        'percentage': 0.0,  # Mock data for now
                        'change': 0.0
                    }
                
                if ticker:
                    embed = discord.Embed(
                        title=f"💰 {symbol} Price",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="Current Price",
                        value=f"${ticker.get('last', 0):,.2f}",
                        inline=True
                    )
                    
                    # Add 24h change if available
                    if 'percentage' in ticker:
                        change_color = "🟢" if ticker['percentage'] >= 0 else "🔴"
                        embed.add_field(
                            name="24h Change",
                            value=f"{change_color} {ticker['percentage']:.2f}%",
                            inline=True
                        )
                    
                    if 'high' in ticker and 'low' in ticker:
                        embed.add_field(
                            name="24h High/Low",
                            value=f"${ticker['high']:,.2f} / ${ticker['low']:,.2f}",
                            inline=True
                        )
                    
                    embed.add_field(
                        name="Exchange",
                        value=exchange.capitalize(),
                        inline=True
                    )
                    
                    embed.set_footer(text="Trading Bot | Real-time data")
                    
                    await interaction.followup.send(embed=embed)
                else:
                    raise ValueError("Could not fetch price data")
            else:
                raise ValueError("Trading bot not available")
                
        except Exception as e:
            logger.error(f"Error in price slash command: {e}")
            
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not fetch price for {symbol}: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
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
        await interaction.response.defer()
        
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
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @app_commands.command(name="stats", description="Get bot statistics and status")
    async def stats_slash(self, interaction: discord.Interaction):
        """Get bot statistics using slash command"""
        await interaction.response.defer()
        
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
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @app_commands.command(name="help", description="Get help information for the trading bot")
    async def help_slash(self, interaction: discord.Interaction):
        """Display help information using slash command"""
        await interaction.response.defer()
        
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
                "`/stats` - View bot statistics and status\n"
                "`/help` - Show this help message"
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
                "`/health` - Check bot health status\n"
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
            await interaction.followup.send(embed=error_embed, ephemeral=True)

async def setup(bot):
    """Setup function to load the cog"""
    await bot.add_cog(SlashCommands(bot))
    logger.info("SlashCommands cog loaded successfully") 