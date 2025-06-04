# Installation Guide

This guide will walk you through installing and setting up the Professional Discord Trading Bot on your system.

## 📋 Prerequisites

Before you begin, ensure you have the following:

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.9 or higher
- **Memory**: At least 2GB RAM
- **Storage**: 1GB free disk space
- **Internet**: Stable internet connection for real-time trading data

### Required Accounts
- **Discord Developer Account**: For creating and managing your bot
- **Exchange Account**: Binance account (recommended) or other supported exchanges
- **Git**: For cloning the repository (optional but recommended)

## 🔧 Step 1: Install Python

### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer and **check "Add Python to PATH"**
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

### macOS
```bash
# Using Homebrew (recommended)
brew install python

# Or download from python.org
# Verify installation
python3 --version
pip3 --version
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
pip3 --version
```

## 📁 Step 2: Download the Bot

### Option A: Clone with Git (Recommended)
```bash
git clone https://github.com/ReinaMacCredy/trading_bot.git
cd trading_bot
```

### Option B: Download ZIP
1. Go to the [GitHub repository](https://github.com/ReinaMacCredy/trading_bot)
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Navigate to the extracted folder

## 🐍 Step 3: Set Up Virtual Environment

Create an isolated Python environment for the bot:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

# Verify activation (you should see (.venv) in your prompt)
```

## 📦 Step 4: Install Dependencies

With the virtual environment activated:

```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
pip list
```

### Common Dependencies Include:
- `discord.py` - Discord API wrapper
- `ccxt` - Exchange API integration
- `pandas` - Data manipulation
- `pandas-ta` - Technical analysis indicators
- `pyyaml` - Configuration file parsing
- `python-dotenv` - Environment variable management

## 🤖 Step 5: Create Discord Bot

### 1. Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Enter application name (e.g., "Trading Bot")
4. Click "Create"

### 2. Create Bot User
1. Go to "Bot" section in left sidebar
2. Click "Add Bot"
3. Customize bot username and avatar
4. Copy the **Bot Token** (keep this secret!)

### 3. Set Bot Permissions
1. Go to "OAuth2" → "URL Generator"
2. Select scopes:
   - `bot`
   - `applications.commands`
3. Select permissions:
   - `Send Messages`
   - `Use Slash Commands`
   - `Embed Links`
   - `Attach Files`
   - `Read Message History`
4. Copy the generated URL and use it to invite the bot to your server

## 🔑 Step 6: Configure Environment Variables

### 1. Copy Environment Template
```bash
cp env.example .env
```

### 2. Edit Configuration
Open `.env` file and add your credentials:

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here

# Exchange API Configuration
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret_key
EXCHANGE_SANDBOX=true

# Trading Configuration
MAX_RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
ENABLE_PAPER_TRADING=true

# Environment Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Exchange API Setup

#### Binance (Recommended)
1. Go to [Binance](https://www.binance.com/) and create account
2. Enable 2FA for security
3. Go to API Management
4. Create new API key with these permissions:
   - ✅ Read Info
   - ✅ Spot & Margin Trading (for live trading)
   - ❌ Futures Trading (unless needed)
   - ❌ Withdrawals (NEVER enable for bot)
5. Add your server IP to whitelist
6. Copy API Key and Secret to `.env` file

**Important**: Start with testnet/sandbox mode (`EXCHANGE_SANDBOX=true`) for testing!

## ⚙️ Step 7: Configure Bot Settings

### 1. Main Configuration
Edit `src/config/config.yml` for advanced settings:

```yaml
# Trading Settings
trading:
  default_strategy: "MACD_RSI"
  risk_per_trade: 0.02
  max_positions: 5
  
# Technical Indicators
indicators:
  rsi:
    period: 14
    overbought: 70
    oversold: 30
  macd:
    fast: 12
    slow: 26
    signal: 9

# Risk Management
risk:
  max_daily_loss: 0.05
  stop_loss_percentage: 0.02
  take_profit_ratio: 2.5
```

### 2. Discord Settings
Configure Discord-specific settings in the config file or environment variables.

## 🚀 Step 8: Test Installation

### 1. Verify Configuration
```bash
python main.py --check-config
```

### 2. Test Discord Connection
```bash
python main.py --test-discord
```

### 3. Test Exchange Connection
```bash
python main.py --test-exchange
```

### 4. Run Full Test
```bash
python main.py --test-all
```

## ▶️ Step 9: Run the Bot

### Development Mode
```bash
python main.py
```

### Production Mode
```bash
python main.py --environment production
```

### Background Mode (Linux/macOS)
```bash
nohup python main.py > bot.log 2>&1 &
```

## ✅ Verification

After starting the bot, verify it's working:

1. **Discord Status**: Bot should appear online in your Discord server
2. **Log Output**: Check console for any errors
3. **Test Command**: Try `b!test_connection` in Discord
4. **Exchange Connection**: Verify API connection with `b!balance`

## 🔧 Troubleshooting

### Common Issues

#### Bot Won't Start
```bash
# Check Python version
python --version

# Verify dependencies
pip install -r requirements.txt --upgrade

# Check environment variables
python -c "import os; print(os.getenv('DISCORD_TOKEN'))"
```

#### Permission Errors
```bash
# Linux/macOS: Check file permissions
chmod +x main.py

# Ensure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

#### Exchange Connection Issues
- Verify API keys are correct
- Check IP whitelist settings
- Ensure sandbox mode is enabled for testing
- Verify exchange is supported

#### Discord Connection Issues
- Verify bot token is correct
- Check bot permissions in Discord server
- Ensure bot is invited to the correct server

### Getting Help

If you encounter issues:

1. **Check Logs**: Look at console output for error messages
2. **Read Documentation**: Check relevant sections in this documentation
3. **GitHub Issues**: Search existing issues or create a new one
4. **Discord Support**: Join our support server

## 🔄 Next Steps

After successful installation:

1. **[Configuration Guide](configuration.md)** - Customize bot settings
2. **[Security Setup](security.md)** - Secure your bot and API keys
3. **[Basic Usage](../guides/basic-usage.md)** - Learn essential commands
4. **[Trading Signals](../guides/trading-signals.md)** - Understand signal generation

## 🔒 Security Notes

- **Never share your bot token or API keys**
- **Use environment variables for sensitive data**
- **Enable 2FA on all accounts**
- **Start with sandbox/testnet mode**
- **Regularly update dependencies**
- **Monitor bot activity and logs**

---

**Congratulations!** Your Discord Trading Bot is now installed and ready to use. Remember to start with paper trading and small amounts when moving to live trading.

*For production deployment, see our [Hosting Guide](hosting.md) for VPS and cloud deployment options.* 