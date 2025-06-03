
import discord
from discord.ext import commands, tasks
import os
import asyncio
import pandas as pd
import ccxt
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class TradingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

        # Initialize exchange (sandbox mode)
        self.exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET'),
            'sandbox': True,  # Use testnet
            'enableRateLimit': True,
        })

        # Trading state
        self.monitoring_symbols = ['BTC/USDT', 'ETH/USDT']
        self.is_trading = False

    async def on_ready(self):
        print(f'{self.user} đã online và sẵn sàng trading!')
        await self.tree.sync()
        # Bắt đầu monitoring loop
        if not self.market_monitor.is_running():
            self.market_monitor.start()

    @tasks.loop(minutes=5)  # Check market mỗi 5 phút
    async def market_monitor(self):
        if not self.is_trading:
            return

        for symbol in self.monitoring_symbols:
            try:
                # Fetch market data
                ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=100)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

                # Simple strategy: RSI + MACD
                signal = self.analyze_market(df)

                if signal != 'HOLD':
                    # Send signal to Discord
                    channel = discord.utils.get(self.get_all_channels(), name='trading-signals')
                    if channel:
                        embed = discord.Embed(
                            title=f"🚨 Trading Signal: {symbol}",
                            color=discord.Color.green() if signal == 'BUY' else discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="Signal", value=signal, inline=True)
                        embed.add_field(name="Price", value=f"${df['close'].iloc[-1]:.4f}", inline=True)
                        await channel.send(embed=embed)

            except Exception as e:
                print(f"Error monitoring {symbol}: {e}")

    def analyze_market(self, df):
        """Simple RSI + EMA strategy"""
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Calculate EMA
        ema_20 = df['close'].ewm(span=20).mean()
        ema_50 = df['close'].ewm(span=50).mean()

        current_rsi = rsi.iloc[-1]
        current_price = df['close'].iloc[-1]
        current_ema_20 = ema_20.iloc[-1]
        current_ema_50 = ema_50.iloc[-1]

        # Simple signal logic
        if current_rsi < 30 and current_price > current_ema_20 > current_ema_50:
            return 'BUY'
        elif current_rsi > 70 and current_price < current_ema_20 < current_ema_50:
            return 'SELL'
        else:
            return 'HOLD'

# Slash commands
bot = TradingBot()

@bot.tree.command(name="start_trading", description="Bắt đầu auto trading")
async def start_trading(interaction: discord.Interaction):
    bot.is_trading = True
    await interaction.response.send_message("✅ Auto trading đã được kích hoạt!")

@bot.tree.command(name="stop_trading", description="Dừng auto trading")
async def stop_trading(interaction: discord.Interaction):
    bot.is_trading = False
    await interaction.response.send_message("⏹️ Auto trading đã được dừng!")

@bot.tree.command(name="analyze", description="Phân tích symbol cụ thể")
async def analyze(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer()

    try:
        # Fetch data
        ohlcv = bot.exchange.fetch_ohlcv(symbol.upper() + '/USDT', '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # Analyze
        signal = bot.analyze_market(df)

        # Create detailed embed
        embed = discord.Embed(
            title=f"📊 Phân Tích Kỹ Thuật: {symbol.upper()}/USDT",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        embed.add_field(name="🎯 Signal", value=signal, inline=True)
        embed.add_field(name="💰 Giá hiện tại", value=f"${df['close'].iloc[-1]:.4f}", inline=True)
        embed.add_field(name="📈 24h Change", value=f"{((df['close'].iloc[-1] / df['close'].iloc[-24] - 1) * 100):.2f}%", inline=True)

        # Calculate RSI for display
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        embed.add_field(name="📊 RSI (14)", value=f"{rsi.iloc[-1]:.2f}", inline=True)
        embed.add_field(name="📊 Volume", value=f"{df['volume'].iloc[-1]:,.0f}", inline=True)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi khi phân tích {symbol}: {str(e)}")

@bot.tree.command(name="portfolio", description="Xem portfolio hiện tại")
async def portfolio(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        # Fetch account balance (sandbox)
        balance = bot.exchange.fetch_balance()

        embed = discord.Embed(
            title="💼 Portfolio Overview",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )

        total_usd = 0
        for currency, amount in balance['total'].items():
            if amount > 0:
                embed.add_field(
                    name=f"{currency}",
                    value=f"{amount:.8f}",
                    inline=True
                )

        embed.add_field(name="📊 Total Value", value="Calculating...", inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Không thể lấy thông tin portfolio: {str(e)}")

@bot.tree.command(name="market", description="Xem thông tin thị trường")
async def market(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        tickers = bot.exchange.fetch_tickers(['BTC/USDT', 'ETH/USDT', 'BNB/USDT'])

        embed = discord.Embed(
            title="🏛️ Market Overview",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )

        for symbol, ticker in tickers.items():
            change_24h = ticker['percentage']
            color_emoji = "🟢" if change_24h > 0 else "🔴"

            embed.add_field(
                name=f"{color_emoji} {symbol}",
                value=f"${ticker['last']:.4f}
{change_24h:.2f}%",
                inline=True
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Không thể lấy thông tin thị trường: {str(e)}")

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
