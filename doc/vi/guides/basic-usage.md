# Hướng Dẫn Sử Dụng Cơ Bản

Hướng dẫn này sẽ giúp bạn bắt đầu với Professional Discord Trading Bot. Sau khi hoàn thành hướng dẫn cài đặt, bạn sẽ học cách sử dụng các tính năng và lệnh cơ bản.

## 🚀 Bắt Đầu

### Các Bước Đầu Tiên

1. **Xác minh Bot đang Online**: Kiểm tra bot hiển thị trực tuyến trong server Discord
2. **Test kết nối cơ bản**: Chạy `b!test_connection` để đảm bảo mọi thứ hoạt động
3. **Kiểm tra số dư**: Dùng `b!balance` để xác minh kết nối exchange (nếu đã cấu hình)

### Hiểu Hệ Thống Lệnh

Tất cả lệnh bắt đầu với prefix `b!` theo sau là tên lệnh và tham số.

```
Format: b!tên_lệnh tham_số_1 tham_số_2
Ví dụ: b!generate_signal BTC
```

## 📊 Signal Trading Đầu Tiên

Hãy tạo signal trading đầu tiên:

### Tạo Signal Cơ Bản

```discord
b!generate_signal BTC
```

Lệnh này sẽ:
- Phân tích dữ liệu thị trường Bitcoin hiện tại
- Áp dụng các chỉ báo kỹ thuật (MACD, RSI, EMA)
- Tạo signal chuyên nghiệp với điểm vào, cắt lỗ, và chốt lời
- Cung cấp điểm tin cậy

## 📊 Lịch Sử Đặt Lệnh & Phân Tích Lệnh

### Xem Lịch Sử Đặt Lệnh

Theo dõi tất cả hoạt động trading của bạn với lệnh lịch sử:

```discord
b!orders
```

Hiển thị:
- Các lệnh gần đây với timestamp
- Chi tiết lệnh (symbol, side, amount, price)
- Trạng thái và loại lệnh
- Định dạng embed đẹp mắt dễ đọc

### Phân Tích Sử Dụng Lệnh

Theo dõi các tính năng bot bạn sử dụng nhiều nhất:

```discord
b!actcmd      # Hiện lệnh bạn đã dùng
b!inactcmd    # Hiện lệnh bạn chưa dùng
b!cmdsta      # Tóm tắt trạng thái lệnh hoàn chỉnh
```

Các lệnh này giúp bạn:
- **Theo dõi patterns sử dụng bot**
- **Khám phá tính năng chưa sử dụng**
- **Monitor hoạt động lệnh**
- **Tối ưu workflow trading**

**Ví dụ Output:**
```
🎯 Lệnh Đã Sử Dụng
analyze, balance, chart, generate_signal, help, price

📋 Lệnh Chưa Sử Dụng
advanced_buy, backtest, optimize_params, position_size

📊 Tóm Tắt Trạng Thái Lệnh
Đã dùng: 6 lệnh | Chưa dùng: 4 lệnh
```

## ⚖️ Quản Lý Rủi Ro

### Thiết Lập Tham Số Rủi Ro

Cấu hình mức độ chấp nhận rủi ro:

```discord
b!risk_settings 2 5 1.5
```

Thiết lập:
- 2% rủi ro mỗi lệnh
- 5% tổn thất tối đa hàng ngày
- 1.5% trailing stop

## 💰 Trading Cơ Bản (Live Trading)

⚠️ **Quan trọng**: Chỉ sử dụng lệnh live trading nếu bạn đã:
- Cấu hình API keys exchange
- Test kỹ lưỡng với paper trading
- Thiết lập quản lý rủi ro phù hợp

### Kiểm Tra Giá Hiện Tại

```discord
b!price BTC
b!price ETHUSDT
```

### Xem Số Dư Tài Khoản

```discord
b!balance
```

## 🔧 Tính Năng Tối Ưu

### Tối Ưu Tham Số Cơ Bản

Tối ưu tham số strategy để hiệu suất tốt hơn:

```discord
b!optimize_params BTC 1h
```

### Tối Ưu Genetic Algorithm

Sử dụng thuật toán genetic để tìm tham số tối ưu:

```discord
b!genetic_optimize ETH 1h 20
```

## 🆘 Hỗ Trợ & Help

### Hệ Thống Help Chuyên Nghiệp

```discord
b!help
```

Hiển thị hệ thống help 2 trang với danh mục lệnh được tổ chức.

### Help Chỉ Báo

```discord
b!help_indicators
```

Hướng dẫn chi tiết về các chỉ báo kỹ thuật có sẵn.

## 💡 Tips Sử Dụng Hiệu Quả

### 1. Bắt Đầu Với Paper Trading
- Luôn test strategy với paper trading trước
- Sử dụng `ENABLE_PAPER_TRADING=true` trong environment

### 2. Thiết Lập Quản Lý Rủi Ro
- Đặt risk per trade thấp (1-2%)
- Sử dụng stop-loss cho mọi lệnh
- Không trade quá 5% tài khoản trong ngày

### 3. Sử Dụng Dual Timeframe
- Kết hợp nhiều timeframe để xác nhận signal
- Timeframe cao hơn cho trend chung
- Timeframe thấp hơn cho entry timing

### 4. Monitor Performance
- Theo dõi lịch sử lệnh thường xuyên
- Phân tích commands đã sử dụng
- Tối ưu strategy dựa trên kết quả

### 5. Giữ Log và Records
- Screenshot các signal quan trọng
- Ghi chú lý do vào/ra lệnh
- Review performance hàng tuần

## ⚠️ Lưu Ý An Toàn

1. **Không Chia Sẻ API Keys**: Giữ bí mật thông tin API
2. **Bắt Đầu Nhỏ**: Test với số tiền nhỏ trước
3. **Backup Configuration**: Lưu trữ cấu hình an toàn
4. **Monitor Bot 24/7**: Kiểm tra hoạt động thường xuyên
5. **Update Thường Xuyên**: Giữ bot version mới nhất

## 🔗 Tài Nguyên Bổ Sung

- [Installation Guide](../setup/installation.md)
- [API Reference](../api-reference/)
- [Troubleshooting](../troubleshooting/)
- [Advanced Features](advanced-usage.md) 