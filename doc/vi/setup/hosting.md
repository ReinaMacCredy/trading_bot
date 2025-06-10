# Hướng Dẫn Hosting & Triển Khai

Hướng dẫn toàn diện để triển khai Professional Discord Trading Bot lên môi trường production. Hướng dẫn này bao gồm nhiều tùy chọn hosting từ setup VPS đơn giản đến triển khai cloud nâng cao.

## 🚀 Tùy Chọn Triển Khai Nhanh

### **Tùy Chọn 1: Triển Khai VPS (Khuyến Nghị cho Người Mới)**
- ✅ **Tiết Kiệm Chi Phí Nhất**: $5-20/tháng
- ✅ **Kiểm Soát Hoàn Toàn**: Truy cập server đầy đủ
- ✅ **Setup Đơn Giản**: Hướng dẫn từng bước bên dưới
- ⚠️ **Yêu Cầu**: Kiến thức Linux cơ bản

### **Tùy Chọn 2: Triển Khai Cloud Platform**
- ✅ **Khả Năng Scale Cao**: Tự động mở rộng
- ✅ **Tính Năng Chuyên Nghiệp**: Load balancing, monitoring
- ⚠️ **Chi Phí Cao Hơn**: $20-100+/tháng
- ⚠️ **Setup Phức Tạp**: Cần cấu hình nâng cao

### **Tùy Chọn 3: Triển Khai Docker**
- ✅ **Môi Trường Nhất Quán**: Chạy được ở mọi nơi có Docker
- ✅ **Cập Nhật Dễ Dàng**: Thay thế container đơn giản
- ✅ **Có Thể Scale**: Sẵn sàng cho Kubernetes
- ⚠️ **Yêu Cầu**: Kiến thức Docker

## 🖥️ Triển Khai VPS (DigitalOcean/Linode/Vultr)

### **Bước 1: Setup Server**

#### **Thông Số VPS Khuyến Nghị**
```
Yêu Cầu Tối Thiểu:
- 1 vCPU
- 1GB RAM
- 20GB SSD Storage
- Ubuntu 20.04/22.04 LTS

Khuyến Nghị cho Production:
- 2 vCPU
- 2GB RAM
- 40GB SSD Storage
- Ubuntu 22.04 LTS
```

#### **Cấu Hình Server Ban Đầu**
```bash
# Cập nhật system packages
sudo apt update && sudo apt upgrade -y

# Cài đặt Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Thêm user hiện tại vào group docker
sudo usermod -aG docker $USER

# Đăng xuất và đăng nhập lại, sau đó kiểm tra
docker --version
docker compose version
```

### **Bước 2: Cài Đặt Bot**

```bash
# Clone repository
git clone https://github.com/ReinaMacCredy/trading_bot.git
cd trading_bot

# Tạo thư mục cần thiết
mkdir -p logs data results
chmod 755 logs data results
```

### **Bước 3: Cấu Hình Environment**

```bash
# Copy template environment
cp config/env.example .env

# Chỉnh sửa cấu hình
nano .env
```

```env
# Cấu Hình Environment Production
ENVIRONMENT=production
DISCORD_TOKEN=your_production_discord_token

# Cấu Hình Exchange
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret
EXCHANGE_SANDBOX=false

# Cài Đặt Bảo Mật
LOG_LEVEL=INFO
MAX_RISK_PER_TRADE=0.01
MAX_DAILY_LOSS=0.03
ENABLE_PAPER_TRADING=false

# Cài Đặt Performance
CACHE_TTL=300
MAX_CONCURRENT_REQUESTS=10
```

### **Bước 4: Triển Khai với Docker Compose**

#### **Tùy Chọn 1: Sử Dụng VPS Optimized (Khuyến nghị cho VPS nhỏ)**

