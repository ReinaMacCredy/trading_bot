"""
Multi-Exchange Discord Commands
Handles commands for Binance, MEXC, and MT5 exchanges
"""

import discord
from discord.ext import commands
import logging
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

from src.trading.multi_exchange_manager import MultiExchangeManager, UnifiedTicker
from src.utils.embed_builder import create_embed

logger = logging.getLogger(__name__)

class MultiExchangeCommands(commands.Cog):
    """Discord commands for multi-exchange functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.multi_exchange_manager = None
        
    async def cog_load(self):
        """Initialize multi-exchange manager when cog loads"""
        try:
            self.multi_exchange_manager = MultiExchangeManager(config=self.bot.config)
            await self.multi_exchange_manager.test_all_connections()
            logger.info("Multi-exchange manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize multi-exchange manager: {e}")
    
    @commands.command(name='exchanges', aliases=['exch', 'ex'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def show_exchanges(self, ctx):
        """Display status of all configured exchanges"""
        if not self.multi_exchange_manager:
            embed = create_embed(
                title="❌ Multi-Exchange Error",
                description="Multi-exchange manager not initialized",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            status = self.multi_exchange_manager.get_exchange_status()
            
            embed = create_embed(
                title="🏛️ Exchange Status",
                description="Multi-Exchange Trading Bot Status",
                color=discord.Color.blue()
            )
            
            # Group exchanges by type
            crypto_exchanges = {}
            forex_exchanges = {}
            
            for name, info in status.items():
                if info['type'] == 'crypto':
                    crypto_exchanges[name] = info
                else:
                    forex_exchanges[name] = info
            
            # Add crypto exchanges
            if crypto_exchanges:
                crypto_text = ""
                for name, info in crypto_exchanges.items():
                    status_icon = "🟢" if info['connected'] else "🔴"
                    enabled_icon = "✅" if info['enabled'] else "❌"
                    
                    crypto_text += f"{status_icon} **{name.upper()}** {enabled_icon}\n"
                    if info['last_error'] and not info['connected']:
                        crypto_text += f"   └─ ⚠️ {info['last_error'][:50]}...\n"
                
                embed.add_field(
                    name="🪙 Cryptocurrency Exchanges",
                    value=crypto_text or "No crypto exchanges configured",
                    inline=False
                )
            
            # Add forex exchanges
            if forex_exchanges:
                forex_text = ""
                for name, info in forex_exchanges.items():
                    status_icon = "🟢" if info['connected'] else "🔴"
                    enabled_icon = "✅" if info['enabled'] else "❌"
                    
                    forex_text += f"{status_icon} **{name.upper()}** {enabled_icon}\n"
                    if info['last_error'] and not info['connected']:
                        forex_text += f"   └─ ⚠️ {info['last_error'][:50]}...\n"
                
                embed.add_field(
                    name="💱 Forex/CFD Exchanges",
                    value=forex_text or "No forex exchanges configured",
                    inline=False
                )
            
            # Add available exchanges summary
            available = self.multi_exchange_manager.get_available_exchanges()
            embed.add_field(
                name="📊 Available for Trading",
                value=", ".join([ex.upper() for ex in available]) if available else "None",
                inline=False
            )
            
            embed.set_footer(text="🟢 Connected • 🔴 Disconnected • ✅ Enabled • ❌ Disabled")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing exchange status: {e}")
            embed = create_embed(
                title="❌ Exchange Status Error",
                description=f"Failed to retrieve exchange status: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='multiprice', aliases=['mprice', 'mp'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def multi_exchange_price(self, ctx, symbol: str, exchange: str = None):
        """Get price from multiple exchanges or specific exchange"""
        if not self.multi_exchange_manager:
            embed = create_embed(
                title="❌ Multi-Exchange Error",
                description="Multi-exchange manager not initialized",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            symbol = symbol.upper()
            
            if exchange:
                # Get price from specific exchange
                exchange = exchange.lower()
                ticker = await self.multi_exchange_manager.fetch_ticker(symbol, exchange)
                
                if ticker:
                    embed = create_embed(
                        title=f"💰 {symbol} Price - {exchange.upper()}",
                        color=discord.Color.green()
                    )
                    
                    embed.add_field(
                        name="💵 Current Price",
                        value=f"**${ticker.last:,.4f}**",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📈 Bid/Ask",
                        value=f"Bid: ${ticker.bid:,.4f}\nAsk: ${ticker.ask:,.4f}",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📊 Volume",
                        value=f"{ticker.volume:,.2f}",
                        inline=True
                    )
                    
                    if ticker.change_24h:
                        change_color = "🟢" if ticker.change_24h > 0 else "🔴"
                        embed.add_field(
                            name="📈 24h Change",
                            value=f"{change_color} {ticker.change_24h:+.2f}%",
                            inline=True
                        )
                    
                    embed.set_footer(text=f"Exchange: {exchange.upper()} • {ticker.timestamp.strftime('%H:%M:%S UTC')}")
                    
                else:
                    embed = create_embed(
                        title="❌ Price Error",
                        description=f"Could not fetch {symbol} price from {exchange.upper()}",
                        color=discord.Color.red()
                    )
                
                await ctx.send(embed=embed)
                
            else:
                # Get prices from all available exchanges
                available_exchanges = self.multi_exchange_manager.get_available_exchanges()
                
                if not available_exchanges:
                    embed = create_embed(
                        title="❌ No Exchanges Available",
                        description="No exchanges are currently connected",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = create_embed(
                    title=f"💰 {symbol} Multi-Exchange Prices",
                    description=f"Prices from {len(available_exchanges)} exchanges",
                    color=discord.Color.blue()
                )
                
                # Fetch prices concurrently
                tasks = [
                    self.multi_exchange_manager.fetch_ticker(symbol, ex)
                    for ex in available_exchanges
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                prices = []
                for i, result in enumerate(results):
                    exchange_name = available_exchanges[i]
                    
                    if isinstance(result, Exception):
                        embed.add_field(
                            name=f"❌ {exchange_name.upper()}",
                            value="Connection Error",
                            inline=True
                        )
                    elif result:
                        prices.append((exchange_name, result.last))
                        change_text = ""
                        if result.change_24h:
                            change_color = "🟢" if result.change_24h > 0 else "🔴"
                            change_text = f"\n{change_color} {result.change_24h:+.2f}%"
                        
                        embed.add_field(
                            name=f"💵 {exchange_name.upper()}",
                            value=f"**${result.last:,.4f}**{change_text}",
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name=f"⚠️ {exchange_name.upper()}",
                            value="No Data",
                            inline=True
                        )
                
                # Add price comparison if we have multiple prices
                if len(prices) > 1:
                    min_price = min(prices, key=lambda x: x[1])
                    max_price = max(prices, key=lambda x: x[1])
                    spread = max_price[1] - min_price[1]
                    spread_pct = (spread / min_price[1]) * 100
                    
                    embed.add_field(
                        name="📊 Price Analysis",
                        value=f"**Spread:** ${spread:.4f} ({spread_pct:.2f}%)\n"
                              f"**Lowest:** {min_price[0].upper()}\n"
                              f"**Highest:** {max_price[0].upper()}",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error fetching multi-exchange price: {e}")
            embed = create_embed(
                title="❌ Price Fetch Error",
                description=f"Failed to fetch price data: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='balances', aliases=['bal', 'balance'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def show_balances(self, ctx, exchange: str = None):
        """Show account balances from all exchanges or specific exchange"""
        if not self.multi_exchange_manager:
            embed = create_embed(
                title="❌ Multi-Exchange Error",
                description="Multi-exchange manager not initialized",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            balances = await self.multi_exchange_manager.get_account_balance(exchange)
            
            if not balances:
                embed = create_embed(
                    title="❌ Balance Error",
                    description="No balance data available or no API keys configured",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            embed = create_embed(
                title="💰 Account Balances",
                description="Multi-Exchange Account Overview",
                color=discord.Color.green()
            )
            
            for exchange_name, balance_data in balances.items():
                if isinstance(balance_data, dict):
                    if 'total' in balance_data:
                        # Crypto exchange format
                        total_usd = 0
                        balance_text = ""
                        
                        for currency, amount in balance_data['free'].items():
                            if amount > 0:
                                balance_text += f"**{currency}:** {amount:.4f}\n"
                        
                        if not balance_text:
                            balance_text = "No significant balances"
                        
                        embed.add_field(
                            name=f"🪙 {exchange_name.upper()}",
                            value=balance_text[:1024],  # Discord limit
                            inline=True
                        )
                    else:
                        # MT5 forex format
                        balance_text = (
                            f"**Balance:** {balance_data.get('balance', 0):,.2f} {balance_data.get('currency', 'USD')}\n"
                            f"**Equity:** {balance_data.get('equity', 0):,.2f}\n"
                            f"**Free Margin:** {balance_data.get('free_margin', 0):,.2f}\n"
                            f"**Profit:** {balance_data.get('profit', 0):+,.2f}"
                        )
                        
                        embed.add_field(
                            name=f"💱 {exchange_name.upper()}",
                            value=balance_text,
                            inline=True
                        )
            
            embed.set_footer(text=f"Updated: {datetime.now().strftime('%H:%M:%S UTC')}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error fetching balances: {e}")
            embed = create_embed(
                title="❌ Balance Error",
                description=f"Failed to fetch balance data: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='testconn', aliases=['test'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def test_connections(self, ctx):
        """Test connections to all exchanges"""
        if not self.multi_exchange_manager:
            embed = create_embed(
                title="❌ Multi-Exchange Error",
                description="Multi-exchange manager not initialized",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            embed = create_embed(
                title="🔄 Testing Exchange Connections...",
                description="Please wait while we test all exchange connections",
                color=discord.Color.orange()
            )
            
            message = await ctx.send(embed=embed)
            
            # Test all connections
            results = await self.multi_exchange_manager.test_all_connections()
            
            embed = create_embed(
                title="🧪 Exchange Connection Test Results",
                color=discord.Color.blue()
            )
            
            connected_count = 0
            total_count = len(results)
            
            for exchange, connected in results.items():
                status_icon = "🟢" if connected else "🔴"
                status_text = "Connected" if connected else "Failed"
                
                embed.add_field(
                    name=f"{status_icon} {exchange.upper()}",
                    value=status_text,
                    inline=True
                )
                
                if connected:
                    connected_count += 1
            
            # Add summary
            summary_color = "🟢" if connected_count == total_count else "🟡" if connected_count > 0 else "🔴"
            embed.add_field(
                name="📊 Summary",
                value=f"{summary_color} {connected_count}/{total_count} exchanges connected",
                inline=False
            )
            
            embed.set_footer(text=f"Test completed at {datetime.now().strftime('%H:%M:%S UTC')}")
            
            await message.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Error testing connections: {e}")
            embed = create_embed(
                title="❌ Connection Test Error",
                description=f"Failed to test connections: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(MultiExchangeCommands(bot)) 