import discord
from discord.ext import commands
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
from trading import TradingBot
import io

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

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

class TradingSignalBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='//', intents=intents)
        self.trading_bot = TradingBot()
        logger.info("Trading bot initialized")
        
    async def setup_hook(self):
        self.add_commands()
        logger.info("Bot commands registered")
        # Log all registered commands
        command_names = [cmd.name for cmd in self.commands]
        logger.info(f"Registered commands: {', '.join(command_names)}")
    
    def add_commands(self):
        @self.command(name="signal")
        async def send_signal(ctx, pair, strategy, entry_price, tp_price, sl_price, ratio="0.0%", status="", imminent=1):
            """Send a trading signal formatted like the example"""
            if ctx.author != self.user:  # Only process commands from users, not the bot itself
                embed = create_signal_embed(pair, strategy, entry_price, tp_price, sl_price, ratio, status, imminent)
                await ctx.send(embed=embed)
        
        @self.command(name="test")
        async def test_command(ctx):
            """Simple test command to verify the bot is responding"""
            await ctx.send("Test command received! Bot is working.")
        
        @self.command(name="price")
        async def get_price(ctx, symbol):
            """Get current price of a cryptocurrency"""
            if ctx.author == self.user:  # Skip if command came from bot
                return
                
            # Ensure the symbol is in uppercase and has USDT suffix if needed
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
                
            price = self.trading_bot.get_price(symbol)
            if price:
                await ctx.send(f"Current price of {symbol}: ${price}")
            else:
                await ctx.send(f"Could not get price for {symbol}. Make sure it's a valid symbol.")
        
        @self.command(name="indicator")
        async def analyze_indicator(ctx, indicator_name, symbol, interval="1h", *args):
            """Analyze a symbol using a specific indicator
            Usage: //indicator <indicator_name> <symbol> [interval] [params]
            Example: //indicator rsi BTC 1h 14 30 70
            """
            if ctx.author == self.user:  # Skip if command came from bot
                return
                
            # Process the symbol
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
            
            # Parse parameters based on indicator
            params = {}
            if indicator_name.lower() == 'rsi':
                # Default RSI parameters: period, oversold, overbought
                if len(args) >= 1:
                    params['period'] = int(args[0])
                if len(args) >= 3:
                    params['oversold'] = int(args[1])
                    params['overbought'] = int(args[2])
            elif indicator_name.lower() == 'macd':
                # Default MACD parameters: fast_period, slow_period, signal_period
                if len(args) >= 1:
                    params['fast_period'] = int(args[0])
                if len(args) >= 2:
                    params['slow_period'] = int(args[1])
                if len(args) >= 3:
                    params['signal_period'] = int(args[2])
            elif indicator_name.lower() == 'ema':
                # Default EMA parameter: period
                if len(args) >= 1:
                    params['period'] = int(args[0])
            
            # Get analysis result
            result = self.trading_bot.analyze_with_indicator(indicator_name, symbol, interval, **params)
            
            if result:
                # Create embed with the analysis result
                embed = discord.Embed(
                    title=f"{symbol} {indicator_name.upper()} Analysis",
                    description=f"Interval: {interval}",
                    color=0x00FFFF
                )
                
                # Add signal
                signal_emoji = "🔴" if result["signal"] == "SELL" else "🟢" if result["signal"] == "BUY" else "⚪"
                embed.add_field(name="Signal", value=f"{signal_emoji} {result['signal']}", inline=False)
                
                # Add current price
                embed.add_field(name="Current Price", value=f"${result['current_price']:.4f}", inline=True)
                
                # Add indicator-specific fields
                if indicator_name.lower() == 'rsi':
                    embed.add_field(name="RSI Value", value=f"{result['rsi']:.2f}", inline=True)
                    embed.add_field(name="Oversold", value=f"{result['oversold']}", inline=True)
                    embed.add_field(name="Overbought", value=f"{result['overbought']}", inline=True)
                elif indicator_name.lower() == 'macd':
                    embed.add_field(name="MACD Line", value=f"{result['macd']:.6f}", inline=True)
                    embed.add_field(name="Signal Line", value=f"{result['signal_line']:.6f}", inline=True)
                    embed.add_field(name="Histogram", value=f"{result['histogram']:.6f}", inline=True)
                elif indicator_name.lower() == 'ema':
                    embed.add_field(name="EMA Value", value=f"{result['ema']:.4f}", inline=True)
                
                # Set timestamp
                embed.timestamp = datetime.utcnow()
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Could not analyze {symbol} with {indicator_name}. Please check the parameters.")
        
        @self.command(name="indicator_chart")
        async def generate_indicator_chart(ctx, indicator_name, symbol, interval="1h", *args):
            """Generate a chart with indicator visualization
            Usage: //indicator_chart <indicator_name> <symbol> [interval] [params]
            Example: //indicator_chart macd BTC 1h 12 26 9
            """
            if ctx.author == self.user:  # Skip if command came from bot
                return
                
            await ctx.send(f"Generating {indicator_name} chart for {symbol}...")
            
            # Process the symbol
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
            
            # Parse parameters based on indicator (same as analyze_indicator)
            params = {}
            if indicator_name.lower() == 'rsi':
                if len(args) >= 1:
                    params['period'] = int(args[0])
                if len(args) >= 3:
                    params['oversold'] = int(args[1])
                    params['overbought'] = int(args[2])
            elif indicator_name.lower() == 'macd':
                if len(args) >= 1:
                    params['fast_period'] = int(args[0])
                if len(args) >= 2:
                    params['slow_period'] = int(args[1])
                if len(args) >= 3:
                    params['signal_period'] = int(args[2])
            elif indicator_name.lower() == 'ema':
                if len(args) >= 1:
                    params['period'] = int(args[0])
            
            # Generate chart
            chart_buf = self.trading_bot.generate_indicator_chart(indicator_name, symbol, interval, **params)
            
            if chart_buf:
                # Create a Discord file from the buffer
                chart_file = discord.File(fp=chart_buf, filename=f"{symbol}_{indicator_name}_chart.png")
                
                # Create embed with the chart
                embed = discord.Embed(
                    title=f"{symbol} {indicator_name.upper()} Chart",
                    description=f"Interval: {interval}",
                    color=0x00FFFF
                )
                
                # Set the chart image
                embed.set_image(url=f"attachment://{symbol}_{indicator_name}_chart.png")
                
                # Set timestamp
                embed.timestamp = datetime.utcnow()
                
                await ctx.send(embed=embed, file=chart_file)
            else:
                await ctx.send(f"Could not generate chart for {symbol} with {indicator_name}. Please check the parameters.")
        
        @self.command(name="help_indicators")
        async def help_indicators(ctx):
            """Show help for indicator commands"""
            if ctx.author == self.user:
                return
                
            embed = discord.Embed(
                title="Technical Indicator Commands",
                description="Commands for analyzing and visualizing technical indicators",
                color=0x00FFFF
            )
            
            embed.add_field(
                name="//indicator <indicator_name> <symbol> [interval] [params]",
                value="Analyze a symbol using a specific indicator\n"
                      "Example: `//indicator rsi BTC 1h 14 30 70`",
                inline=False
            )
            
            embed.add_field(
                name="//indicator_chart <indicator_name> <symbol> [interval] [params]",
                value="Generate a chart with indicator visualization\n"
                      "Example: `//indicator_chart macd ETH 4h 12 26 9`",
                inline=False
            )
            
            embed.add_field(
                name="Available Indicators",
                value="- `rsi`: Relative Strength Index [period] [oversold] [overbought]\n"
                      "- `macd`: Moving Average Convergence Divergence [fast_period] [slow_period] [signal_period]\n"
                      "- `ema`: Exponential Moving Average [period]",
                inline=False
            )
            
            embed.add_field(
                name="Default Parameters",
                value="- RSI: period=14, oversold=30, overbought=70\n"
                      "- MACD: fast_period=12, slow_period=26, signal_period=9\n"
                      "- EMA: period=20",
                inline=False
            )
            
            await ctx.send(embed=embed)
    
    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        
    async def send_trading_signal(self, channel_id, pair, strategy, entry_price, tp_price, sl_price, ratio="0.0%", status="", imminent=1):
        """Send a trading signal to a specific channel"""
        channel = self.get_channel(int(channel_id))
        if not channel:
            logger.error(f"Channel with ID {channel_id} not found")
            return False
        
        embed = create_signal_embed(pair, strategy, entry_price, tp_price, sl_price, ratio, status, imminent)
        await channel.send(embed=embed)
        return True

