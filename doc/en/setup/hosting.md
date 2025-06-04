# Hosting & Deployment Guide

A comprehensive guide for deploying the Professional Discord Trading Bot to production environments. This guide covers multiple hosting options from simple VPS setups to advanced cloud deployments.

## 🚀 Quick Start Deployment Options

### **Option 1: VPS Deployment (Recommended for Beginners)**
- ✅ **Most Cost-Effective**: $5-20/month
- ✅ **Full Control**: Complete server access
- ✅ **Simple Setup**: Step-by-step instructions below
- ⚠️ **Requires**: Basic Linux knowledge

### **Option 2: Cloud Platform Deployment**
- ✅ **Highly Scalable**: Auto-scaling capabilities
- ✅ **Professional Features**: Load balancing, monitoring
- ⚠️ **Higher Cost**: $20-100+/month
- ⚠️ **Complex Setup**: Advanced configuration required

### **Option 3: Docker Deployment**
- ✅ **Consistent Environment**: Works anywhere Docker runs
- ✅ **Easy Updates**: Simple container replacement
- ✅ **Scalable**: Kubernetes-ready
- ⚠️ **Requires**: Docker knowledge

## 🖥️ VPS Deployment (DigitalOcean/Linode/Vultr)

### **Step 1: Server Setup**

#### **Recommended VPS Specifications**
```
Minimum Requirements:
- 1 vCPU
- 1GB RAM
- 20GB SSD Storage
- Ubuntu 20.04/22.04 LTS

Recommended for Production:
- 2 vCPU
- 2GB RAM
- 40GB SSD Storage
- Ubuntu 22.04 LTS
```

#### **Initial Server Configuration**
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git screen nginx certbot python3-certbot-nginx

# Create a user for the bot
sudo adduser --disabled-password --gecos "" tradingbot
sudo usermod -aG sudo tradingbot

# Switch to bot user
sudo su - tradingbot
```

### **Step 2: Bot Installation**

```bash
# Clone the repository
git clone https://github.com/ReinaMacCredy/trading_bot.git
cd trading_bot

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create production environment file
cp env.example .env
nano .env  # Configure your environment variables
```

### **Step 3: Environment Configuration**

```env
# Production Environment Configuration
ENVIRONMENT=production
DISCORD_TOKEN=your_production_discord_token

# Exchange Configuration
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret
EXCHANGE_SANDBOX=false

# Database Configuration (PostgreSQL recommended for production)
DATABASE_URL=postgresql://tradingbot:secure_password@localhost:5432/trading_bot_prod

# Security Settings
LOG_LEVEL=INFO
MAX_RISK_PER_TRADE=0.01
MAX_DAILY_LOSS=0.03
ENABLE_PAPER_TRADING=false

# Performance Settings
CACHE_TTL=300
MAX_CONCURRENT_REQUESTS=10
```

### **Step 4: Database Setup (PostgreSQL)**

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE trading_bot_prod;
CREATE USER tradingbot WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE trading_bot_prod TO tradingbot;
\q

# Test database connection
psql -h localhost -U tradingbot -d trading_bot_prod
```

### **Step 5: Process Management with Systemd**

Create a systemd service file:

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

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/home/cfp/trading_bot

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start the service
sudo systemctl enable tradingbot
sudo systemctl start tradingbot

# Check status
sudo systemctl status tradingbot

# View logs
sudo journalctl -u tradingbot -f
```

## ☁️ Cloud Platform Deployment

### **AWS Deployment**

#### **Using AWS EC2**

```yaml
# docker-compose.yml for AWS
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

#### **AWS Lambda Deployment (Serverless)**

**Important**: Discord bots require persistent connections, so Lambda is only suitable for webhook-based implementations.

```python
# lambda_handler.py
import json
import os
from src.bot.webhook_handler import handle_discord_webhook

def lambda_handler(event, context):
    """AWS Lambda handler for Discord webhook"""
    
    try:
        # Parse the Discord webhook payload
        body = json.loads(event['body'])
        
        # Process the webhook
        response = handle_discord_webhook(body)
        
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### **Google Cloud Platform (GCP)**

#### **Using Google Compute Engine**

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Create VM instance
gcloud compute instances create trading-bot-vm \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=40GB \
    --tags=trading-bot

# SSH into the instance
gcloud compute ssh trading-bot-vm --zone=us-central1-a
```

#### **Using Cloud Run (Containerized)**

