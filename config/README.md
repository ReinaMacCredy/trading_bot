# ⚙️ Configuration Files

Thư mục này chứa tất cả file cấu hình cho Discord Trading Bot.

## 📁 Files Overview

### Environment Configuration
- **`env.example`** - Template file cho environment variables

## 🔧 Setup Instructions

### 1. Copy Environment Template
```bash
cp config/env.example .env
```

### 2. Configure Required Variables

#### Discord Bot (Required)
```bash
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id_here
```

#### Trading Exchanges (Optional)
```bash
# Binance
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET=your_binance_secret_key_here

# MEXC
MEXC_API_KEY=your_mexc_api_key_here
MEXC_SECRET=your_mexc_secret_key_here

# Other exchanges...
```

#### Risk Management
```bash
MAX_RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
ENABLE_PAPER_TRADING=true
```

## 🚀 Quick Start Configurations

### Development Mode
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
EXCHANGE_SANDBOX=true
ENABLE_PAPER_TRADING=true
```

### Production Mode
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
EXCHANGE_SANDBOX=false
ENABLE_PAPER_TRADING=false
```

### VPS Mode (Lightweight)
```bash
ENVIRONMENT=production
DATABASE_URL=sqlite:///data/trading_bot.db
LOG_LEVEL=INFO
```

## 🔒 Security Notes

- ⚠️ **Never commit .env file to git**
- 🔐 Use sandbox mode for testing
- 🛡️ Enable paper trading initially
- 🔑 Store API keys securely

## 📊 Multi-Exchange Support

Bot hỗ trợ nhiều exchange:
- **Crypto**: Binance, MEXC, Coinbase, Kraken, Bybit, KuCoin
- **Forex**: MetaTrader 5 (MT5)
- **Auto-routing**: Tự động chọn exchange phù hợp

## 🔧 Advanced Configuration

### Database Options
```bash
# SQLite (Default, lightweight)
DATABASE_URL=sqlite:///data/trading_bot.db

# PostgreSQL (Production)
DATABASE_URL=postgresql://user:pass@localhost:5432/trading_bot
```

### Feature Flags
```bash
ENABLE_BACKTESTING=true
ENABLE_ANALYTICS=true
ENABLE_WEB_DASHBOARD=false
ENABLE_MULTI_EXCHANGE=true
``` 