def create_signal_embed(pair, strategy, entry_price, tp_price, sl_price, ratio="0.0%", status="takeprofit", imminent=1):
    """Create a Discord embed for a trading signal"""
    # Split the pair into its components
    pair_components = pair.split("-")
    coin = pair_components[0].strip()
    strategy_code = pair_components[1].strip() if len(pair_components) > 1 else ""
    
    # Format the ratio if it doesn't end with %
    if not ratio.endswith("%"):
        ratio = f"{ratio}%"
    
    # Create the embed
    embed = discord.Embed(
        title=f"{coin} - {strategy_code}",
        description="",
        color=0x7CFC00  # Green color
    )
    
    # Format the embed content like the example
    entry_text = f"Entry: {entry_price}"
    tp_text = f"TP (2R): {tp_price}"
    sl_text = f"SL: {sl_price}"
    
    embed.description = f"{entry_text} - {tp_text} - {sl_text}\n"
    embed.description += f"Imminent (Sắp vào Entry): {imminent}\n"
    embed.description += f"Ratio (Tỉ lệ): {ratio}\n"
    embed.description += f"Status (Trạng thái): {status}"
    
    # Set footer
    embed.set_footer(text="By Reina~")
    
    return embed

def run_bot():
    """Run the trading signal bot"""
    if not TOKEN:
        logger.error("Discord token not found in environment variables")
        return
    
    bot = TradingSignalBot()
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot()