```dockerfile
# Dockerfile.cloudrun
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY config/ ./config/

# Set production environment
ENV ENVIRONMENT=production
ENV PYTHONPATH=/app

# Expose port for health checks
EXPOSE 8080

CMD ["python", "main.py"]
```

```bash
# Build and deploy to Cloud Run
gcloud run deploy trading-bot \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=production
```

## 🐳 Docker Deployment

### **Basic Docker Setup**

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash tradingbot
USER tradingbot

# Copy requirements and install dependencies
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

# Start the bot
CMD ["python", "main.py"]
```

### **Docker Compose for Development**

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

### **Docker Compose for Production**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  tradingbot:
    build: .
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://tradingbot:${DB_PASSWORD}@postgres:5432/trading_bot_prod
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - BINANCE_API_KEY=${BINANCE_API_KEY}
      - BINANCE_SECRET=${BINANCE_SECRET}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - internal

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: trading_bot_prod
      POSTGRES_USER: tradingbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    networks:
      - internal
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    networks:
      - internal
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    networks:
      - internal
    restart: unless-stopped

volumes:
  postgres_prod_data:

networks:
  internal:
    driver: bridge
```

## 🎯 Heroku Deployment

### **Step 1: Heroku Setup**

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login

# Create Heroku app
heroku create your-trading-bot-name

# Set environment variables
heroku config:set ENVIRONMENT=production
heroku config:set DISCORD_TOKEN=your_discord_token
heroku config:set BINANCE_API_KEY=your_api_key
heroku config:set BINANCE_SECRET=your_secret
```

### **Step 2: Heroku Configuration Files**

```
# Procfile
worker: python main.py
```

```python
# runtime.txt
python-3.11.6
```

```
# app.json
{
  "name": "Professional Discord Trading Bot",
  "description": "A professional-grade Discord bot for cryptocurrency trading",
      "repository": "https://github.com/ReinaMacCredy/trading_bot",
  "logo": "https://your-logo-url.com/logo.png",
  "keywords": ["discord", "trading", "cryptocurrency", "bot"],
  "env": {
    "DISCORD_TOKEN": {
      "description": "Discord bot token",
      "required": true
    },
    "BINANCE_API_KEY": {
      "description": "Binance API key",
      "required": true
    },
    "BINANCE_SECRET": {
      "description": "Binance API secret",
      "required": true
    },
    "ENVIRONMENT": {
      "description": "Environment mode",
      "value": "production"
    }
  },
  "addons": [
    {
      "plan": "heroku-postgresql:mini"
    },
    {
      "plan": "heroku-redis:mini"
    }
  ]
}
```

### **Step 3: Deploy to Heroku**

```bash
# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Add Redis addon
heroku addons:create heroku-redis:mini

# Deploy the bot
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Scale the worker
heroku ps:scale worker=1

# View logs
heroku logs --tail
```

## 🔧 Advanced Production Setup

### **Monitoring & Logging**

#### **Prometheus & Grafana Setup**

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
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

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

#### **Application Metrics**

```python
# src/utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Metrics definitions
COMMAND_COUNTER = Counter('discord_commands_total', 'Total Discord commands processed', ['command'])
RESPONSE_TIME = Histogram('command_response_seconds', 'Command response time')
ACTIVE_USERS = Gauge('active_users', 'Number of active users')
SIGNALS_GENERATED = Counter('signals_generated_total', 'Total signals generated', ['symbol', 'strategy'])

def start_metrics_server(port=8000):
    """Start Prometheus metrics server"""
    start_http_server(port)

