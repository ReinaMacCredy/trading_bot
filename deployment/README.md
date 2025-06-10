# 🚀 Deployment Configuration

Thư mục này chứa tất cả file cấu hình để triển khai Discord Trading Bot lên các môi trường khác nhau.

## 📁 Files Overview

### Docker Files
- **`Dockerfile`** - Container chính cho development
- **`Dockerfile.vps`** - Container tối ưu cho VPS deployment
- **`.dockerignore`** - Loại trừ file không cần thiết khỏi Docker build

### Docker Compose Configurations
- **`docker-compose.yml`** - Development environment (PostgreSQL + Redis + Adminer)
- **`docker-compose.prod.yml`** - Production environment (Full monitoring stack)
- **`docker-compose.vps.yml`** - VPS optimized (Lightweight, SQLite)

### Deployment Scripts
- **`vps-deployment.sh`** - Script tự động triển khai cho VPS cfp.io.vn
- **`app.json`** - Heroku one-click deployment configuration
- **`Procfile`** - Heroku process configuration

## 🚀 Quick Deployment Commands

### VPS Deployment (cfp.io.vn)
```bash
cd deployment/
chmod +x vps-deployment.sh
./vps-deployment.sh
```

### Production Deployment
```bash
cd deployment/
docker compose -f docker-compose.prod.yml up -d
```

### Development Deployment
```bash
cd deployment/
docker compose -f docker-compose.yml up -d
```

### VPS Optimized Deployment
```bash
cd deployment/
docker compose -f docker-compose.vps.yml up -d
```

## 📊 Environment Comparison

| Feature | Development | Production | VPS |
|---------|-------------|------------|-----|
| Database | PostgreSQL | PostgreSQL | SQLite |
| Monitoring | Basic | Full Stack | Basic |
| Resources | High | High | Limited |
| SSL/Nginx | No | Yes | No |
| Auto-updates | No | No | Yes |

## 🔧 Configuration

Trước khi deploy, copy file config:
```bash
cp ../config/env.example ../.env
# Edit .env với credentials thực tế
```

## 📝 Notes

- **VPS deployment** tự động cài đặt Docker và dependencies
- **Production deployment** bao gồm Prometheus, Grafana, Nginx
- **Development deployment** có hot-reload và database tools
- Tất cả deployments đều có health checks và automatic restarts 