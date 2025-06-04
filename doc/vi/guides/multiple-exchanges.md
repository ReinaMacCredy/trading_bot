# Hỗ Trợ Đa Sàn Giao Dịch

## Tổng Quan

Discord Trading Bot hỗ trợ giao dịch trên nhiều sàn giao dịch đồng thời, bao gồm:

### 🪙 Sàn Giao Dịch Tiền Điện Tử
- **Binance** - Sàn chính cho crypto
- **MEXC Global (MEXV)** - Sàn phụ cho altcoin
- **Coinbase** - Sàn lớn tại Mỹ
- **Kraken** - Sàn uy tín châu Âu
- **Bybit** - Sàn derivatives

### 💱 Sàn Giao Dịch Forex/CFD
- **MetaTrader 5 (MT5)** - Forex và CFD chuyên nghiệp

## Cài Đặt và Cấu Hình

### 1. Cấu Hình API Keys

Tạo file `.env` và thêm API keys cho các sàn:

```env
# Binance
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret
BINANCE_SANDBOX=true

# MEXC 
MEXC_API_KEY=your_mexc_api_key
MEXC_SECRET=your_mexc_secret
MEXC_SANDBOX=true

# MT5 (MetaTrader 5)
MT5_ENABLED=true
MT5_LOGIN=your_mt5_account_number
MT5_PASSWORD=your_mt5_password
MT5_SERVER=MetaQuotes-Demo
MT5_PATH="C:\Program Files\MetaTrader 5\terminal64.exe"

# Coinbase (Tùy chọn)
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_SECRET=your_coinbase_secret
COINBASE_PASSPHRASE=your_coinbase_passphrase

# Kraken (Tùy chọn)
KRAKEN_API_KEY=your_kraken_api_key
KRAKEN_SECRET=your_kraken_secret

# Bybit (Tùy chọn)
BYBIT_API_KEY=your_bybit_api_key
BYBIT_SECRET=your_bybit_secret
```

### 2. Cài Đặt MetaTrader 5

Để sử dụng MT5:

1. **Tải và cài đặt MT5**: Từ MetaQuotes website
2. **Cài package Python**: `pip install MetaTrader5`
3. **Tạo tài khoản demo**: Hoặc sử dụng tài khoản thật
4. **Cấu hình đường dẫn**: Trong file `.env`

### 3. Cập Nhật Dependencies

```bash
pip install -r requirements.txt
```

## Lệnh Discord Mới

### 📊 Kiểm Tra Trạng Thái Sàn

```
b!exchanges
b!exch
b!ex
```

Hiển thị trạng thái kết nối của tất cả sàn giao dịch:
- 🟢 Đã kết nối
- 🔴 Chưa kết nối  
- ✅ Đã bật
- ❌ Đã tắt

### 💰 So Sánh Giá Đa Sàn

```
b!multiprice BTCUSDT
b!mprice EURUSD binance
b!mp ETHUSDT
```

**Tính năng:**
- So sánh giá từ tất cả sàn có sẵn
- Tính spread giữa các sàn
- Tự động chọn sàn phù hợp với symbol
- Có thể chỉ định sàn cụ thể

### 💳 Xem Số Dư Tài Khoản

```
b!balances
b!bal binance
b!balance mt5
```

**Hiển thị:**
- Số dư từ tất cả sàn (nếu không chỉ định)
- Số dư crypto (Binance, MEXC, v.v.)
- Số dư forex (MT5)
- Tổng quan tài khoản

### 🧪 Test Kết Nối

```
b!testconn
b!test
```

Kiểm tra kết nối đến tất cả sàn và báo cáo trạng thái.

## Chức Năng Tự Động

### 🎯 Tự Động Chọn Sàn

Bot tự động chọn sàn phù hợp dựa trên symbol:

**Tiền điện tử** (chứa USDT, BTC, ETH, etc.):
```
BTCUSDT → Binance (ưu tiên) hoặc MEXC
ETHUSDT → Binance (ưu tiên) hoặc MEXC
ADAUSDT → Binance (ưu tiên) hoặc MEXC
```

**Forex** (các cặp tiền tệ):
```
EURUSD → MT5
GBPUSD → MT5
USDJPY → MT5
```

### 🔄 Failover Tự Động

Nếu sàn chính không khả dụng:
1. Tự động chuyển sang sàn phụ
2. Thông báo lỗi cho người dùng
3. Tiếp tục hoạt động bình thường

### ⚡ Xử Lý Đồng Thời

- Lấy dữ liệu từ nhiều sàn song song
- Timeout thông minh cho từng sàn
- Không bị ảnh hưởng bởi sàn chậm

## Ví Dụ Sử Dụng

### 1. So Sánh Giá Bitcoin

```
b!multiprice BTCUSDT
```

