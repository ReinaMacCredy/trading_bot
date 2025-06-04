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

# Cài đặt packages cần thiết
sudo apt install -y python3 python3-pip python3-venv git screen nginx certbot python3-certbot-nginx

# Tạo user cho bot
sudo adduser --disabled-password --gecos "" tradingbot
sudo usermod -aG sudo tradingbot

# Chuyển sang bot user
sudo su - tradingbot
```

### **Bước 2: Cài Đặt Bot**

```bash
# Clone repository
git clone https://github.com/ReinaMacCredy/trading_bot.git
cd trading_bot

# Tạo và kích hoạt virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Tạo file environment production
cp env.example .env
nano .env  # Cấu hình environment variables
```

### **Bước 3: Cấu Hình Environment**

```env
# Cấu Hình Environment Production
ENVIRONMENT=production
DISCORD_TOKEN=your_production_discord_token

# Cấu Hình Exchange
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret
EXCHANGE_SANDBOX=false

# Cấu Hình Database (PostgreSQL khuyến nghị cho production)
DATABASE_URL=postgresql://tradingbot:secure_password@localhost:5432/trading_bot_prod

# Cài Đặt Bảo Mật
LOG_LEVEL=INFO
MAX_RISK_PER_TRADE=0.01
MAX_DAILY_LOSS=0.03
ENABLE_PAPER_TRADING=false

# Cài Đặt Performance
CACHE_TTL=300
MAX_CONCURRENT_REQUESTS=10
```

### **Bước 4: Setup Database (PostgreSQL)**

```bash
# Cài đặt PostgreSQL
sudo apt install postgresql postgresql-contrib

# Tạo database và user
sudo -u postgres psql
CREATE DATABASE trading_bot_prod;
CREATE USER tradingbot WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE trading_bot_prod TO tradingbot;
\q

# Test kết nối database
psql -h localhost -U tradingbot -d trading_bot_prod
```

### **Bước 5: Quản Lý Process với Systemd**

Tạo file systemd service:

```bash
sudo nano /etc/systemd/system/tradingbot.service
```

```ini
[Unit]
Description=Professional Discord Trading Bot
After=network.target postgresql.service

[Service]
Type=simple
User=cfp
WorkingDirectory=/home/cfp/trading_bot
Environment=PATH=/home/cfp/trading_bot/venv/bin
ExecStart=/home/cfp/trading_bot/venv/bin/python main.py
Restart=always
RestartSec=10

# Cài đặt bảo mật
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/home/cfp/trading_bot

[Install]
WantedBy=multi-user.target
```

```bash
# Kích hoạt và start service
sudo systemctl enable tradingbot
sudo systemctl start tradingbot

# Kiểm tra status
sudo systemctl status tradingbot

# Xem logs
sudo journalctl -u tradingbot -f
```

## ☁️ Triển Khai Cloud Platform

### **Triển Khai AWS**

#### **Sử Dụng AWS EC2**

```yaml
# docker-compose.yml cho AWS
version: '3.8'

services:
  tradingbot:
    build: .
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - DISCORD_TOKEN=${DISCORD_TOKEN}
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - bot-network

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: trading_bot_prod
      POSTGRES_USER: tradingbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - bot-network

  redis:
    image: redis:7-alpine
    networks:
      - bot-network

volumes:
  postgres_data:

networks:
  bot-network:
    driver: bridge
```

### **Google Cloud Platform (GCP)**

#### **Sử Dụng Google Compute Engine**

```bash
# Cài đặt gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Tạo VM instance
gcloud compute instances create trading-bot-vm \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=40GB \
    --tags=trading-bot

# SSH vào instance
gcloud compute ssh trading-bot-vm --zone=us-central1-a
```

## 🐳 Triển Khai Docker

### **Setup Docker Cơ Bản**

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Cài đặt system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Tạo non-root user
RUN useradd --create-home --shell /bin/bash tradingbot
USER tradingbot

# Copy requirements và cài đặt dependencies
COPY --chown=tradingbot:tradingbot requirements.txt .
RUN pip install --user -r requirements.txt

# Copy application code
COPY --chown=tradingbot:tradingbot . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/home/tradingbot/.local/bin:${PATH}"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Start bot
CMD ["python", "main.py"]
```