@RESPONSE_TIME.time()
def track_command_response(func):
    """Decorator to track command response times"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        RESPONSE_TIME.observe(time.time() - start_time)
        return result
    return wrapper
```

### **SSL/TLS Configuration**

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

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;

        location / {
            proxy_pass http://tradingbot;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### **Backup & Recovery**

```bash
#!/bin/bash
# backup.sh

DB_CONTAINER="tradingbot_postgres_1"
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# Create database backup
docker exec $DB_CONTAINER pg_dump -U tradingbot trading_bot_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Backup application logs
tar -czf $BACKUP_DIR/logs_backup_$DATE.tar.gz logs/

# Upload to cloud storage (example: AWS S3)
aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql s3://your-backup-bucket/
aws s3 cp $BACKUP_DIR/logs_backup_$DATE.tar.gz s3://your-backup-bucket/

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

## 📊 Performance Optimization

### **Production Performance Settings**

```yaml
# config/production.yml
performance:
  connection_pool_size: 20
  max_concurrent_requests: 50
  cache_ttl: 300
  
  # Database optimization
  database:
    pool_size: 10
    max_overflow: 20
    pool_timeout: 30
    
  # Redis configuration
  redis:
    max_connections: 100
    socket_timeout: 5
    
  # Bot optimization
  bot:
    command_cooldown: 1.0
    max_commands_per_minute: 30
    shard_count: 1  # Increase for large bots
```

### **Scaling Considerations**

```python
# src/bot/scaling.py
import asyncio
from discord.ext import commands

class ScalingMixin:
    """Mixin for bot scaling features"""
    
    async def setup_sharding(self):
        """Setup automatic sharding"""
        if self.shard_count is None:
            # Auto-calculate shard count based on guild count
            guild_count = len(self.guilds)
            self.shard_count = max(1, guild_count // 2500)
    
    async def setup_clustering(self):
        """Setup clustering for multiple instances"""
        # Implement Redis-based coordination
        pass
    
    async def setup_load_balancing(self):
        """Setup load balancing for high traffic"""
        # Implement request distribution
        pass
```

## 🚨 Security Best Practices

### **Environment Security**

```bash
# Secure file permissions
chmod 600 .env
chmod 700 ~/.ssh
chmod 644 ~/.ssh/authorized_keys

# Firewall configuration
sudo ufw allow ssh
sudo ufw allow 443
sudo ufw enable

# Fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### **Application Security**

```python
# src/security/validator.py
import re
from cryptography.fernet import Fernet

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_discord_token(token: str) -> bool:
        """Validate Discord token format"""
        return re.match(r'^[A-Za-z0-9._-]{59}$', token) is not None
    
    @staticmethod
    def encrypt_api_key(key: str, encryption_key: bytes) -> str:
        """Encrypt API keys for storage"""
        fernet = Fernet(encryption_key)
        return fernet.encrypt(key.encode()).decode()
    
    @staticmethod
    def decrypt_api_key(encrypted_key: str, encryption_key: bytes) -> str:
        """Decrypt API keys"""
        fernet = Fernet(encryption_key)
        return fernet.decrypt(encrypted_key.encode()).decode()
```

## 🔍 Troubleshooting

### **Common Issues**

#### **Memory Issues**
```bash
# Check memory usage
free -h
htop

# Optimize Python memory
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

#### **Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
psql -h localhost -U tradingbot -d trading_bot_prod
```

#### **Discord Connection Issues**
```python
# Add connection monitoring
@bot.event
async def on_disconnect():
    logger.warning("Bot disconnected from Discord")

@bot.event
async def on_resumed():
    logger.info("Bot connection resumed")
```

### **Log Analysis**

```bash
# View bot logs
sudo journalctl -u tradingbot -f

# Search for errors
sudo journalctl -u tradingbot | grep ERROR

# Export logs for analysis
sudo journalctl -u tradingbot --since "2024-01-01" > bot_logs.txt
```

## 📞 Support & Maintenance

### **Regular Maintenance Tasks**

```bash
#!/bin/bash
# maintenance.sh

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart bot service
sudo systemctl restart tradingbot

# Check service status
sudo systemctl status tradingbot

# Cleanup old logs
find logs/ -name "*.log" -mtime +30 -delete
```

### **Health Monitoring**

```python
# src/bot/health_check.py
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bot_status": "online" if bot.is_ready() else "offline",
        "database": await check_database_connection(),
        "exchange": await check_exchange_connection()
    }

async def check_database_connection():
    """Check database connectivity"""
    try:
        # Test database query
        return "connected"
    except Exception:
        return "disconnected"

async def check_exchange_connection():
    """Check exchange connectivity"""
    try:
        # Test exchange API
        return "connected"
    except Exception:
        return "disconnected"
```

---

## 🎉 Deployment Checklist

### **Pre-Deployment**
- [ ] Environment variables configured
- [ ] Database setup completed
- [ ] SSL certificates installed (if applicable)
- [ ] Firewall configured
- [ ] Backup system setup
- [ ] Monitoring configured

### **Post-Deployment**
- [ ] Bot appears online in Discord
- [ ] Commands respond correctly
- [ ] Database connections working
- [ ] Exchange API connections working
- [ ] Logs are being generated
- [ ] Monitoring systems active

### **Production Ready**
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Backup/recovery tested
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Team trained on operations

**🚀 Your Discord Trading Bot is now ready for production deployment!**

---

*For additional support, join our [Discord Support Server](https://discord.gg/your-server) or check our [troubleshooting guide](../troubleshooting/common-issues.md).* 