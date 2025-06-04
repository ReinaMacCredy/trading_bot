# Lệnh Slash Discord

Discord Trading Bot hiện đã hỗ trợ các lệnh slash hiện đại cùng với các lệnh prefix truyền thống. Lệnh slash cung cấp trải nghiệm người dùng trực quan và thân thiện hơn với tính năng tự động hoàn thành và xác thực tham số.

## Các Lệnh Slash Có Sẵn

### `/price <symbol> [exchange]`
Lấy giá cryptocurrency theo thời gian thực với dữ liệu thị trường.

**Tham số:**
- `symbol` (bắt buộc): Ký hiệu cryptocurrency (ví dụ: BTC, ETH, ADA)
- `exchange` (tùy chọn): Sàn giao dịch để truy vấn (binance, coinbase, kraken, bybit) - mặc định: binance

**Ví dụ:**
```
/price symbol:BTC exchange:binance
```

**Tính năng:**
- Dữ liệu giá theo thời gian thực
- Phần trăm thay đổi 24 giờ
- Giá cao/thấp nhất 24 giờ
- Thông tin sàn giao dịch
- Định dạng embed chuyên nghiệp

### `/signal <symbol> [strategy] [timeframe]`
Tạo tín hiệu giao dịch chuyên nghiệp với các tham số có thể tùy chỉnh.

**Tham số:**
- `symbol` (bắt buộc): Ký hiệu cryptocurrency (ví dụ: BTC, ETH)
- `strategy` (tùy chọn): Chiến lược giao dịch (SC01, SC02, SC02+FRVP) - mặc định: SC01
- `timeframe` (tùy chọn): Khung thời gian phân tích (1h, 4h, 1d) - mặc định: 1h

**Ví dụ:**
```
/signal symbol:ETH strategy:SC02 timeframe:4h
```

**Tính năng:**
- Định dạng tín hiệu chuyên nghiệp
- Giá vào lệnh, chốt lời và cắt lỗ
- Tính toán tỷ lệ risk/reward
- Lựa chọn chiến lược và khung thời gian
- Tích hợp dữ liệu thị trường theo thời gian thực

### `/stats`
Hiển thị thống kê bot toàn diện và trạng thái hệ thống.

**Ví dụ:**
```
/stats
```

**Tính năng:**
- Thông tin thời gian hoạt động bot
- Số lượng server và người dùng
- Bộ đếm lệnh đã thực hiện
- Thống kê lỗi
- Trạng thái kết nối sàn giao dịch
- Thời gian heartbeat cuối cùng

### `/help`
Hệ thống trợ giúp hiện đại hiển thị các lệnh và tính năng có sẵn.

**Ví dụ:**
```
/help
```

**Tính năng:**
- Tham khảo lệnh hoàn chỉnh
- Danh sách lệnh slash và prefix
- Mô tả tính năng
- Danh sách sàn giao dịch được hỗ trợ
- Ví dụ sử dụng

## Thiết Lập Lệnh Slash

### Đồng Bộ Tự Động
Lệnh slash được đồng bộ tự động khi bot khởi động. Quá trình này đăng ký tất cả lệnh với Discord.

### Đồng Bộ Thủ Công
Quản trị viên có thể đồng bộ lệnh thủ công bằng lệnh prefix:

```
b!sync [guild_id]
```

**Tham số:**
- `guild_id` (tùy chọn): Đồng bộ với server cụ thể (nhanh hơn) hoặc toàn cầu (chậm hơn)

**Ví dụ:**
```
b!sync                    # Đồng bộ toàn cầu (mất tới 1 giờ)
b!sync 123456789012345678 # Đồng bộ server cụ thể (ngay lập tức)
```

## Tính Năng Lệnh

### Tích Hợp Discord Hiện Đại
- **Tự động hoàn thành**: Tham số hiển thị gợi ý khi bạn gõ
- **Xác thực**: Discord xác thực tham số trước khi gửi
- **Mô tả**: Mỗi lệnh và tham số đều có mô tả hữu ích
- **Xử lý lỗi**: Thông báo lỗi thân thiện với người dùng
- **Phản hồi hoãn**: Xử lý thích hợp thời gian xử lý

### Định Dạng Chuyên Nghiệp
- **Rich Embeds**: Định dạng đẹp mắt với màu sắc và biểu tượng
- **Timestamps**: Tất cả phản hồi bao gồm thời gian tạo
- **Phong cách nhất quán**: Phù hợp với ngôn ngữ thiết kế bot hiện có
- **Chỉ báo trạng thái**: Phản hồi trực quan cho các trạng thái khác nhau

