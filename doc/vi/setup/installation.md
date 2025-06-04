# Hướng Dẫn Cài Đặt

Hướng dẫn này sẽ dẫn bạn qua quá trình cài đặt và thiết lập Bot Giao Dịch Discord Chuyên Nghiệp trên hệ thống của bạn.

## 📋 Yêu Cầu Trước Khi Bắt Đầu

Trước khi bắt đầu, hãy đảm bảo bạn có những thứ sau:

### Yêu Cầu Hệ Thống
- **Hệ Điều Hành**: Windows 10+, macOS 10.14+, hoặc Linux (Ubuntu 18.04+)
- **Python**: Phiên bản 3.9 trở lên
- **Bộ Nhớ**: Ít nhất 2GB RAM
- **Lưu Trữ**: 1GB dung lượng trống
- **Internet**: Kết nối internet ổn định cho dữ liệu giao dịch thời gian thực

### Tài Khoản Cần Thiết
- **Tài Khoản Discord Developer**: Để tạo và quản lý bot của bạn
- **Tài Khoản Sàn Giao Dịch**: Tài khoản Binance (khuyến nghị) hoặc sàn khác được hỗ trợ
- **Git**: Để clone repository (tuỳ chọn nhưng khuyến nghị)

## 🔧 Bước 1: Cài Đặt Python