### **Docker Compose cho Development**

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  tradingbot:
    build: .
    volumes:
      - .:/app
      - ./logs:/app/logs
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://tradingbot:password@postgres:5432/trading_bot_dev
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: trading_bot_dev
      POSTGRES_USER: tradingbot
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  adminer:
    image: adminer
    ports:
      - "8080:8080"

volumes:
  postgres_dev_data:
```

## 🎯 Triển Khai Heroku

### **Bước 1: Setup Heroku**

```bash
# Cài đặt Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Đăng nhập Heroku
heroku login

# Tạo Heroku app
heroku create your-trading-bot-name

# Set environment variables
heroku config:set ENVIRONMENT=production
heroku config:set DISCORD_TOKEN=your_discord_token
heroku config:set BINANCE_API_KEY=your_api_key
heroku config:set BINANCE_SECRET=your_secret
```

### **Bước 2: File Cấu Hình Heroku**

```
# Procfile
worker: python main.py
```

```python
# runtime.txt
python-3.11.6
```

### **Bước 3: Deploy lên Heroku**

```bash
# Thêm PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Thêm Redis addon
heroku addons:create heroku-redis:mini

# Deploy bot
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Scale worker
heroku ps:scale worker=1

# Xem logs
heroku logs --tail
```

## 🔧 Setup Production Nâng Cao

### **Monitoring & Logging**

#### **Setup Prometheus & Grafana**

```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

### **Cấu Hình SSL/TLS**

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream tradingbot {
        server tradingbot:8080;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/ssl/fullchain.pem;
        ssl_certificate_key /etc/ssl/privkey.pem;

        location / {
            proxy_pass http://tradingbot;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## 🚨 Best Practices Bảo Mật

### **Bảo Mật Environment**

```bash
# Cài đặt file permissions bảo mật
chmod 600 .env
chmod 700 ~/.ssh
chmod 644 ~/.ssh/authorized_keys

# Cấu hình firewall
sudo ufw allow ssh
sudo ufw allow 443
sudo ufw enable

# Fail2ban cho SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

## 🔍 Troubleshooting

### **Vấn Đề Thường Gặp**

#### **Vấn Đề Memory**
```bash
# Kiểm tra memory usage
free -h
htop

# Tối ưu Python memory
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

#### **Vấn Đề Kết Nối Database**
```bash
# Kiểm tra PostgreSQL status
sudo systemctl status postgresql

# Test database connection
psql -h localhost -U tradingbot -d trading_bot_prod
```

### **Phân Tích Logs**

```bash
# Xem bot logs
sudo journalctl -u tradingbot -f

# Tìm kiếm errors
sudo journalctl -u tradingbot | grep ERROR

# Export logs để phân tích
sudo journalctl -u tradingbot --since "2024-01-01" > bot_logs.txt
```

## 📞 Hỗ Trợ & Maintenance

### **Tác Vụ Maintenance Thường Xuyên**

```bash
#!/bin/bash
# maintenance.sh

# Cập nhật system packages
sudo apt update && sudo apt upgrade -y

# Cập nhật Python dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart bot service
sudo systemctl restart tradingbot

# Kiểm tra service status
sudo systemctl status tradingbot

# Cleanup old logs
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 🎉 Checklist Triển Khai

### **Trước Triển Khai**
- [ ] Environment variables đã cấu hình
- [ ] Database setup hoàn thành
- [ ] SSL certificates đã cài đặt (nếu cần)
- [ ] Firewall đã cấu hình
- [ ] Hệ thống backup đã setup
- [ ] Monitoring đã cấu hình

### **Sau Triển Khai**
- [ ] Bot hiển thị online trong Discord
- [ ] Commands phản hồi đúng
- [ ] Kết nối database hoạt động
- [ ] Kết nối Exchange API hoạt động
- [ ] Logs đang được tạo
- [ ] Hệ thống monitoring hoạt động

### **Sẵn Sàng Production**
- [ ] Load testing hoàn thành
- [ ] Security audit đã pass
- [ ] Backup/recovery đã test
- [ ] Monitoring alerts đã cấu hình
- [ ] Documentation đã cập nhật
- [ ] Team đã được training về operations

**🚀 Discord Trading Bot của bạn đã sẵn sàng cho production deployment!**

---

*Để được hỗ trợ thêm, tham gia [Discord Support Server](https://discord.gg/your-server) hoặc xem [hướng dẫn troubleshooting](../troubleshooting/common-issues.md) của chúng tôi.* 