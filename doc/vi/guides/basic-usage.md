# Hướng Dẫn Sử Dụng Cơ Bản

Hướng dẫn này sẽ giúp bạn bắt đầu với Bot Giao Dịch Discord Chuyên Nghiệp. Sau khi làm theo hướng dẫn cài đặt, bạn sẽ học cách sử dụng các tính năng và lệnh thiết yếu.

## 🚀 Bắt Đầu

### Các Bước Đầu Tiên

1. **Xác Minh Bot Đang Online**: Kiểm tra bot hiển thị online trong Discord server của bạn
2. **Kiểm Tra Kết Nối Cơ Bản**: Chạy `b!test_connection` để đảm bảo mọi thứ hoạt động
3. **Kiểm Tra Số Dư**: Dùng `b!balance` để xác minh kết nối exchange (nếu đã cấu hình)

### Hiểu Hệ Thống Lệnh

Tất cả lệnh bắt đầu với tiền tố `b!` theo sau là tên lệnh và tham số.

```
Định dạng: b!tên_lệnh tham_số1 tham_số2
Ví dụ: b!generate_signal BTC
```

## 📊 Tín Hiệu Giao Dịch Đầu Tiên

Hãy tạo tín hiệu giao dịch đầu tiên của bạn:

### Tạo Tín Hiệu Cơ Bản

```discord
b!generate_signal BTC
```

Điều này sẽ:
- Phân tích dữ liệu thị trường hiện tại của Bitcoin
- Áp dụng các chỉ báo kỹ thuật (MACD, RSI, EMA)
- Tạo tín hiệu chuyên nghiệp với entry, stop-loss và take-profit
- Cung cấp điểm tin cậy

### Giải Thích Kết Quả Tín Hiệu

Một tín hiệu thông thường trông như thế này:

```
🎯 TÍN HIỆU GIAO DỊCH - BTC/USDT

📈 HƯỚNG: LONG
🎯 VÀO LỆNH: $60,500 - $60,800
🛑 CẮT LỖ: $58,200 (-3.8%)
💰 CHỐT LÃI: $63,400 (+4.5%)
📊 TIN CẬY: 78%

📋 PHÂN TÍCH:
• RSI (14): 32 - Quá bán
• MACD: Tín hiệu tăng
• EMA Trend: Hướng lên
• Volume: Trên trung bình

⚠️ Rủi ro: 2% danh mục
💡 Vị thế khuyến nghị: 0.025 BTC
```

### Hiểu Các Thành Phần Tín Hiệu

- **Hướng**: LONG (mua) hoặc SHORT (bán)
- **Vào Lệnh**: Khoảng giá để vào lệnh
- **Cắt Lỗ**: Mức lỗ tối đa (quản lý rủi ro)
- **Chốt Lãi**: Mức lợi nhuận mục tiêu
- **Tin Cậy**: Độ tin cậy thuật toán (0-100%)
- **Phân Tích**: Đọc chỉ báo kỹ thuật
- **Rủi Ro**: Phần trăm rủi ro đề xuất
- **Vị Thế**: Kích thước vị thế khuyến nghị

## 🔍 Lệnh Phân Tích Thị Trường

### Tín Hiệu Nhiều Thị Trường

Lấy tín hiệu cho top cryptocurrencies:

```discord
b!market_signals 5
```

Điều này tạo tín hiệu cho top 5 cryptocurrency theo vốn hóa thị trường.

### Phân Tích Chỉ Báo Cụ Thể

Phân tích từng chỉ báo riêng lẻ:

```discord
b!indicator rsi BTC 1h
b!indicator macd ETH 4h
```

### Phân Tích Dual Timeframe

Để có tín hiệu chính xác hơn, sử dụng phân tích dual timeframe:

```discord
b!dual_macd_rsi BTC 1h 4h
```

Điều này phân tích Bitcoin trên cả khung thời gian 1 giờ và 4 giờ để xác nhận tín hiệu.

## ⚖️ Quản Lý Rủi Ro

### Thiết Lập Tham Số Rủi Ro

Cấu hình khả năng chịu rủi ro của bạn:

