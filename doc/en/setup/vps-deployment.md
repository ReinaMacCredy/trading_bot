# VPS Deployment Guide

## Quick Fix for Common VPS Issues

### Issue 1: ModuleNotFoundError: No module named 'discord'

This happens when dependencies aren't installed on your VPS. Follow these steps:

```bash
# 1. Navigate to your project directory
cd /path/to/your/trading_bot

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verify discord.py installation
python3 -c "import discord; print('Discord.py version:', discord.__version__)"
```

### Issue 2: cgitb DeprecationWarning

The `cgitb` module has been removed from the main.py file as it's deprecated in Python 3.13.

## Automated Setup Script

Use the provided setup script for easier deployment:

```bash
# Make the script executable
chmod +x scripts/vps_setup.sh

# Run the setup script
./scripts/vps_setup.sh
```

## Manual Setup Steps

### 1. System Requirements

- Python 3.11+ 
- Virtual environment support
- Internet connectivity for API calls

### 2. Environment Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip if not available
sudo apt install python3 python3-pip python3-venv -y

# Clone or upload your project files
# git clone https://github.com/ReinaMacCredy/trading_bot.git
# cd trading_bot
```

### 3. Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configuration

```bash
# Copy environment template
cp env.example .env

# Edit configuration with your values
nano .env
```

Required environment variables:
- `DISCORD_TOKEN` - Your Discord bot token
- `DISCORD_CHANNEL_ID` - Target channel ID
- `BINANCE_API_KEY` - Your Binance API key (optional)
- `BINANCE_API_SECRET` - Your Binance API secret (optional)

### 5. Running the Bot

```bash
# Test run
python main.py

# Run in background with logs
nohup python main.py > logs/bot.log 2>&1 &

# Or use screen/tmux for persistent sessions
screen -S tradingbot
python main.py
# Ctrl+A, D to detach
```

## Production Deployment

### Using Docker

```bash
# Build the image
docker build -t trading-bot .

# Run with docker-compose
docker-compose up -d
```

### Using systemd Service

Create `/etc/systemd/system/trading-bot.service`:

```ini
[Unit]
Description=Discord Trading Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/trading_bot
Environment=PATH=/path/to/trading_bot/venv/bin
ExecStart=/path/to/trading_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

## Monitoring

### Health Check
The bot includes built-in health monitoring on port 8080:
- `http://your-vps:8080/health` - Health status
- `http://your-vps:8080/metrics` - Performance metrics

### Logs
- Application logs: `logs/bot.log`
- Discord logs: `discord.log`
- System logs: `journalctl -u trading-bot -f`

## Troubleshooting

### Common Issues

1. **Permission denied**: Ensure proper file permissions
2. **Port conflicts**: Check if port 8080 is available
3. **Memory issues**: Monitor VPS resources
4. **API rate limits**: Check exchange API limits

### Debug Commands

```bash
# Check bot status
python3 -c "
import discord
from src.config.config_loader import get_config
print('Config loaded successfully')
"

# Test Discord connection
python3 -c "
import asyncio
import discord
from src.config.config_loader import get_discord_config
print('Discord libraries working')
"

# Verify all dependencies
python3 -c "
modules = ['discord', 'ccxt', 'pandas', 'numpy', 'dotenv', 'aiohttp']
for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError as e:
        print(f'❌ {module}: {e}')
"
```

## Support

If you encounter issues:
1. Check the logs for error messages
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed
4. Check network connectivity and firewall settings 