"""
Analysis Commands Cog for Discord Trading Bot
Implements technical analysis commands
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal
import logging
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

try:
    from src.trading.indicators.legacy_indicators import IndicatorFactory
except ImportError as e:
    logger.exception("CRITICAL: Failed to import IndicatorFactory from src.trading.indicators.legacy_indicators. The AnalysisCommands cog will NOT load.", exc_info=True)
    raise # Re-raise to ensure the cog loading fails visibly

class AnalysisCommands(commands.Cog):
    """Technical analysis commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Analysis commands cog initialized")
    
    @commands.command(name="dual_macd_rsi")
    async def dual_macd_rsi(self, ctx, symbol: str):
        """Analyze a symbol with dual timeframe MACD+RSI strategy (1h + 4h)"""
        try:
            # Setup
            await ctx.send(f"COG_V4_ACTIVE: Analyzing {symbol.upper()}USDT with dual timeframe MACD+RSI strategy (1h + 4h)...")
            
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
            
            # Get market data for both timeframes directly from exchange client
            if not self.bot.exchange_client:
                await ctx.send(f"❌ Exchange client not initialized.")
                return

            df_1h_raw = await self.bot.exchange_client.fetch_ohlcv(symbol, '1h', limit=100)
            df_4h_raw = await self.bot.exchange_client.fetch_ohlcv(symbol, '4h', limit=50)

            if df_1h_raw is None or df_4h_raw is None:
                await ctx.send(f"❌ Error fetching market data for {symbol}")
                return

            # Convert to DataFrame and ensure correct format if not already
            # The fetch_ohlcv from ExchangeClient already returns a DataFrame with timestamp index
            # but legacy_indicators might expect timestamp as a column.
            
            df_1h = df_1h_raw.copy()
            if df_1h.index.name == 'timestamp':
                df_1h = df_1h.reset_index()

            df_4h = df_4h_raw.copy()
            if df_4h.index.name == 'timestamp':
                df_4h = df_4h.reset_index()

            # Ensure required columns are present (IndicatorFactory might rely on this)
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df_1h.columns:
                    await ctx.send(f"❌ Market data for 1h timeframe missing column: {col}")
                    return
                if col not in df_4h.columns:
                    await ctx.send(f"❌ Market data for 4h timeframe missing column: {col}")
                    return

            # Create indicator
            indicator = IndicatorFactory.get_indicator('dual_macd_rsi')
            
            # Calculate signals with dual timeframe confirmation
            result = indicator.get_signal(df_1h, df_4h)
            
            if result is None:
                await ctx.send(f"❌ Error calculating signals for {symbol}")
                return
            
            # Get the most recent signal
            current_signal = result['signal'].iloc[-1]
            
            # Determine signal type
            if current_signal > 0:
                signal_type = "BUY"
                signal_emoji = "🟢"
                color = 0x00ff00
            elif current_signal < 0:
                signal_type = "SELL"
                signal_emoji = "🔴"
                color = 0xff0000
            else:
                signal_type = "NEUTRAL"
                signal_emoji = "⚪"
                color = 0x808080
            
            # Get indicator values
            rsi_value = result['rsi'].iloc[-1]
            macd_value = result['macd'].iloc[-1]
            signal_line = result['signal_line'].iloc[-1]
            histogram = result['histogram'].iloc[-1]
            
            # Create embed
            embed = discord.Embed(
                title=f"📊 Dual MACD+RSI Analysis: {symbol}",
                description=f"Analysis using dual timeframe MACD+RSI strategy (1h + 4h)",
                color=color,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Signal",
                value=f"{signal_emoji} {signal_type}",
                inline=False
            )
            
            embed.add_field(
                name="RSI (1h)",
                value=f"{rsi_value:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="MACD (1h)",
                value=f"MACD: {macd_value:.2f}\nSignal: {signal_line:.2f}\nHistogram: {histogram:.2f}",
                inline=True
            )
            
            if 'higher_tf_bullish' in result.columns:
                higher_tf_trend = "Bullish" if result['higher_tf_bullish'].iloc[-1] else "Bearish"
                embed.add_field(
                    name="4h Trend",
                    value=f"{'🟢' if higher_tf_trend == 'Bullish' else '🔴'} {higher_tf_trend}",
                    inline=True
                )
            
            embed.set_footer(text="Trading Bot | Real-time Analysis")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in dual_macd_rsi command: {e}")
            logger.error(traceback.format_exc())
            await ctx.send(f"An error occurred while analyzing {symbol}: {str(e)}")
    
    @commands.command(name="a_indicator")
    async def analyze_indicator(self, ctx, indicator_name: str, symbol: str, interval: str = "1h", *args):
        """Analyze a symbol using a specific indicator"""
        try:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            indicator_name = indicator_name.upper()
            
            embed = discord.Embed(
                title=f"📊 Indicator Analysis: {indicator_name}",
                description=f"Analysis of {symbol} on {interval} timeframe",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            # Demo indicator values
            values = {
                "RSI": f"{30 + hash(symbol + indicator_name) % 40:.2f}",
                "MACD": f"MACD: {hash(symbol) % 10 - 5:.2f}, Signal: {hash(symbol + 'signal') % 10 - 5:.2f}",
                "EMA": f"EMA20: {10000 + hash(symbol + 'ema20') % 1000:.2f}, EMA50: {10000 + hash(symbol + 'ema50') % 1000:.2f}",
                "BBANDS": f"Upper: {10000 + hash(symbol + 'upper') % 1000:.2f}, Middle: {10000 + hash(symbol) % 1000:.2f}, Lower: {10000 + hash(symbol + 'lower') % 1000:.2f}",
                "ATR": f"{hash(symbol + 'atr') % 100:.2f}"
            }
            
            value = values.get(indicator_name, f"Demo value for {indicator_name}")
            
            embed.add_field(
                name="Symbol",
                value=symbol,
                inline=True
            )
            
            embed.add_field(
                name="Timeframe",
                value=interval,
                inline=True
            )
            
            embed.add_field(
                name=indicator_name,
                value=value,
                inline=False
            )
            
            if indicator_name == "RSI":
                rsi_value = float(values["RSI"])
                if rsi_value < 30:
                    signal = "🟢 Oversold (Bullish)"
                elif rsi_value > 70:
                    signal = "🔴 Overbought (Bearish)"
                else:
                    signal = "⚪ Neutral"
                
                embed.add_field(
                    name="Signal",
                    value=signal,
                    inline=False
                )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in analyze_indicator command: {e}")
            await ctx.send(f"❌ Error analyzing indicator: {str(e)}")
    
    @commands.command(name="help_indicators")
    async def help_indicators(self, ctx):
        """Show help for indicators"""
        try:
            embed = discord.Embed(
                title="📊 Technical Indicators Help",
                description="Available technical indicators and how to use them",
                color=0x0099ff
            )
            
            embed.add_field(
                name="RSI (Relative Strength Index)",
                value="Usage: `b!indicator RSI <symbol> [interval]`\nDefault interval: 1h",
                inline=False
            )
            
            embed.add_field(
                name="MACD (Moving Average Convergence Divergence)",
                value="Usage: `b!indicator MACD <symbol> [interval]`\nDefault interval: 1h",
                inline=False
            )
            
            embed.add_field(
                name="EMA (Exponential Moving Average)",
                value="Usage: `b!indicator EMA <symbol> [interval] [period]`\nDefault interval: 1h, Default period: 20",
                inline=False
            )
            
            embed.add_field(
                name="BBANDS (Bollinger Bands)",
                value="Usage: `b!indicator BBANDS <symbol> [interval]`\nDefault interval: 1h",
                inline=False
            )
            
            embed.add_field(
                name="ATR (Average True Range)",
                value="Usage: `b!indicator ATR <symbol> [interval]`\nDefault interval: 1h",
                inline=False
            )
            
            embed.add_field(
                name="Dual MACD+RSI",
                value="Usage: `b!dual_macd_rsi <symbol>`\nCombines MACD and RSI with dual timeframe confirmation",
                inline=False
            )
            
            embed.set_footer(text="Trading Bot | Prefix: b!")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in help_indicators command: {e}")
            await ctx.send(f"❌ Error showing indicators help: {str(e)}")

async def setup(bot):
    await bot.add_cog(AnalysisCommands(bot))
    logger.info("Analysis commands cog loaded") 