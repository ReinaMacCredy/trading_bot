# Lộ Trình Phát Triển Discord Trading Bot

## Giai Đoạn 1: Thiết Lập Môi Trường (1-2 ngày)

### 1.1 Cài Đặt Python Environment
```bash
# Tạo thư mục project
mkdir discord-trading-bot
cd discord-trading-bot

# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

### 1.2 Tạo Cấu Trúc Project
```
discord-trading-bot/
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── commands/
│   │   ├── events/
│   │   └── utils/
│   ├── trading/
│   │   ├── __init__.py
│   │   ├── indicators.py
│   │   ├── strategies.py
│   │   ├── risk_manager.py
│   │   └── exchanges/
│   └── config/
│       ├── __init__.py
│       ├── settings.py
│       └── config.yml
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### 1.3 Tạo Requirements.txt
```txt
discord.py>=2.3.0
py-cord>=2.4.0
python-dotenv>=1.0.0
ccxt>=4.0.0
pandas>=2.0.0
pandas-ta>=0.3.14b
numpy>=1.24.0
asyncio-mqtt>=0.16.0
redis>=4.5.0
SQLAlchemy>=2.0.0
aiohttp>=3.8.0
PyYAML>=6.0
cryptography>=40.0.0
structlog>=23.0.0
psutil>=5.9.0
```

## Giai Đoạn 2: Tạo Discord Application (30 phút)

### 2.1 Tạo Discord Bot Application
1. Truy cập [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" và nhập tên bot
3. Vào tab "Bot" và click "Add Bot"
4. Copy Bot Token và lưu vào file `.env`
5. Enable "Message Content Intent" và "Server Members Intent"

### 2.2 Tạo Invite Link
1. Vào tab "OAuth2 > URL Generator"
2. Chọn scope "bot" và "applications.commands"
3. Chọn permissions cần thiết:
   - Send Messages
   - Embed Links
   - Attach Files
   - Use Slash Commands
4. Copy invite URL và thêm bot vào server test

### 2.3 Tạo File Environment
```bash
# .env
DISCORD_TOKEN=your_bot_token_here
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Giai Đoạn 3: Phát Triển Core Bot (3-5 ngày)

### 3.1 Basic Discord Bot Setup
```python
# src/bot/main.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

class TradingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
    async def on_ready(self):
        print(f'{self.user} đã online!')
        await self.tree.sync()

bot = TradingBot()

@bot.tree.command(name="health", description="Kiểm tra trạng thái bot")
async def health(interaction: discord.Interaction):
    await interaction.response.send_message("Bot đang hoạt động!")

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
```

### 3.2 Tạo Configuration System
```python
# src/config/settings.py
import yaml
import os
from dataclasses import dataclass

@dataclass
class TradingConfig:
    risk_percentage: float = 2.0
    max_positions: int = 5
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    ema_periods: list = None

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)
```

### 3.3 Tạo Indicators Module
```python
# src/trading/indicators.py
import pandas as pd
import pandas_ta as ta

class TechnicalIndicators:
    @staticmethod
    def calculate_rsi(df, period=14):
        return ta.rsi(df['close'], length=period)
    
    @staticmethod
    def calculate_macd(df, fast=12, slow=26, signal=9):
        macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
        return macd['MACD_12_26_9'], macd['MACDs_12_26_9'], macd['MACDh_12_26_9']
    
    @staticmethod
    def calculate_ema(df, periods):
        emas = {}
        for period in periods:
            emas[f'ema_{period}'] = ta.ema(df['close'], length=period)
        return emas
```

## Giai Đoạn 4: Tích Hợp Exchange API (2-3 ngày)

### 4.1 Exchange Connection
```python
# src/trading/exchanges/binance_client.py
import ccxt
import asyncio
from typing import Dict, List

class BinanceClient:
    def __init__(self, api_key: str, secret: str, sandbox: bool = True):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'sandbox': sandbox,
            'enableRateLimit': True,
        })
    
    async def get_market_data(self, symbol: str, timeframe: str = '1h', limit: int = 100):
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    async def place_order(self, symbol: str, side: str, amount: float, price: float = None):
        try:
            if price:
                order = await self.exchange.create_limit_order(symbol, side, amount, price)
            else:
                order = await self.exchange.create_market_order(symbol, side, amount)
            return order
        except Exception as e:
            print(f"Error placing order: {e}")
            return None
```

### 4.2 Strategy Implementation
```python
# src/trading/strategies.py
from .indicators import TechnicalIndicators
import pandas as pd

class MACDStrategy:
    def __init__(self, config):
        self.config = config
        self.indicators = TechnicalIndicators()
    
    def analyze(self, df: pd.DataFrame):
        # Calculate indicators
        rsi = self.indicators.calculate_rsi(df, self.config.rsi_period)
        macd_line, signal_line, histogram = self.indicators.calculate_macd(df)
        emas = self.indicators.calculate_ema(df, self.config.ema_periods)
        
        # Generate signals
        latest_idx = -1
        
        # Buy conditions
        buy_conditions = [
            rsi.iloc[latest_idx] > 30 and rsi.iloc[latest_idx] < 70,
            macd_line.iloc[latest_idx] > signal_line.iloc[latest_idx],
            df['close'].iloc[latest_idx] > emas['ema_50'].iloc[latest_idx],
        ]
        
        # Sell conditions
        sell_conditions = [
            rsi.iloc[latest_idx] > 70,
            macd_line.iloc[latest_idx] < signal_line.iloc[latest_idx],
            df['close'].iloc[latest_idx] < emas['ema_50'].iloc[latest_idx],
        ]
        
        if sum(buy_conditions) >= 2:
            return 'BUY'
        elif sum(sell_conditions) >= 2:
            return 'SELL'
        else:
            return 'HOLD'
