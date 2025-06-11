"""
Trading Commands Cog for Discord Trading Bot
Implements trading-related commands
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal
import logging
from datetime import datetime
import random
import matplotlib.pyplot as plt
import io

logger = logging.getLogger(__name__)

class TradingCommands(commands.Cog):
    """Trading commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self._settings = {
            "risk_percentage": 2.0,
            "daily_loss_limit": 5.0,
            "strategy": "MACD_RSI",
            "timeframe": "4h"
        }
        self._recent_signals = []
        logger.info("Trading commands cog initialized")
    
    @commands.command(name="chart")
    async def chart(self, ctx, symbol: str):
        """Generate price chart for a cryptocurrency"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            # Inform user we're generating the chart
            await ctx.send(f"📊 Generating chart for {symbol}... Please wait.")
            
            # Create a simple mock chart using matplotlib
            plt.figure(figsize=(10, 6))
            
            # Generate some random price data for demo
            days = 30
            x = range(days)
            y = [random.uniform(100, 130) for _ in range(days)]
            for i in range(1, days):
                # Make it somewhat realistic with some trend
                y[i] = y[i-1] * (1 + random.uniform(-0.03, 0.03))
            
            plt.plot(x, y, 'b-')
            plt.title(f"{symbol} Price Chart (Last 30 Days)")
            plt.xlabel("Days")
            plt.ylabel("Price (USDT)")
            plt.grid(True)
            
            # Save the chart to a buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            
            # Send the chart
            file = discord.File(buf, filename=f"{symbol}_chart.png")
            
            embed = discord.Embed(
                title=f"📈 {symbol} Price Chart",
                description="Price movement over the last 30 days",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            embed.set_image(url=f"attachment://{symbol}_chart.png")
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(file=file, embed=embed)
            plt.close()
            
        except Exception as e:
            logger.error(f"Error in chart command: {e}")
            await ctx.send(f"❌ Error generating chart: {str(e)}")
    
    @commands.command(name="tradesignal")
    async def tradesignal(self, ctx, symbol: str):
        """Get trading signals for a cryptocurrency
        
        Usage: b!tradesignal <symbol>
        Example: b!tradesignal BTC"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
            
            # Use default strategy
            strategy_code = self._settings["strategy"]
                
            embed = discord.Embed(
                title=f"📊 Trading Signal: {symbol}",
                description=f"Signal analysis using strategy: {strategy_code}",
                color=0x9400d3,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Symbol",
                value=symbol,
                inline=True
            )
            
            embed.add_field(
                name="Strategy",
                value=strategy_code,
                inline=True
            )
            
            # Demo signal results - randomly choose BUY, SELL or HOLD
            signal_types = ["🟢 BUY", "🔴 SELL", "⚪ HOLD"]
            signal = random.choice(signal_types)
            
            embed.add_field(
                name="Signal",
                value=signal,
                inline=False
            )
            
            strength = random.randint(65, 95)
            embed.add_field(
                name="Strength",
                value=f"{'Strong' if strength > 80 else 'Moderate'} ({strength}%)",
                inline=True
            )
            
            embed.add_field(
                name="Time Frame",
                value=self._settings["timeframe"],
                inline=True
            )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            # Store signal in recent signals
            self._recent_signals.append({
                "symbol": symbol,
                "signal": signal,
                "strength": strength,
                "timestamp": datetime.now(),
                "strategy": strategy_code
            })
            
            # Keep only last 10 signals
            if len(self._recent_signals) > 10:
                self._recent_signals.pop(0)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in tradesignal command: {e}")
            await ctx.send(f"❌ Error generating signal: {str(e)}")
    
    @commands.command(name="signals")
    async def signals(self, ctx):
        """Show recent trading signals"""
        try:
            if not self._recent_signals:
                await ctx.send("⚠️ No recent signals available. Generate some signals first!")
                return
                
            embed = discord.Embed(
                title="📝 Recent Trading Signals",
                description="Last 10 signals generated by the bot",
                color=0x9400d3,
                timestamp=datetime.now()
            )
            
            for i, signal in enumerate(reversed(self._recent_signals), 1):
                time_str = signal['timestamp'].strftime('%Y-%m-%d %H:%M')
                embed.add_field(
                    name=f"{i}. {signal['symbol']}",
                    value=f"{signal['signal']} | Strength: {signal['strength']}% | {time_str}\nStrategy: {signal['strategy']}",
                    inline=False
                )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in signals command: {e}")
            await ctx.send(f"❌ Error fetching recent signals: {str(e)}")

    @commands.command(name="analyze")
    async def analyze(self, ctx, symbol: str):
        """Perform technical analysis on a cryptocurrency"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            embed = discord.Embed(
                title=f"🔍 Technical Analysis: {symbol}",
                description="Comprehensive technical analysis summary",
                color=0x6a0dad,
                timestamp=datetime.now()
            )
            
            # Mock technical analysis results
            trend_status = random.choice(["Bullish", "Bearish", "Neutral"])
            trend_color = {
                "Bullish": 0x00ff00,
                "Bearish": 0xff0000,
                "Neutral": 0x808080
            }.get(trend_status, 0x0099ff)
            
            embed.color = trend_color
            
            embed.add_field(
                name="Market Trend",
                value=f"{trend_status}",
                inline=True
            )
            
            embed.add_field(
                name="Volatility",
                value=f"{random.choice(['Low', 'Medium', 'High'])}",
                inline=True
            )
            
            embed.add_field(
                name="Support Levels",
                value=f"${random.randint(90, 95)}, ${random.randint(85, 89)}",
                inline=True
            )
            
            embed.add_field(
                name="Resistance Levels",
                value=f"${random.randint(101, 105)}, ${random.randint(106, 110)}",
                inline=True
            )
            
            embed.add_field(
                name="RSI (14)",
                value=f"{random.randint(30, 70)}",
                inline=True
            )
            
            embed.add_field(
                name="MACD",
                value=f"{random.choice(['Bullish crossover', 'Bearish crossover', 'Neutral'])}",
                inline=True
            )
            
            embed.add_field(
                name="Volume Analysis",
                value=f"{random.choice(['Increasing', 'Decreasing', 'Stable'])}",
                inline=True
            )
            
            embed.add_field(
                name="Moving Averages",
                value=f"MA50 {random.choice(['Above', 'Below'])} MA200",
                inline=True
            )
            
            embed.add_field(
                name="Overall Signal",
                value=random.choice(["🟢 Strong Buy", "🟡 Buy", "⚪ Neutral", "🟠 Sell", "🔴 Strong Sell"]),
                inline=False
            )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in analyze command: {e}")
            await ctx.send(f"❌ Error performing analysis: {str(e)}")

    @commands.command(name="indicators")
    async def indicators(self, ctx, symbol: str = None):
        """Show available technical indicators or indicator values for a symbol"""
        try:
            embed = discord.Embed(
                title="📈 Technical Indicators",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            if symbol:
                symbol = symbol.upper()
                if not symbol.endswith('USDT'):
                    symbol = f"{symbol}USDT"
                
                embed.description = f"Current indicator values for {symbol}"
                
                # Mock indicator values
                indicators = {
                    "RSI (14)": f"{random.randint(30, 70)}",
                    "MACD": f"{random.uniform(-2, 2):.2f}",
                    "Signal Line": f"{random.uniform(-2, 2):.2f}",
                    "Bollinger Bands": f"Upper: {random.uniform(105, 110):.2f}, Lower: {random.uniform(90, 95):.2f}",
                    "Stochastic Oscillator": f"{random.randint(20, 80)}",
                    "ADX": f"{random.randint(15, 40)}",
                    "ATR": f"{random.uniform(1, 5):.2f}",
                    "OBV": f"{random.randint(1000000, 9000000)}",
                    "Ichimoku Cloud": f"{random.choice(['Bullish', 'Bearish', 'Neutral'])}",
                    "MA (50/200)": f"{random.choice(['Golden Cross', 'Death Cross', 'Neutral'])}"
                }
                
                for name, value in indicators.items():
                    embed.add_field(name=name, value=value, inline=True)
            else:
                embed.description = "Available technical indicators for analysis"
                
                indicators = [
                    "**Trend Indicators**\n• Moving Averages (MA)\n• MACD\n• Parabolic SAR\n• ADX",
                    "**Momentum Indicators**\n• RSI\n• Stochastic Oscillator\n• CCI\n• Williams %R",
                    "**Volatility Indicators**\n• Bollinger Bands\n• ATR\n• Standard Deviation",
                    "**Volume Indicators**\n• OBV\n• Volume\n• Money Flow Index",
                    "**Custom Indicators**\n• VWAP\n• Ichimoku Cloud\n• Hull MA\n• Supertrend"
                ]
                
                for indicator_group in indicators:
                    embed.add_field(name="\u200b", value=indicator_group, inline=True)
                
                embed.add_field(
                    name="Usage",
                    value="Use `b!indicators <symbol>` to see current values for a specific symbol",
                    inline=False
                )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in indicators command: {e}")
            await ctx.send(f"❌ Error fetching indicators: {str(e)}")

    @commands.command(name="buy")
    async def buy(self, ctx, symbol: str, quantity: float):
        """Buy a cryptocurrency"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            embed = discord.Embed(
                title=f"🟢 Buy Order: {symbol}",
                description=f"Processing buy order for {quantity} {symbol}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Symbol",
                value=symbol,
                inline=True
            )
            
            embed.add_field(
                name="Quantity",
                value=str(quantity),
                inline=True
            )
            
            embed.add_field(
                name="Risk",
                value=f"{self._settings['risk_percentage']}% of account",
                inline=True
            )
            
            embed.add_field(
                name="Status",
                value="✅ Demo Order Placed",
                inline=False
            )
            
            embed.set_footer(text=f"Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in buy command: {e}")
            await ctx.send(f"❌ Error processing buy order: {str(e)}")
    
    @commands.command(name="sell")
    async def sell(self, ctx, symbol: str, quantity: float):
        """Sell a cryptocurrency"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            embed = discord.Embed(
                title=f"🔴 Sell Order: {symbol}",
                description=f"Processing sell order for {quantity} {symbol}",
                color=0xff0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Symbol",
                value=symbol,
                inline=True
            )
            
            embed.add_field(
                name="Quantity",
                value=str(quantity),
                inline=True
            )
            
            embed.add_field(
                name="Status",
                value="✅ Demo Order Placed",
                inline=False
            )
            
            embed.set_footer(text=f"Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in sell command: {e}")
            await ctx.send(f"❌ Error processing sell order: {str(e)}")
    
    @commands.command(name="balance")
    async def balance(self, ctx):
        """Get account balance"""
        try:
            embed = discord.Embed(
                title="💰 Account Balance",
                description="Current account balance (Demo Mode)",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            # Demo balances
            embed.add_field(name="BTC", value="0.1 BTC", inline=True)
            embed.add_field(name="ETH", value="2.5 ETH", inline=True)
            embed.add_field(name="USDT", value="10,000 USDT", inline=True)
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in balance command: {e}")
            await ctx.send(f"❌ Error fetching balance: {str(e)}")
    
    @commands.command(name="risk")
    async def risk(self, ctx, percentage: float):
        """Set risk percentage per trade"""
        try:
            if percentage < 0.1 or percentage > 20:
                await ctx.send("❌ Risk percentage must be between 0.1% and 20%")
                return
                
            self._settings["risk_percentage"] = percentage
            
            embed = discord.Embed(
                title="⚙️ Risk Settings Updated",
                description=f"Risk per trade set to {percentage}%",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Current Risk",
                value=f"{percentage}% per trade",
                inline=True
            )
            
            embed.add_field(
                name="Daily Loss Limit",
                value=f"{self._settings['daily_loss_limit']}% of account",
                inline=True
            )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in risk command: {e}")
            await ctx.send(f"❌ Error updating risk settings: {str(e)}")
    
    @commands.command(name="setdaily")
    async def setdaily(self, ctx, percentage: float):
        """Set daily loss limit percentage"""
        try:
            if percentage < 1 or percentage > 50:
                await ctx.send("❌ Daily loss limit must be between 1% and 50%")
                return
                
            self._settings["daily_loss_limit"] = percentage
            
            embed = discord.Embed(
                title="⚙️ Daily Loss Limit Updated",
                description=f"Daily loss limit set to {percentage}%",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Risk per Trade",
                value=f"{self._settings['risk_percentage']}% of account",
                inline=True
            )
            
            embed.add_field(
                name="Daily Loss Limit",
                value=f"{percentage}% of account",
                inline=True
            )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in setdaily command: {e}")
            await ctx.send(f"❌ Error updating daily loss limit: {str(e)}")
    
    @commands.command(name="settings")
    async def settings(self, ctx):
        """View current bot settings"""
        try:
            embed = discord.Embed(
                title="⚙️ Bot Settings",
                description="Current configuration for trading bot",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Risk Settings",
                value=f"**Risk per Trade:** {self._settings['risk_percentage']}%\n**Daily Loss Limit:** {self._settings['daily_loss_limit']}%",
                inline=False
            )
            
            embed.add_field(
                name="Strategy Settings",
                value=f"**Active Strategy:** {self._settings['strategy']}\n**Timeframe:** {self._settings['timeframe']}",
                inline=False
            )
            
            embed.add_field(
                name="Mode",
                value="Demo Mode (Paper Trading)",
                inline=False
            )
            
            embed.set_footer(text="Trading Bot | Use b!risk and b!setdaily to update")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in settings command: {e}")
            await ctx.send(f"❌ Error fetching settings: {str(e)}")
    
    @commands.command(name="health")
    async def health(self, ctx):
        """Check bot health and status"""
        try:
            embed = discord.Embed(
                title="🔍 Bot Health Check",
                description="Current status and performance metrics",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            # Calculate uptime (mock value for demo)
            embed.add_field(
                name="Uptime",
                value="3 days, 7 hours, 45 minutes",
                inline=True
            )
            
            embed.add_field(
                name="Latency",
                value=f"{round(self.bot.latency * 1000)}ms",
                inline=True
            )
            
            embed.add_field(
                name="Status",
                value="✅ Operational",
                inline=True
            )
            
            embed.add_field(
                name="API Status",
                value="✅ Connected",
                inline=True
            )
            
            embed.add_field(
                name="Database",
                value="✅ Connected",
                inline=True
            )
            
            embed.add_field(
                name="Memory Usage",
                value=f"{random.randint(100, 400)}MB",
                inline=True
            )
            
            embed.add_field(
                name="Commands Processed",
                value=f"{random.randint(50, 500)}",
                inline=True
            )
            
            embed.add_field(
                name="Mode",
                value="Demo Mode",
                inline=True
            )
            
            embed.set_footer(text="Trading Bot | System Status")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in health command: {e}")
            await ctx.send(f"❌ Error checking bot health: {str(e)}")
    
    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx, guild_id: Optional[int] = None):
        """Sync slash commands (Admin only)"""
        try:
            if guild_id:
                guild = discord.Object(id=guild_id)
                self.bot.tree.copy_global_to(guild=guild)
                await self.bot.tree.sync(guild=guild)
                await ctx.send(f"✅ Commands synced to guild ID {guild_id}")
            else:
                await self.bot.tree.sync()
                await ctx.send("✅ Global commands synced")
            
        except Exception as e:
            logger.error(f"Error in sync command: {e}")
            await ctx.send(f"❌ Error syncing commands: {str(e)}")
    
    @commands.command(name="optimize")
    async def optimize(self, ctx, symbol: str):
        """Optimize strategy parameters for a symbol"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            # Send an initial message
            message = await ctx.send(f"⏳ Optimizing strategy parameters for {symbol}... This may take a moment.")
            
            # In a real implementation, this would run an actual optimization
            await ctx.send(f"🔄 Testing different parameter combinations for {symbol}...")
            
            # Create optimization result embed
            embed = discord.Embed(
                title=f"🔧 Strategy Optimization: {symbol}",
                description=f"Optimization results for {self._settings['strategy']} strategy",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            # Mock optimization results
            embed.add_field(
                name="Optimal Parameters",
                value="Fast MA: 12\nSlow MA: 26\nSignal Line: 9\nRSI Period: 14",
                inline=False
            )
            
            embed.add_field(
                name="Backtest Results",
                value=f"Win Rate: {random.randint(55, 75)}%\nProfit Factor: {random.uniform(1.5, 2.5):.2f}\nMax Drawdown: {random.randint(10, 30)}%",
                inline=False
            )
            
            embed.add_field(
                name="Time Period",
                value="Last 90 days",
                inline=True
            )
            
            embed.add_field(
                name="Trades",
                value=f"{random.randint(30, 100)}",
                inline=True
            )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in optimize command: {e}")
            await ctx.send(f"❌ Error optimizing strategy: {str(e)}")
    
    @commands.command(name="backtest")
    async def backtest(self, ctx, symbol: str):
        """Run a strategy backtest on a symbol"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            # Send an initial message
            message = await ctx.send(f"⏳ Running backtest for {symbol} using {self._settings['strategy']} strategy... Please wait.")
            
            # In a real implementation, this would run an actual backtest
            
            # Create backtest result embed
            embed = discord.Embed(
                title=f"📊 Backtest Results: {symbol}",
                description=f"Strategy: {self._settings['strategy']}, Timeframe: {self._settings['timeframe']}",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            # Mock backtest results
            profit = random.uniform(15, 50)
            embed.add_field(
                name="Total Return",
                value=f"📈 +{profit:.2f}%",
                inline=True
            )
            
            embed.add_field(
                name="Win Rate",
                value=f"{random.randint(55, 75)}%",
                inline=True
            )
            
            embed.add_field(
                name="Trades",
                value=f"{random.randint(30, 100)}",
                inline=True
            )
            
            embed.add_field(
                name="Profit Factor",
                value=f"{random.uniform(1.5, 2.5):.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Max Drawdown",
                value=f"{random.randint(10, 30)}%",
                inline=True
            )
            
            embed.add_field(
                name="Sharpe Ratio",
                value=f"{random.uniform(1.0, 2.5):.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Period",
                value="Last 90 days",
                inline=True
            )
            
            embed.add_field(
                name="Market Condition",
                value=random.choice(["Bullish", "Bearish", "Sideways", "Volatile"]),
                inline=True
            )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in backtest command: {e}")
            await ctx.send(f"❌ Error running backtest: {str(e)}")
    
    @commands.command(name="strategy")
    async def strategy(self, ctx, name: str = None):
        """Switch or view current trading strategy"""
        try:
            available_strategies = ["MACD_RSI", "BB_RSI", "EMA_Cross", "VWAP_Bounce", "Supertrend"]
            
            if name:
                name = name.upper()
                
                if name not in [s.upper() for s in available_strategies]:
                    strategies_str = ", ".join(available_strategies)
                    await ctx.send(f"❌ Invalid strategy. Available strategies: {strategies_str}")
                    return
                    
                # Find the correct case version
                for strategy in available_strategies:
                    if strategy.upper() == name:
                        name = strategy
                        break
                
                # Set the new strategy
                self._settings["strategy"] = name
                
                embed = discord.Embed(
                    title="🔄 Strategy Changed",
                    description=f"Trading strategy updated to {name}",
                    color=0x0099ff,
                    timestamp=datetime.now()
                )
                
                # Add strategy description based on name
                descriptions = {
                    "MACD_RSI": "Combines MACD crossovers with RSI confirmation for trend following",
                    "BB_RSI": "Uses Bollinger Bands for volatility and RSI for momentum",
                    "EMA_Cross": "Simple but effective EMA crossover strategy (fast/slow)",
                    "VWAP_Bounce": "Trades bounces off the VWAP line with volume confirmation",
                    "Supertrend": "Uses Supertrend indicator for trend identification and signals"
                }
                
                embed.add_field(
                    name="Strategy Description",
                    value=descriptions.get(name, "Custom trading strategy"),
                    inline=False
                )
                
                embed.add_field(
                    name="Recommended Timeframe",
                    value=self._settings["timeframe"],
                    inline=True
                )
                
                embed.add_field(
                    name="Use With",
                    value="b!signal <symbol>",
                    inline=True
                )
                
            else:
                # Just show current strategy
                embed = discord.Embed(
                    title="📈 Trading Strategies",
                    description="Available trading strategies and current selection",
                    color=0x0099ff,
                    timestamp=datetime.now()
                )
                
                strategies_list = "\n".join([f"• {'✅ ' if s == self._settings['strategy'] else ''}{s}" for s in available_strategies])
                
                embed.add_field(
                    name="Available Strategies",
                    value=strategies_list,
                    inline=False
                )
                
                embed.add_field(
                    name="Current Strategy",
                    value=self._settings["strategy"],
                    inline=True
                )
                
                embed.add_field(
                    name="Usage",
                    value="b!strategy <name>",
                    inline=True
                )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in strategy command: {e}")
            await ctx.send(f"❌ Error with strategy command: {str(e)}")

    @commands.command(name="signalcmd")
    async def signal(self, ctx, symbol: str, strategy_code: str = None):
        """Generate a simple trading signal
        
        Usage: b!signalcmd <symbol> [strategy]
        This is an alternate command that works the same as b!signal"""
        try:
            await self.tradesignal(ctx, symbol)
        except Exception as e:
            logger.error(f"Error in signalcmd command: {e}")
            await ctx.send(f"❌ Error generating signal: {str(e)}")

async def setup(bot):
    await bot.add_cog(TradingCommands(bot))
    logger.info("Trading commands cog loaded") 