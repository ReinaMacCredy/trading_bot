"""
Portfolio Commands Cog for Discord Trading Bot
Implements portfolio management commands
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PortfolioCommands(commands.Cog):
    """Portfolio management commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Portfolio commands cog initialized")
    
    @commands.command(name="portfolio")
    async def portfolio(self, ctx):
        """Show portfolio summary"""
        try:
            embed = discord.Embed(
                title="📈 Portfolio Summary",
                description="Current portfolio status (Demo Mode)",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            # Demo portfolio data
            portfolio_value = 12500.00
            daily_change = 2.35
            weekly_change = 5.78
            
            embed.add_field(
                name="💰 Total Value",
                value=f"${portfolio_value:,.2f}",
                inline=False
            )
            
            embed.add_field(
                name="📊 Daily Change",
                value=f"{'🟢' if daily_change >= 0 else '🔴'} {daily_change:.2f}%",
                inline=True
            )
            
            embed.add_field(
                name="📈 Weekly Change",
                value=f"{'🟢' if weekly_change >= 0 else '🔴'} {weekly_change:.2f}%",
                inline=True
            )
            
            # Demo assets
            assets = [
                {"symbol": "BTC", "amount": 0.1, "value": 5000.00, "allocation": 40.0},
                {"symbol": "ETH", "amount": 2.5, "value": 4000.00, "allocation": 32.0},
                {"symbol": "ADA", "amount": 1000, "value": 500.00, "allocation": 4.0},
                {"symbol": "USDT", "amount": 3000, "value": 3000.00, "allocation": 24.0}
            ]
            
            for asset in assets:
                embed.add_field(
                    name=f"{asset['symbol']}",
                    value=f"Amount: {asset['amount']}\nValue: ${asset['value']:,.2f}\nAllocation: {asset['allocation']}%",
                    inline=True
                )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in portfolio command: {e}")
            await ctx.send(f"❌ Error fetching portfolio: {str(e)}")
    
    @commands.command(name="position_size")
    async def position_size(self, ctx, symbol: str, entry_price: float, stop_loss: float):
        """Calculate optimal position size based on risk management"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            # Demo account balance
            account_balance = 10000.00
            risk_percentage = 2.0  # 2% risk per trade
            
            # Calculate risk
            risk_per_unit = abs(entry_price - stop_loss)
            if risk_per_unit == 0:
                await ctx.send("❌ Entry price and stop loss cannot be the same.")
                return
                
            risk_amount = account_balance * (risk_percentage / 100)
            position_size = risk_amount / risk_per_unit
            position_value = position_size * entry_price
            
            embed = discord.Embed(
                title=f"📊 Position Size Calculator: {symbol}",
                description=f"Based on risk management principles",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Symbol",
                value=symbol,
                inline=True
            )
            
            embed.add_field(
                name="Account Balance",
                value=f"${account_balance:,.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Risk Per Trade",
                value=f"{risk_percentage:.1f}%",
                inline=True
            )
            
            embed.add_field(
                name="Entry Price",
                value=f"${entry_price:,.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Stop Loss",
                value=f"${stop_loss:,.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Risk Per Unit",
                value=f"${risk_per_unit:,.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Position Size",
                value=f"{position_size:,.8f} {symbol.replace('USDT', '')}",
                inline=False
            )
            
            embed.add_field(
                name="Position Value",
                value=f"${position_value:,.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Max Loss",
                value=f"${risk_amount:,.2f}",
                inline=True
            )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in position_size command: {e}")
            await ctx.send(f"❌ Error calculating position size: {str(e)}")

async def setup(bot):
    await bot.add_cog(PortfolioCommands(bot))
    logger.info("Portfolio commands cog loaded") 