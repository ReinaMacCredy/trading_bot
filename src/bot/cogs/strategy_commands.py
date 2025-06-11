"""
Strategy Commands Cog for Discord Trading Bot
Implements strategy-related commands
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class StrategyCommands(commands.Cog):
    """Strategy commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Strategy commands cog initialized")
    
    @commands.command(name="strategies")
    async def list_strategies(self, ctx):
        """List available trading strategies"""
        try:
            embed = discord.Embed(
                title="📊 Available Trading Strategies",
                description="List of available trading strategies",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            # Demo strategies
            strategies = {
                "SC01": "Simple MACD Crossover",
                "SC02": "RSI + MACD Combination",
                "SC02+FRVP": "RSI + MACD with Fibonacci Retracement",
                "DUAL_MACD": "Dual Timeframe MACD Strategy",
                "BBANDS": "Bollinger Bands Strategy"
            }
            
            for code, name in strategies.items():
                embed.add_field(
                    name=code,
                    value=name,
                    inline=False
                )
            
            embed.set_footer(text="Trading Bot | Use !analyze <strategy> <symbol> to test a strategy")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in list_strategies command: {e}")
            await ctx.send(f"❌ Error listing strategies: {str(e)}")
    
    @commands.command(name="analyze")
    async def analyze(self, ctx, strategy: str, symbol: str, interval: str = '1d'):
        """Analyze a symbol using a specific strategy"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            embed = discord.Embed(
                title=f"📈 Strategy Analysis: {symbol}",
                description=f"Analysis using {strategy} strategy on {interval} timeframe",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            # Demo analysis result
            signal = "BUY" if hash(f"{symbol}{strategy}{interval}") % 3 != 0 else "SELL"
            confidence = round(50 + hash(f"{symbol}{strategy}") % 50, 2)
            
            embed.add_field(
                name="Symbol",
                value=symbol,
                inline=True
            )
            
            embed.add_field(
                name="Strategy",
                value=strategy,
                inline=True
            )
            
            embed.add_field(
                name="Timeframe",
                value=interval,
                inline=True
            )
            
            embed.add_field(
                name="Signal",
                value=f"{'🟢' if signal == 'BUY' else '🔴'} {signal}",
                inline=True
            )
            
            embed.add_field(
                name="Confidence",
                value=f"{confidence}%",
                inline=True
            )
            
            embed.add_field(
                name="Note",
                value="This is a demo analysis result",
                inline=False
            )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in analyze command: {e}")
            await ctx.send(f"❌ Error analyzing strategy: {str(e)}")

    # Original signal command removed to avoid conflict with trading_commands.py

    @commands.command(name="strategysignal")
    async def strategysignal(self, ctx, symbol: str, strategy: str = "SC01"):
        """Generate a simple trading signal for a cryptocurrency with a specific strategy
        
        Usage: b!strategysignal <symbol> [strategy]
        Example: b!strategysignal BTC SC01"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            # Demo signal generation
            import random
            signal_type = random.choice(["BUY", "SELL"])
            current_price = 50000 + random.uniform(-5000, 5000) if "BTC" in symbol else 2000 + random.uniform(-200, 200)
            
            if signal_type == "BUY":
                entry_price = current_price * random.uniform(0.99, 1.01)
                tp_price = entry_price * random.uniform(1.05, 1.10)
                sl_price = entry_price * random.uniform(0.90, 0.95)
            else:
                entry_price = current_price * random.uniform(0.99, 1.01)
                tp_price = entry_price * random.uniform(0.90, 0.95)
                sl_price = entry_price * random.uniform(1.05, 1.10)
            
            # Calculate risk/reward ratio
            risk = abs(entry_price - sl_price)
            reward = abs(entry_price - tp_price)
            ratio = reward / risk if risk > 0 else 0
            
            embed = discord.Embed(
                title=f"📊 Trading Signal: {symbol}",
                description=f"Generated signal using {strategy} strategy",
                color=0x00ff00 if signal_type == "BUY" else 0xff0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Signal Type",
                value=f"{'🟢' if signal_type == 'BUY' else '🔴'} {signal_type}",
                inline=True
            )
            
            embed.add_field(
                name="Strategy",
                value=strategy,
                inline=True
            )
            
            embed.add_field(
                name="Current Price",
                value=f"${current_price:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Entry Price",
                value=f"${entry_price:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Take Profit",
                value=f"${tp_price:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Stop Loss",
                value=f"${sl_price:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Risk/Reward",
                value=f"1:{ratio:.2f}",
                inline=True
            )
            
            embed.set_footer(text=f"Trading Bot | Generated at")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in strategysignal command: {e}")
            await ctx.send(f"❌ Error generating signal: {str(e)}")

async def setup(bot):
    await bot.add_cog(StrategyCommands(bot))
    logger.info("Strategy commands cog loaded") 