```bash
# Di chuyển đến thư mục deployment
cd deployment

# Triển khai với docker-compose
docker compose -f docker-compose.vps.yml up -d --build

# Kiểm tra trạng thái
docker compose -f docker-compose.vps.yml ps

# Xem logs
docker compose -f docker-compose.vps.yml logs -f tradingbot
```

#### **Tùy Chọn 2: Sử Dụng Production Stack (Khuyến nghị cho monitoring đầy đủ)**

```bash
# Di chuyển đến thư mục deployment
cd deployment

# Triển khai với production stack
docker compose -f docker-compose.prod.yml up -d

# Kiểm tra trạng thái
docker compose -f docker-compose.prod.yml ps
```

#### **Tùy Chọn 3: Sử Dụng Deployment Script (Tự động setup)**

```bash
# Di chuyển đến thư mục deployment
cd deployment

# Cấp quyền thực thi cho script
chmod +x vps-deployment.sh

# Chạy script cài đặt tự động
./vps-deployment.sh
```

Script sẽ:
- Kiểm tra yêu cầu hệ thống
- Cài đặt Docker nếu cần
- Thiết lập cấu hình môi trường
- Build và triển khai bot
- Cấu hình monitoring và systemd service

### **Bước 5: Thiết Lập Systemd Service (Tùy chọn)**

```bash
# Tạo systemd service
sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<EOF
[Unit]
Description=Discord Trading Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)/deployment
ExecStart=/usr/bin/docker compose -f docker-compose.vps.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.vps.yml down
TimeoutStartSec=0
User=$USER
Group=docker

[Install]
WantedBy=multi-user.target
EOF

# Kích hoạt và khởi động service
sudo systemctl daemon-reload
sudo systemctl enable trading-bot.service
sudo systemctl start trading-bot
```

## 📊 Monitoring và Quản Lý

### **Health Check**

Bot có sẵn endpoint kiểm tra sức khỏe:
```bash
curl http://localhost:8080/health
```

Kết quả mong đợi:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime": "2h 15m 30s",
  "version": "1.0.0"
}
```

### **Các Lệnh Quản Lý**

```bash
# Di chuyển đến thư mục deployment
cd deployment

# Khởi động bot
docker compose -f docker-compose.vps.yml up -d

# Dừng bot
docker compose -f docker-compose.vps.yml down

# Khởi động lại bot
docker compose -f docker-compose.vps.yml restart tradingbot

# Xem trạng thái
docker compose -f docker-compose.vps.yml ps

# Xem logs
docker compose -f docker-compose.vps.yml logs tradingbot
```

### **Quản Lý Logs**

Logs được tự động xoay vòng và lưu trữ trong:
- `logs/bot.log` - Logs chính của bot
- `logs/trading.log` - Logs hoạt động giao dịch
- `logs/errors.log` - Logs lỗi

Xem logs:
```bash
# Logs real-time
docker compose -f deployment/docker-compose.vps.yml logs -f tradingbot

# Logs gần đây
tail -f logs/bot.log

# Logs lỗi
tail -f logs/errors.log
```

## ☁️ Triển Khai Cloud Platform

### **Triển Khai Heroku**

Triển khai lên Heroku với nút "Deploy to Heroku" trong README hoặc:

```bash
# Đảm bảo bạn đã cài đặt Heroku CLI
heroku login

# Tạo ứng dụng
heroku create your-bot-name

# Thêm các add-ons
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev

# Đặt environment variables
heroku config:set DISCORD_TOKEN=your_discord_token
heroku config:set ENVIRONMENT=production
# Thêm các biến môi trường khác

# Triển khai
git push heroku main
```

### **Triển Khai AWS EC2**

```bash
# Di chuyển đến thư mục deployment
cd deployment

# Triển khai production stack
docker compose -f docker-compose.prod.yml up -d
```

## 🐛 Xử Lý Sự Cố

### **Vấn Đề Phổ Biến**

#### Bot Không Khởi Động
```bash
# Kiểm tra logs
cd deployment
docker compose -f docker-compose.vps.yml logs tradingbot

