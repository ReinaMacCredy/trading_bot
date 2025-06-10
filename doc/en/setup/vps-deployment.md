# 🚀 Discord Trading Bot - VPS Deployment Guide

Complete guide for deploying your Discord Trading Bot to a VPS using Docker.

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Installation](#manual-installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## 🔧 Prerequisites

### VPS Requirements
- **OS**: Ubuntu 20.04+ or Debian 11+ (recommended)
- **RAM**: Minimum 1GB, recommended 2GB+
- **Storage**: Minimum 10GB free space
- **CPU**: 1 vCPU minimum, 2 vCPU recommended
- **Network**: Stable internet connection

### Required Software
- Docker Engine 20.10+
- Docker Compose v2.0+
- Git
- Curl
- Text editor (nano, vim, etc.)

### Required Credentials
- Discord Bot Token
- Binance API Key and Secret (optional for demo mode)
- VPS SSH access

## ⚡ Quick Start

### Automated Deployment (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/ReinaMacCredy/trading_bot.git
cd trading_bot
```

2. **Make deployment script executable:**
```bash
cd deployment
chmod +x vps-deployment.sh
```

3. **Run automated deployment:**
```bash
./vps-deployment.sh
```

The script will:
- Check system requirements
- Install Docker if needed
- Set up environment configuration
- Build and deploy the bot
- Configure monitoring and systemd service

## 🔨 Manual Installation

### Step 1: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then verify
docker --version
docker compose version
```

### Step 2: Clone Repository

```bash
git clone https://github.com/ReinaMacCredy/trading_bot.git
cd trading_bot
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp config/env.example .env

# Edit configuration
nano .env
```

**Required variables:**
```env
DISCORD_TOKEN=your_discord_bot_token_here
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET=your_binance_secret_here
EXCHANGE_SANDBOX=true
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Step 4: Create Directories

```bash
mkdir -p logs data results
chmod 755 logs data results
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DISCORD_TOKEN` | Your Discord bot token | ✅ | - |
| `BINANCE_API_KEY` | Binance API key | ❌ | Demo mode |
| `BINANCE_SECRET` | Binance API secret | ❌ | Demo mode |
| `EXCHANGE_SANDBOX` | Use sandbox/testnet | ❌ | `true` |
| `MAX_RISK_PER_TRADE` | Maximum risk per trade (%) | ❌ | `0.01` |
| `MAX_DAILY_LOSS` | Maximum daily loss (%) | ❌ | `0.03` |
| `LOG_LEVEL` | Logging level | ❌ | `INFO` |

### Docker Compose Configuration

The bot uses `docker-compose.vps.yml` for VPS deployment with:
- **Optimized resource limits**: 512MB RAM, 0.5 CPU
- **SQLite database**: Lightweight, no external DB required
- **Redis caching**: For performance optimization
- **Health checks**: Automatic monitoring
- **Log rotation**: Prevents disk space issues
- **Auto-restart**: Ensures high availability

## 🚀 Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Navigate to deployment directory
cd deployment

# Build and start services
docker compose -f docker-compose.vps.yml up -d --build

# Check status
docker compose -f docker-compose.vps.yml ps

# View logs
docker compose -f docker-compose.vps.yml logs -f tradingbot
```

### Option 2: Systemd Service

```bash
# Create systemd service
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

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable trading-bot.service
sudo systemctl start trading-bot
```

## 📊 Monitoring

### Health Check

The bot exposes a health endpoint:
```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime": "2h 15m 30s",
  "version": "1.0.0"
}
```

### Monitoring Script

Use the included monitoring script:
```bash
# Navigate to deployment directory
cd deployment

# Check bot status
./monitor_bot.sh status

# View recent logs
./monitor_bot.sh logs

# View resource usage
./monitor_bot.sh stats

# Restart bot
./monitor_bot.sh restart
```

### Log Management

Logs are automatically rotated and stored in:
- `logs/bot.log` - Main bot logs
- `logs/trading.log` - Trading activity logs
- `logs/errors.log` - Error logs

View logs:
```bash
# Real-time logs
docker compose -f deployment/docker-compose.vps.yml logs -f tradingbot

# Recent logs
tail -f logs/bot.log

# Error logs
tail -f logs/errors.log
```

## 🔧 Management Commands

### Basic Operations

```bash
# Navigate to deployment directory
cd deployment

# Start bot
docker compose -f docker-compose.vps.yml up -d

# Stop bot
docker compose -f docker-compose.vps.yml down

# Restart bot
docker compose -f docker-compose.vps.yml restart tradingbot

# View status
docker compose -f docker-compose.vps.yml ps

# View logs
docker compose -f docker-compose.vps.yml logs tradingbot
```

### Updates and Maintenance

```bash
# Update bot
git pull
cd deployment
docker compose -f docker-compose.vps.yml up -d --build

# Clean up old images
docker image prune -f

# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/

# Check disk usage
df -h
docker system df
```

### Systemd Management

```bash
# Start/stop via systemd
sudo systemctl start trading-bot
sudo systemctl stop trading-bot
sudo systemctl restart trading-bot

# Check status
sudo systemctl status trading-bot

# View service logs
sudo journalctl -u trading-bot -f
```

## 🐛 Troubleshooting

### Common Issues

#### Bot Won't Start
```bash
# Check logs
cd deployment
docker compose -f docker-compose.vps.yml logs tradingbot

# Check environment
cat .env

# Verify Discord token
curl -H "Authorization: Bot YOUR_TOKEN" https://discord.com/api/v10/users/@me
```

#### Memory Issues
```bash
# Check memory usage
free -h
docker stats

# Restart with memory limit
cd deployment
docker compose -f docker-compose.vps.yml down
docker compose -f docker-compose.vps.yml up -d
```

#### Disk Space Issues
```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a

# Clean logs
sudo truncate -s 0 logs/*.log
```

#### Network Issues
```bash
# Check connectivity
ping discord.com
ping api.binance.com

# Check ports
netstat -tulpn | grep 8080

# Test health endpoint
curl localhost:8080/health
```

### Log Analysis

Common error patterns:
```bash
# Discord connection errors
grep -i "discord" logs/errors.log

# API errors
grep -i "api" logs/errors.log

# Memory errors
grep -i "memory\|oom" logs/errors.log

# Database errors
grep -i "database\|sqlite" logs/errors.log
```

## 🔐 Security Best Practices

### Environment Security
- Store secrets in `.env` file with restricted permissions:
```bash
chmod 600 .env
```

- Use environment variables, never hardcode secrets
- Regularly rotate API keys
- Use sandbox mode for testing

### Container Security
- Run as non-root user (automatically configured)
- Use specific resource limits
- Keep Docker and images updated
- Monitor security logs

### Network Security
- Use firewall rules:
```bash
sudo ufw allow ssh
sudo ufw allow 8080/tcp
sudo ufw enable
```

- Consider using a reverse proxy (nginx)
- Enable fail2ban for SSH protection

## 📈 Performance Optimization

### Resource Monitoring
```bash
# Check container resources
docker stats

# Check system resources
htop
free -h
df -h
```

### Optimization Tips
1. **Memory**: Increase if you see OOM errors
2. **CPU**: Monitor during high trading activity
3. **Disk**: Regular cleanup and log rotation
4. **Network**: Monitor API rate limits

### Scaling Options
- Vertical scaling: Increase VPS resources
- Horizontal scaling: Multiple bot instances
- Database scaling: Switch to PostgreSQL for high volume

## 📞 Support

### Getting Help
- Check logs first: `docker compose -f deployment/docker-compose.vps.yml logs tradingbot`
- Use monitoring script: `./deployment/monitor_bot.sh status`
- Review common issues above
- Check GitHub issues

### Useful Commands
```bash
# Quick health check
curl -s localhost:8080/health | jq '.'

# Container inspection
docker inspect tradingbot

# Resource usage
docker stats --no-stream

# Network inspection
docker network ls
docker network inspect trading_bot_bot-network
```

----

## 🎉 Congratulations!

Your Discord Trading Bot is now running on your VPS! 

**Quick verification:**
1. Check health: `curl localhost:8080/health`
2. Monitor status: `./deployment/monitor_bot.sh status`
3. View logs: `./deployment/monitor_bot.sh logs`
4. Test Discord commands in your server

For ongoing support and updates, star the repository and watch for releases.

----

**Happy Trading! 📈🚀** 