### Windows
1. Tải Python từ [python.org](https://www.python.org/downloads/)
2. Chạy installer và **check "Add Python to PATH"**
3. Xác minh cài đặt:
   ```cmd
   python --version
   pip --version
   ```

### macOS
```bash
# Sử dụng Homebrew (khuyến nghị)
brew install python

# Hoặc tải từ python.org
# Xác minh cài đặt
python3 --version
pip3 --version
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
pip3 --version
```

## 📁 Bước 2: Tải Bot

### Tùy Chọn A: Clone với Git (Khuyến nghị)
```bash
git clone https://github.com/ReinaMacCredy/trading_bot.git
cd trading_bot
```

### Tùy Chọn B: Tải ZIP
1. Đi tới [GitHub repository](https://github.com/ReinaMacCredy/trading_bot)
2. Click "Code" → "Download ZIP"
3. Giải nén file ZIP
4. Navigate tới thư mục đã giải nén

## 🐍 Bước 3: Thiết Lập Virtual Environment

Tạo môi trường Python riêng biệt cho bot:

```bash
# Tạo virtual environment
python -m venv .venv

# Kích hoạt virtual environment
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

# Xác minh kích hoạt (bạn sẽ thấy (.venv) trong prompt)
```

## 📦 Bước 4: Cài Đặt Dependencies

Với virtual environment đã được kích hoạt:

```bash
# Cài đặt các package cần thiết
pip install -r requirements.txt

# Xác minh cài đặt
pip list
```

### Dependencies Thường Gặp Bao Gồm:
- `discord.py` - Discord API wrapper
- `ccxt` - Exchange API integration
- `pandas` - Data manipulation
- `pandas-ta` - Technical analysis indicators
- `pyyaml` - Configuration file parsing
- `python-dotenv` - Environment variable management

## 🤖 Bước 5: Tạo Discord Bot

### 1. Tạo Discord Application
1. Đi tới [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Nhập tên application (vd: "Trading Bot")
4. Click "Create"

### 2. Tạo Bot User
1. Đi tới section "Bot" ở sidebar bên trái
2. Click "Add Bot"
3. Tùy chỉnh username và avatar của bot
4. Copy **Bot Token** (giữ bí mật!)

### 3. Thiết Lập Bot Permissions
1. Đi tới "OAuth2" → "URL Generator"
2. Chọn scopes:
   - `bot`
   - `applications.commands`
3. Chọn permissions:
   - `Send Messages`
   - `Use Slash Commands`
   - `Embed Links`
   - `Attach Files`
   - `Read Message History`
4. Copy URL được tạo và sử dụng để mời bot vào server của bạn

## 🔑 Bước 6: Cấu Hình Environment Variables

### 1. Copy Environment Template
```bash
cp env.example .env
```

### 2. Chỉnh Sửa Cấu Hình
Mở file `.env` và thêm credentials của bạn:

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here

# Exchange API Configuration
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret_key
EXCHANGE_SANDBOX=true

# Trading Configuration
MAX_RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
ENABLE_PAPER_TRADING=true

# Environment Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Thiết Lập Exchange API

#### Binance (Khuyến nghị)
1. Đi tới [Binance](https://www.binance.com/) và tạo tài khoản
2. Bật 2FA để bảo mật
3. Đi tới API Management
4. Tạo API key mới với các permissions:
   - ✅ Read Info
   - ✅ Spot & Margin Trading (cho live trading)
   - ❌ Futures Trading (trừ khi cần)
   - ❌ Withdrawals (KHÔNG BAO GIỜ bật cho bot)
5. Thêm IP server của bạn vào whitelist
6. Copy API Key và Secret vào file `.env`

**Quan trọng**: Bắt đầu với chế độ testnet/sandbox (`EXCHANGE_SANDBOX=true`) để kiểm tra!

## ⚙️ Bước 7: Cấu Hình Bot Settings

### 1. Cấu Hình Chính
Chỉnh sửa `src/config/config.yml` cho các thiết lập nâng cao:

```yaml
# Trading Settings
trading:
  default_strategy: "MACD_RSI"
  risk_per_trade: 0.02
  max_positions: 5
  
# Technical Indicators
indicators:
  rsi:
    period: 14
    overbought: 70
    oversold: 30
  macd:
    fast: 12
    slow: 26
    signal: 9

# Risk Management
risk:
  max_daily_loss: 0.05
  stop_loss_percentage: 0.02
  take_profit_ratio: 2.5
```

### 2. Discord Settings
Cấu hình các thiết lập Discord cụ thể trong config file hoặc environment variables.

## 🚀 Bước 8: Kiểm Tra Cài Đặt

### 1. Xác Minh Cấu Hình
```bash
python main.py --check-config
```

### 2. Kiểm Tra Kết Nối Discord
```bash
python main.py --test-discord
```

### 3. Kiểm Tra Kết Nối Exchange
```bash
python main.py --test-exchange
```

### 4. Chạy Kiểm Tra Đầy Đủ
```bash
python main.py --test-all
```

## ▶️ Bước 9: Chạy Bot

### Chế Độ Development
```bash
python main.py
```

### Chế Độ Production
```bash
python main.py --environment production
```

### Chế Độ Background (Linux/macOS)
```bash
nohup python main.py > bot.log 2>&1 &
```

## ✅ Xác Minh

Sau khi khởi động bot, xác minh nó đang hoạt động:

1. **Discord Status**: Bot nên hiển thị online trong Discord server của bạn
2. **Log Output**: Kiểm tra console để xem có lỗi nào không
3. **Test Command**: Thử `b!test_connection` trong Discord
4. **Exchange Connection**: Xác minh API connection với `b!balance`

## 🔧 Khắc Phục Sự Cố

### Vấn Đề Thường Gặp

#### Bot Không Khởi Động
```bash
# Kiểm tra phiên bản Python
python --version

# Xác minh dependencies
pip install -r requirements.txt --upgrade

# Kiểm tra environment variables
python -c "import os; print(os.getenv('DISCORD_TOKEN'))"
```

#### Lỗi Permission
```bash
# Linux/macOS: Kiểm tra file permissions
chmod +x main.py

# Đảm bảo virtual environment được kích hoạt
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

#### Vấn Đề Kết Nối Exchange
- Xác minh API keys đúng
- Kiểm tra thiết lập IP whitelist
- Đảm bảo sandbox mode được bật để kiểm tra
- Xác minh exchange được hỗ trợ

#### Vấn Đề Kết Nối Discord
- Xác minh bot token đúng
- Kiểm tra bot permissions trong Discord server
- Đảm bảo bot được mời vào đúng server

### Nhận Trợ Giúp

Nếu bạn gặp vấn đề:

1. **Kiểm Tra Logs**: Xem console output để tìm thông báo lỗi
2. **Đọc Tài Liệu**: Kiểm tra các phần liên quan trong tài liệu này
3. **GitHub Issues**: Tìm kiếm issues hiện có hoặc tạo issue mới
4. **Discord Support**: Tham gia support server của chúng tôi

## 🔄 Bước Tiếp Theo

Sau khi cài đặt thành công:

1. **[Hướng Dẫn Cấu Hình](configuration.md)** - Tùy chỉnh thiết lập bot
2. **[Thiết Lập Bảo Mật](security.md)** - Bảo mật bot và API keys
3. **[Sử Dụng Cơ Bản](../guides/basic-usage.md)** - Học các lệnh thiết yếu
4. **[Tín Hiệu Giao Dịch](../guides/trading-signals.md)** - Hiểu việc tạo tín hiệu

## 🔒 Ghi Chú Bảo Mật

- **Không bao giờ chia sẻ bot token hoặc API keys**
- **Sử dụng environment variables cho dữ liệu nhạy cảm**
- **Bật 2FA trên tất cả tài khoản**
- **Bắt đầu với chế độ sandbox/testnet**
- **Thường xuyên cập nhật dependencies**
- **Giám sát hoạt động và logs của bot**

---

**Chúc mừng!** Bot Giao Dịch Discord của bạn đã được cài đặt và sẵn sàng sử dụng. Nhớ bắt đầu với paper trading và số tiền nhỏ khi chuyển sang live trading.

*Để triển khai production, xem [Hướng Dẫn Hosting](hosting.md) cho các tùy chọn triển khai VPS và cloud.* 