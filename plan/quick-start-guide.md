# Quick Start Guide - Discord Trading Bot

## 🚀 Bắt Đầu Ngay (15 phút)

### Bước 1: Clone Project và Setup Environment
```bash
# Tạo thư mục project
mkdir my-trading-bot
cd my-trading-bot

# Tạo virtual environment
python -m venv venv

# Kích hoạt environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies cơ bản
pip install discord.py python-dotenv ccxt pandas pandas-ta asyncio
```

### Bước 2: Tạo Discord Bot (5 phút)
1. Vào [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" → Nhập tên bot
3. Vào tab "Bot" → Click "Add Bot"
4. Copy Bot Token và lưu lại
5. Enable "Message Content Intent"
6. Vào "OAuth2 > URL Generator":
   - Chọn scope: `bot` và `applications.commands`
   - Chọn permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
7. Copy invite URL và add bot vào Discord server

### Bước 3: Setup API Keys
1. Tạo tài khoản [Binance Testnet](https://testnet.binance.vision/)
2. Tạo API key trên testnet (KHÔNG dùng mainnet)
3. Copy API Key và Secret

### Bước 4: Tạo File Environment
```bash
# Tạo file .env
DISCORD_TOKEN=paste_your_discord_token_here
BINANCE_API_KEY=paste_your_testnet_api_key
BINANCE_SECRET=paste_your_testnet_secret
ENVIRONMENT=development
```

### Bước 5: Chạy Bot
1. Download file `basic_trading_bot.py` đã được tạo
2. Chạy bot:
```bash
python basic_trading_bot.py
```

## 🎯 Các Lệnh Cơ Bản

Sau khi bot online, bạn có thể sử dụng các slash commands:

- `/analyze BTCUSDT` - Phân tích kỹ thuật cho Bitcoin
- `/market` - Xem tổng quan thị trường
- `/portfolio` - Xem portfolio (testnet)
- `/start_trading` - Bắt đầu auto monitoring
- `/stop_trading` - Dừng auto monitoring

## ⚡ Testing Bot

### Test 1: Kiểm tra kết nối
```bash
# Bot sẽ hiển thị trong Discord server
# Thử command: /analyze BTCUSDT
```

### Test 2: Kiểm tra API
```bash
# Thử command: /market
# Nếu hiển thị giá BTC, ETH, BNB → API hoạt động
```

### Test 3: Auto monitoring
```bash
# Tạo channel "trading-signals" trong Discord
# Chạy: /start_trading
# Bot sẽ gửi signal mỗi 5 phút
```

## 🔧 Troubleshooting

### Lỗi thường gặp:

**Bot không online:**
- Kiểm tra DISCORD_TOKEN trong .env
- Đảm bảo bot đã được invite vào server

**Không fetch được dữ liệu:**
- Kiểm tra BINANCE_API_KEY và SECRET
- Đảm bảo sử dụng testnet keys

**Commands không hoạt động:**
- Chờ vài phút sau khi bot online
- Thử restart bot

**Module not found:**
- Kiểm tra virtual environment đã được activate
- Chạy lại: `pip install -r requirements.txt`

### Debug mode:
```python
# Thêm vào cuối file basic_trading_bot.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Bước Tiếp Theo

Sau khi bot cơ bản hoạt động:

### Ngắn hạn (1-2 tuần):
1. **Cải thiện strategy** - Thêm RSI, MACD, EMA filters
2. **Risk management** - Implement stop-loss, position sizing
3. **Backtesting** - Test strategy với dữ liệu lịch sử
4. **Paper trading** - Simulate trades trước khi live

### Trung hạn (1 tháng):
1. **Database integration** - Lưu trade history và metrics
2. **Advanced indicators** - Bollinger Bands, Fibonacci, Support/Resistance
3. **Multi-timeframe analysis** - Combine 15m, 1h, 4h signals
4. **Portfolio management** - Multi-symbol trading

### Dài hạn (2-3 tháng):
1. **Machine Learning** - Optimize parameters với AI
2. **Sentiment analysis** - Tích hợp news và social sentiment
3. **Advanced deployment** - Docker, CI/CD, monitoring
4. **Live trading** - Chuyển từ testnet sang mainnet (thận trọng!)

## ⚠️ Cảnh Báo An Toàn

🔴 **QUAN TRỌNG:**
- Luôn test trên testnet/sandbox trước
- Không bao giờ share API keys
- Bắt đầu với số tiền nhỏ
- Set stop-loss và risk limits
- Monitor bot 24/7 khi live trading
- Backup code và data thường xuyên

🟡 **Lưu ý pháp lý:**
- Tuân thủ quy định trading tại địa phương
- Khai báo thuế đúng quy định
- Trading bot có rủi ro mất tiền
- Không investment advice

## 🆘 Support

Nếu gặp vấn đề:
1. Check logs trong terminal
2. Xem troubleshooting guide trên
3. Join Discord communities về trading bots
4. GitHub issues nếu có lỗi code

## 📖 Resources Hữu Ích

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [CCXT Documentation](https://docs.ccxt.com/)
- [Binance API Docs](https://binance-docs.github.io/apidocs/)
- [Technical Analysis Library](https://technical-analysis-library-in-python.readthedocs.io/)
- [Freqtrade](https://www.freqtrade.io/) - Advanced trading bot framework

Happy Trading! 🚀📈