```discord
b!risk_settings 2 5 1.5
```

Điều này thiết lập:
- 2% rủi ro mỗi giao dịch
- 5% lỗ tối đa hàng ngày
- 1.5% trailing stop

### Tính Toán Kích Thước Vị Thế

Tính toán kích thước vị thế tối ưu cho giao dịch:

```discord
b!position_size BTC 60000 58500
```

Tham số:
- Symbol: BTC
- Giá vào: $60,000
- Stop loss: $58,500

Bot sẽ tính toán số lượng chính xác để giao dịch dựa trên thiết lập rủi ro của bạn.

## 📈 Phân Tích Biểu Đồ

### Biểu Đồ Cơ Bản

Tạo biểu đồ giá với các chỉ báo:

```discord
b!chart BTC 4h 100
```

Điều này tạo biểu đồ Bitcoin 4 giờ với 100 nến cuối cùng.

### Biểu Đồ Chỉ Báo Cụ Thể

Xem biểu đồ tập trung vào chỉ báo cụ thể:

```discord
b!indicator_chart rsi BTC 4h
b!indicator_chart macd ETH 1h
```

### Biểu Đồ Chiến Lược

Xem hiệu suất chiến lược trực quan:

```discord
b!strategy_chart bollinger_bands BTC 4h
```

## 💰 Giao Dịch Cơ Bản (Live Trading)

⚠️ **Quan trọng**: Chỉ sử dụng lệnh live trading nếu bạn đã:
- Cấu hình API keys exchange
- Kiểm tra kỹ lưỡng với paper trading
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

### Lệnh Mua Nâng Cao

Đặt lệnh mua với stop-loss và take-profit tự động:

```discord
b!advanced_buy BTC 0.01 61500 58500
```

Tham số:
- Symbol: BTC
- Số lượng: 0.01 BTC
- Take profit: $61,500
- Stop loss: $58,500

## 🔧 Tính Năng Tối Ưu Hóa

### Tối Ưu Tham Số Cơ Bản

Tối ưu tham số chiến lược để có hiệu suất tốt hơn:

```discord
b!optimize_params BTC 1h
```

Điều này chạy tối ưu hóa grid search trên chiến lược mặc định.

### Phát Hiện Chế Độ Thị Trường

Hiểu điều kiện thị trường hiện tại:

```discord
b!market_regime BTC 4h
```

Điều này giúp điều chỉnh cách tiếp cận giao dịch theo điều kiện thị trường hiện tại.

## 📝 Thực Hành Tốt Nhất Cho Người Mới

### 1. Bắt Đầu Với Paper Trading

- Bật chế độ paper trading trong cấu hình
- Thực hành với tiền ảo trước khi rủi ro tiền thật
- Học cách tín hiệu hoạt động trong các điều kiện thị trường khác nhau

### 2. Sử dụng Thiết Lập Rủi Ro Thận Trọng

```discord
b!risk_settings 1 3 1.0
```

Bắt đầu với:
- 1% rủi ro mỗi giao dịch (thận trọng)
- 3% lỗ tối đa hàng ngày
- 1% trailing stop

### 3. Tập Trung Khung Thời Gian Cao

- Bắt đầu với khung thời gian 4h và hàng ngày
- Tránh scalping (1m, 5m) cho đến khi có kinh nghiệm
- Khung thời gian cao thường đáng tin cậy hơn

### 4. Đa Dạng Hóa Phân Tích

- Đừng dựa vào một tín hiệu duy nhất
- Sử dụng phân tích dual timeframe
- Kiểm tra nhiều chỉ báo
- Xem xét chế độ thị trường

### 5. Giám Sát Hiệu Suất

- Theo dõi các giao dịch của bạn
- Sử dụng tính năng theo dõi hiệu suất của bot
- Điều chỉnh chiến lược dựa trên kết quả

## 🔍 Hiểu Điều Kiện Thị Trường

### Thị Trường Theo Xu Hướng

Trong thị trường xu hướng (phát hiện bởi `b!market_regime`):
- Theo hướng xu hướng
- Sử dụng chỉ báo momentum (MACD)
- Đặt stop loss rộng hơn

