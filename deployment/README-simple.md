# 🚀 Simple Deployment Guide

Đây là phiên bản deploy đơn giản cho Trading Bot, loại bỏ các tính năng phức tạp và chỉ giữ lại những gì cần thiết.

## 📋 Yêu cầu

- Docker & Docker Compose
- Discord Bot Token
- (Optional) Binance API credentials

## ⚡ Quick Start

### 1. Tạo file .env
```bash
# Tạo file .env trong thư mục gốc
cp config/env.example .env

# Chỉnh sửa với thông tin của bạn
DISCORD_TOKEN=your_discord_bot_token
BINANCE_API_KEY=your_api_key      # Optional
BINANCE_SECRET=your_secret        # Optional
```

### 2. Deploy đơn giản

```bash
cd deployment

# Chỉ Discord Bot (đơn giản nhất)
./simple-deploy.sh bot

# Hoặc Bot + Web Server
./simple-deploy.sh all
```

## 🎯 Các chế độ deploy

### 1. Bot only (Khuyến nghị cho bắt đầu)
```bash
./simple-deploy.sh bot
```
- Chỉ Discord Bot
- Không cần database
- Không cần Redis
- Nhẹ nhất, dễ nhất

### 2. Full Stack
```bash
./simple-deploy.sh all
```
- Discord Bot + Web Server + Redis
- Có TradingView webhook
- API endpoints

### 3. Web only
```bash
./simple-deploy.sh web
```
- Chỉ Web Server + Redis
- Không có Discord Bot

## 📊 Quản lý

```bash
# Xem trạng thái
docker-compose -f simple-deploy.yml ps

# Xem logs
docker-compose -f simple-deploy.yml logs -f

# Stop
docker-compose -f simple-deploy.yml down

# Update
docker-compose -f simple-deploy.yml up --build -d
```

## 🔧 Khác biệt với deployment full

| Feature | Simple | Full |
|---------|--------|------|
| PostgreSQL | ❌ | ✅ |
| Monitoring | ❌ | ✅ |
| SSL/TLS | ❌ | ✅ |
| Multi-stage Docker | ❌ | ✅ |
| Health checks | ❌ | ✅ |
| Adminer | ❌ | ✅ |
| Dependencies | 13 packages | 62 packages |
| Setup time | 2-5 phút | 10-15 phút |

## 🚨 Lưu ý

- Simple deployment phù hợp cho testing và development
- Không có persistence cho Redis (restart sẽ mất data)
- Không có monitoring và alerting
- Chỉ support basic features

## 🆙 Upgrade lên Full

Khi cần full features:
```bash
# Stop simple
docker-compose -f simple-deploy.yml down

# Start full
docker-compose -f docker-compose.prod.yml up -d
``` 