### Tích Hợp Với Hệ Thống Hiện Có
- **Exchange Client**: Tích hợp đầy đủ với hệ thống giao dịch
- **Quản lý rủi ro**: Tính toán rủi ro giống như lệnh prefix
- **Xử lý lỗi**: Xử lý lỗi nhất quán trên các loại lệnh
- **Logging**: Tích hợp logging đầy đủ để debug

## So Sánh Lệnh

| Tính năng | Lệnh Prefix | Lệnh Slash |
|-----------|-------------|------------|
| Dễ sử dụng | Gõ thủ công | Tự động hoàn thành |
| Xác thực tham số | Runtime | Pre-validation |
| Khám phá | Lệnh help | Giao diện Discord |
| Trải nghiệm mobile | Tiêu chuẩn | Nâng cao |
| Ngăn chặn lỗi | Runtime errors | Type validation |

## Thực Hành Tốt Nhất

### Cho Người Dùng
1. **Sử dụng lệnh slash** để có trải nghiệm tốt hơn và ít lỗi đánh máy
2. **Thử tự động hoàn thành** bằng cách gõ `/` và chọn lệnh
3. **Kiểm tra mô tả tham số** nếu không chắc chắn về đầu vào
4. **Sử dụng lệnh prefix** cho các thao tác phức tạp hoặc nâng cao

### Cho Quản Trị Viên
1. **Đồng bộ lệnh sau khi cập nhật** bằng `b!sync`
2. **Sử dụng đồng bộ server cụ thể** để kiểm thử (nhanh hơn)
3. **Theo dõi logs** để phát hiện vấn đề đồng bộ
4. **Đồng bộ toàn cầu** cho triển khai production

## Khắc Phục Sự Cố

### Lệnh Không Xuất Hiện
1. Kiểm tra quyền bot trong cài đặt server
2. Đảm bảo bot có quyền "Use Slash Commands"
3. Thử đồng bộ thủ công: `b!sync [guild_id]`
4. Đợi tới 1 giờ cho đồng bộ toàn cầu

### Vấn Đề Quyền
- Bot cần quyền "Use Slash Commands"
- Lệnh có thể bị hạn chế bởi cài đặt server
- Kiểm tra cài đặt tích hợp Discord server

### Lỗi Đồng Bộ
- Xác minh token bot hợp lệ
- Kiểm tra kết nối mạng
- Xem lại logs bot để biết chi tiết lỗi
- Thử đồng bộ server cụ thể trước

## Chi Tiết Kỹ Thuật

### Triển Khai
- Xây dựng bằng `discord.app_commands`
- Xác thực kiểu tự động
- Mẫu phản hồi hoãn cho các thao tác dài
- Xử lý lỗi với thông báo ephemeral

### Hiệu Suất
- Lệnh đồng bộ tự động khi khởi động
- Đồng bộ server cụ thể: ngay lập tức
- Đồng bộ toàn cầu: tới 1 giờ
- Thời gian phản hồi: dưới giây cho hầu hết thao tác

## Hướng Dẫn Sử Dụng

### Cách Sử Dụng Lệnh Slash
1. **Gõ `/`** trong Discord để mở menu lệnh slash
2. **Chọn lệnh** từ danh sách hoặc tiếp tục gõ để lọc
3. **Điền tham số** - Discord sẽ hiển thị gợi ý và xác thực
4. **Nhấn Enter** để thực hiện lệnh

### Ví Dụ Cụ Thể
```
/price symbol:BTC          # Lấy giá Bitcoin từ Binance
/price symbol:ETH exchange:coinbase  # Lấy giá Ethereum từ Coinbase
/signal symbol:BTC strategy:SC02     # Tạo tín hiệu BTC với chiến lược SC02
/stats                     # Xem thống kê bot
/help                      # Xem trợ giúp đầy đủ
```

### Mẹo Sử Dụng
- **Tự động hoàn thành**: Bắt đầu gõ tên coin, Discord sẽ gợi ý
- **Tham số tùy chọn**: Có thể bỏ qua các tham số không bắt buộc
- **Kiểm tra lỗi**: Nếu có lỗi, thông báo sẽ chỉ hiển thị cho bạn
- **Trải nghiệm mobile**: Lệnh slash hoạt động tốt hơn trên điện thoại

## Tương Lai

### Tính Năng Sắp Tới
- Thêm nhiều lệnh slash cho các tính năng nâng cao
- Tích hợp với hệ thống portfolio
- Lệnh slash cho quản lý rủi ro
- Tính năng đăng ký alerts

### Cải Tiến
- Tối ưu hóa hiệu suất đồng bộ
- Thêm tham số động dựa trên context
- Tích hợp với AI để gợi ý thông minh
- Hỗ trợ localization cho nhiều ngôn ngữ 