# Kiểm tra environment
cat .env

# Xác minh Discord token
curl -H "Authorization: Bot YOUR_TOKEN" https://discord.com/api/v10/users/@me
```

#### Vấn Đề Bộ Nhớ
```bash
# Kiểm tra sử dụng bộ nhớ
free -h
docker stats

# Khởi động lại với giới hạn bộ nhớ
cd deployment
docker compose -f docker-compose.vps.yml down
docker compose -f docker-compose.vps.yml up -d
```

#### Vấn Đề Ổ Đĩa
```bash
# Kiểm tra sử dụng ổ đĩa
df -h

# Dọn dẹp Docker
docker system prune -a

# Xóa logs
sudo truncate -s 0 logs/*.log
```

## 🔒 Bảo Mật

### **Bảo Mật Environment**
- Lưu trữ các bí mật trong file `.env` với quyền hạn chế:
```bash
chmod 600 .env
```

- Sử dụng biến môi trường, không bao giờ hardcode bí mật
- Thường xuyên thay đổi API keys
- Sử dụng chế độ sandbox cho testing

### **Bảo Mật Container**
- Chạy dưới quyền non-root (đã được cấu hình tự động)
- Sử dụng giới hạn tài nguyên cụ thể
- Giữ Docker và images cập nhật
- Giám sát logs bảo mật

### **Bảo Mật Mạng**
- Sử dụng quy tắc tường lửa:
```bash
sudo ufw allow ssh
sudo ufw allow 8080/tcp
sudo ufw enable
```

- Cân nhắc sử dụng reverse proxy (nginx)
- Bật fail2ban để bảo vệ SSH

## 📈 Tối Ưu Hóa Hiệu Suất

### **Giám Sát Tài Nguyên**
```bash
# Kiểm tra tài nguyên container
docker stats

# Kiểm tra tài nguyên hệ thống
htop
free -h
df -h
```

### **Mẹo Tối Ưu Hóa**
1. **Bộ Nhớ**: Tăng nếu bạn thấy lỗi OOM
2. **CPU**: Giám sát trong hoạt động giao dịch cao
3. **Ổ Đĩa**: Dọn dẹp thường xuyên và xoay vòng log
4. **Mạng**: Giám sát API rate limits

### **Tùy Chọn Mở Rộng**
- Mở rộng theo chiều dọc: Tăng tài nguyên VPS
- Mở rộng theo chiều ngang: Nhiều instances bot
- Mở rộng database: Chuyển sang PostgreSQL cho khối lượng cao

## 📞 Hỗ Trợ

### **Nhận Trợ Giúp**
- Kiểm tra logs trước: `docker compose -f deployment/docker-compose.vps.yml logs tradingbot`
- Sử dụng script giám sát: `./deployment/monitor_bot.sh status`
- Xem xét các vấn đề phổ biến ở trên
- Kiểm tra GitHub issues

### **Lệnh Hữu Ích**
```bash
# Kiểm tra sức khỏe nhanh
curl -s localhost:8080/health | jq '.'

# Kiểm tra container
docker inspect tradingbot

# Sử dụng tài nguyên
docker stats --no-stream

# Kiểm tra mạng
docker network ls
docker network inspect trading_bot_bot-network
```

----

## 🎉 Chúc Mừng!

Discord Trading Bot của bạn hiện đang chạy trên VPS! 

**Xác minh nhanh:**
1. Kiểm tra sức khỏe: `curl localhost:8080/health`
2. Giám sát trạng thái: `./deployment/monitor_bot.sh status`
3. Xem logs: `./deployment/monitor_bot.sh logs`
4. Kiểm tra lệnh Discord trong server của bạn

Để nhận hỗ trợ và cập nhật liên tục, hãy star repository và theo dõi các bản phát hành.

----

**Happy Trading! 📈🚀** 