**Kết quả:**
```
💰 BTCUSDT Multi-Exchange Prices
Prices from 3 exchanges

💵 BINANCE: $43,250.50 🟢 +2.5%
💵 MEXC: $43,245.20 🟢 +2.4%  
💵 COINBASE: $43,260.80 🟢 +2.6%

📊 Price Analysis
Spread: $15.60 (0.036%)
Lowest: MEXC
Highest: COINBASE
```

### 2. Xem Giá Forex từ MT5

```
b!multiprice EURUSD mt5
```

**Kết quả:**
```
💰 EURUSD Price - MT5

💵 Current Price: $1.0850
📈 Bid/Ask: Bid: $1.0849 Ask: $1.0851
📊 Volume: 150,420.50

Exchange: MT5 • 14:30:25 UTC
```

### 3. Kiểm Tra Số Dư Tất Cả Sàn

```
b!balances
```

**Kết quả:**
```
💰 Account Balances
Multi-Exchange Account Overview

🪙 BINANCE
BTC: 0.0250
ETH: 1.5000
USDT: 5,000.00

💱 MT5
Balance: 10,000.00 USD
Equity: 10,250.50
Free Margin: 8,500.00
Profit: +250.50
```

## Cấu Hình Nâng Cao

### Tùy Chỉnh Ưu Tiên Sàn

Trong file `.env`:

```env
# Thứ tự ưu tiên sàn crypto
PREFERRED_EXCHANGE_ORDER=binance,mexc,coinbase,kraken

# Sàn mặc định
DEFAULT_CRYPTO_EXCHANGE=binance
DEFAULT_FOREX_EXCHANGE=mt5

# Bật/tắt tự động chọn sàn
AUTO_EXCHANGE_SELECTION=true
```

### Monitoring và Alert

```env
# Kiểm tra sức khỏe sàn (giây)
HEALTH_CHECK_INTERVAL=300

# Cảnh báo khi mất kết nối
ALERT_ON_CONNECTION_LOSS=true

# Bật failover tự động
EXCHANGE_FAILOVER_ENABLED=true
```

## Troubleshooting

### ❌ Lỗi Thường Gặp

**1. "MT5 not connected"**
```
Giải pháp:
- Kiểm tra MT5 đã được cài đặt
- Xác nhận tài khoản MT5 đúng
- Kiểm tra MT5_ENABLED=true trong .env
```

**2. "No API key configured"**
```
Giải pháp:
- Thêm API key vào file .env
- Restart bot sau khi cập nhật .env
- Kiểm tra quyền API key
```

**3. "Exchange not available"**
```
Giải pháp:
- Chạy b!testconn để kiểm tra kết nối
- Kiểm tra internet connection
- Xác nhận API key còn hiệu lực
```

### 🔧 Debug Mode

Bật debug để xem chi tiết:

```env
LOG_LEVEL=DEBUG
DEBUG=true
```

### 📊 Performance Tips

1. **Giới hạn số lượng sàn**: Chỉ bật những sàn cần thiết
2. **Sử dụng sandbox**: Để test trước khi production
3. **Monitor rate limits**: Tránh spam API calls
4. **Cache dữ liệu**: Sử dụng cache cho dữ liệu ít thay đổi

## Security Best Practices

### 🔐 Bảo Mật API Keys

1. **Quyền tối thiểu**: Chỉ cấp quyền đọc nếu không trade
2. **IP Whitelist**: Giới hạn IP có thể sử dụng API
3. **Regular rotation**: Thay đổi API key định kỳ
4. **Environment variables**: Không hardcode trong code

### 🛡️ Risk Management

1. **Sandbox mode**: Test trước khi dùng tiền thật
2. **Position limits**: Đặt giới hạn size giao dịch
3. **Stop loss**: Luôn đặt stop loss
4. **Monitor positions**: Theo dõi thường xuyên

## Tương Lai

### 🚀 Tính Năng Sắp Tới

- **Arbitrage Detection**: Phát hiện cơ hội chênh lệch giá
- **Cross-Exchange Orders**: Đặt lệnh trên nhiều sàn
- **Portfolio Management**: Quản lý danh mục đa sàn
- **Advanced Analytics**: Phân tích deep hơn

### 📈 Roadmap

**Q1 2024:**
- Advanced order routing
- Real-time spread monitoring
- Cross-exchange risk management

**Q2 2024:**
- Arbitrage trading automation  
- Multi-exchange backtesting
- Portfolio optimization

## Hỗ Trợ

Nếu gặp vấn đề:

1. **Check logs**: Xem file log để biết lỗi cụ thể
2. **Test connections**: Dùng `b!testconn`
3. **Verify config**: Kiểm tra file `.env`
4. **Contact support**: Liên hệ team phát triển

---

> 💡 **Lưu ý**: Multi-exchange support là tính năng nâng cao. Hãy test kỹ trước khi sử dụng với tiền thật! 