### Thị Trường Sideway

Trong thị trường đi ngang:
- Sử dụng chiến lược mean reversion
- Tìm điều kiện oversold/overbought
- Sử dụng mục tiêu lãi chặt hơn

### Thị Trường Biến Động Cao

Trong biến động cao:
- Giảm kích thước vị thế
- Sử dụng stop rộng hơn
- Xem xét khung thời gian ngắn hơn

## 🚨 Lỗi Thường Gặp Của Người Mới

### 1. Bỏ Qua Quản Lý Rủi Ro
- **Vấn đề**: Giao dịch không có stop loss
- **Giải pháp**: Luôn đặt stop loss và kích thước vị thế

### 2. Giao Dịch Quá Nhiều
- **Vấn đề**: Lấy mọi tín hiệu
- **Giải pháp**: Chọn lọc, tập trung vào tín hiệu tin cậy cao

### 3. FOMO (Sợ Bỏ Lỡ)
- **Vấn đề**: Đuổi theo pump và vào muộn
- **Giải pháp**: Chờ điểm vào thích hợp

### 4. Giao Dịch Cảm Xúc
- **Vấn đề**: Để cảm xúc chi phối quyết định
- **Giải pháp**: Tuân thủ tín hiệu và quy tắc rủi ro của bot

### 5. Kiểm Tra Không Đủ
- **Vấn đề**: Live ngay mà không kiểm tra đúng
- **Giải pháp**: Paper trading và backtesting kỹ lưỡng

## 📞 Nhận Trợ Giúp

### Hệ Thống Trợ Giúp Tích Hợp

```discord
b!help
b!help generate_signal
```

### Trạng Thái và Thông Tin

```discord
b!status      # Trạng thái bot và hiệu suất
b!version     # Phiên bản bot hiện tại
```

### Vấn Đề Thường Gặp

Nếu lệnh không hoạt động:

1. **Kiểm tra quyền bot**: Đảm bảo bot có thể gửi tin nhắn và embed
2. **Xác minh kết nối API**: Sử dụng `b!test_connection`
3. **Kiểm tra cú pháp lệnh**: Dùng `b!help tên_lệnh`
4. **Xem logs**: Kiểm tra console output để tìm lỗi

## 🔄 Bước Tiếp Theo

Khi bạn đã quen với sử dụng cơ bản:

1. **[Hướng Dẫn Tín Hiệu Giao Dịch](trading-signals.md)** - Phân tích tín hiệu nâng cao
2. **[Quản Lý Rủi Ro](risk-management.md)** - Kỹ thuật rủi ro chuyên nghiệp
3. **[Tối Ưu Chiến Lược](strategy-optimization.md)** - Nâng cao hiệu suất
4. **[Tính Năng Nâng Cao](advanced-features.md)** - Chức năng cấp chuyên gia

## 💡 Mẹo Pro

### Lệnh Nhanh
- Dùng alias: `b!gs BTC` thay vì `b!generate_signal BTC`
- Chuỗi phân tích: Chạy nhiều chỉ báo để xác nhận
- Lưu thiết lập: Cấu hình một lần, tái sử dụng ở mọi nơi

### Mẹo Hiệu Quả
- Thiết lập channel giao dịch chuyên dụng
- Sử dụng thiết lập rủi ro theo channel
- Giám sát nhiều khung thời gian đồng thời

### Mẹo Hiệu Suất
- Xem lại tín hiệu trong các điều kiện thị trường khác nhau
- Theo dõi chiến lược nào hoạt động tốt nhất cho bạn
- Điều chỉnh tham số dựa trên dữ liệu hiệu suất

---

**Nhớ rằng**: Giao dịch có rủi ro. Luôn bắt đầu nhỏ, sử dụng quản lý rủi ro đúng cách, và không bao giờ giao dịch nhiều hơn bạn có thể chịu được. Bot là công cụ hỗ trợ giao dịch của bạn, không phải đảm bảo lợi nhuận.

*Sẵn sàng cho các tính năng nâng cao hơn? Xem [Hướng Dẫn Tính Năng Nâng Cao](advanced-features.md)!* 