```

## Giai Đoạn 5: Risk Management (1-2 ngày)

### 5.1 Risk Manager
```python
# src/trading/risk_manager.py
import pandas as pd

class RiskManager:
    def __init__(self, max_risk_per_trade=0.02, max_daily_loss=0.05):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.daily_pnl = 0
        self.open_positions = 0
    
    def calculate_position_size(self, account_balance, entry_price, stop_loss_price):
        risk_amount = account_balance * self.max_risk_per_trade
        price_difference = abs(entry_price - stop_loss_price)
        position_size = risk_amount / price_difference
        return position_size
    
    def can_trade(self):
        return (abs(self.daily_pnl) < self.max_daily_loss and 
                self.open_positions < 5)
```

## Giai Đoạn 6: Discord Commands (2-3 ngày)

### 6.1 Trading Commands
```python
# src/bot/commands/trading_commands.py
import discord
from discord.ext import commands
from discord import app_commands

class TradingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.strategy = MACDStrategy()
        self.exchange = BinanceClient()
    
    @app_commands.command(name="analyze", description="Phân tích kỹ thuật cho symbol")
    async def analyze(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer()
        
        # Fetch market data
        df = await self.exchange.get_market_data(symbol)
        if df is None:
            await interaction.followup.send("Không thể lấy dữ liệu thị trường")
            return
        
        # Analyze
        signal = self.strategy.analyze(df)
        
        # Create embed
        embed = discord.Embed(
            title=f"Phân Tích {symbol}",
            color=discord.Color.green() if signal == 'BUY' else discord.Color.red()
        )
        embed.add_field(name="Tín hiệu", value=signal, inline=True)
        embed.add_field(name="Giá hiện tại", value=f"{df['close'].iloc[-1]:.4f}", inline=True)
        
        await interaction.followup.send(embed=embed)
```

## Giai Đoạn 7: Testing và Debugging (2-3 ngày)

### 7.1 Unit Tests
```python
# tests/test_strategy.py
import unittest
import pandas as pd
from src.trading.strategies import MACDStrategy

class TestMACDStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = MACDStrategy()
        
    def test_analyze_with_sample_data(self):
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        df = pd.DataFrame({
            'close': range(100),
            'high': range(1, 101),
            'low': range(100),
            'open': range(100),
            'volume': [1000] * 100
        })
        
        signal = self.strategy.analyze(df)
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
```

### 7.2 Paper Trading Mode
```python
# src/trading/paper_trading.py
class PaperTrader:
    def __init__(self, initial_balance=10000):
        self.balance = initial_balance
        self.positions = {}
        self.trades = []
    
    def execute_trade(self, symbol, side, amount, price):
        trade = {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'timestamp': pd.Timestamp.now()
        }
        self.trades.append(trade)
        
        if side == 'BUY':
            self.balance -= amount * price
        else:
            self.balance += amount * price
        
        return trade
```

## Giai Đoạn 8: Deployment (1-2 ngày)

### 8.1 Docker Setup
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env ./

CMD ["python", "src/bot/main.py"]
```

### 8.2 VPS Deployment
```bash
# Deploy trên VPS
scp -r discord-trading-bot user@your-vps:/home/user/
ssh user@your-vps
cd discord-trading-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup python src/bot/main.py &
```

## Giai Đoạn 9: Monitoring và Optimization (Liên tục)

### 9.1 Logging System
```python
# src/utils/logger.py
import structlog
import logging

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

### 9.2 Performance Monitoring
```python
# src/utils/metrics.py
import psutil
import asyncio

class BotMetrics:
    def __init__(self):
        self.total_trades = 0
        self.successful_trades = 0
        self.total_pnl = 0
    
    async def get_system_metrics(self):
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'total_trades': self.total_trades,
            'win_rate': self.successful_trades / self.total_trades if self.total_trades > 0 else 0
        }
```

## Timeline Tổng Thể: 2-3 tuần

**Tuần 1:** Giai đoạn 1-4 (Setup environment, Discord bot, Core development, Exchange integration)
**Tuần 2:** Giai đoạn 5-7 (Risk management, Discord commands, Testing)
**Tuần 3:** Giai đoạn 8-9 (Deployment, Monitoring, Optimization)

## Lưu Ý Quan Trọng

1. **Bắt đầu với Paper Trading** - Không bao giờ trade với tiền thật cho đến khi đã test kỹ càng
2. **Security First** - Luôn bảo vệ API keys và không commit vào Git
3. **Start Simple** - Bắt đầu với strategy đơn giản trước khi phức tạp hóa
4. **Monitor Continuously** - Thiết lập alerts và logging từ đầu
5. **Backup Strategy** - Luôn có plan B khi bot gặp sự cố

## Resources Tham Khảo

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [CCXT Documentation](https://ccxt.readthedocs.io/)
- [Pandas-TA Documentation](https://github.com/twopirllc/pandas-ta)
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)