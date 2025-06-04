# Professional Discord Trading Bot

A professional-grade Discord bot for cryptocurrency trading signals, analysis, and automated trading. Features advanced configuration management, multi-exchange support, and comprehensive technical analysis capabilities.

## 🚀 Key Features

### **Trading Signals & Analysis**
- **Real-time signal generation** using live Binance market data
- **Professional signal formatting** similar to trading channels
- **Multi-timeframe analysis** with MACD+RSI strategies
- **Advanced technical indicators** (RSI, MACD, EMA, Bollinger Bands, ATR, Stochastic)
- **Market regime detection** and adaptive parameters
- **Volatility-based entry/exit calculations**

### **Risk Management & Optimization**
- **Dynamic position sizing** based on account balance and risk tolerance
- **Professional risk management** with stop-loss and take-profit automation
- **Parameter optimization** using genetic algorithms and grid search
- **Real-time market condition analysis**
- **Advanced order placement** with multiple order types

### **Configuration & Architecture**
- **Professional configuration management** with YAML + environment variables
- **Modular architecture** with clean separation of concerns
- **Multi-exchange support** through CCXT integration
- **Comprehensive logging** and error handling
- **Database integration** for signal storage and analysis

### **Advanced Features**
- **Backtesting capabilities** for strategy validation
- **Paper trading mode** for safe testing
- **Machine learning optimization** (optional)
- **Performance tracking** and analytics
- **Security features** with encrypted API key storage

## 🏗️ Architecture

```
trading_bot/
├── src/
│   ├── config/           # Configuration management
│   │   ├── config_loader.py  # Smart config loader
│   │   └── config.yml        # Main configuration
│   ├── bot/              # Discord bot core
│   ├── trading/          # Trading engine
│   │   ├── strategies.py     # Trading strategies
│   │   ├── indicators.py     # Technical indicators
│   │   ├── optimization_manager.py  # Parameter optimization
│   │   └── risk_manager.py   # Risk management
│   └── utils/            # Utilities
├── legacy/              # Archived legacy modules
├── memory-bank/          # Project documentation
├── main.py              # Bot entry point
└── requirements.txt     # Dependencies
```

Legacy modules contain earlier versions of the trading engine and helper
functions. They are kept for reference but are no longer actively
maintained.

## 🛠️ Setup & Installation

### **Prerequisites**
- Python 3.9+
- Discord Bot Token
- Binance API credentials (optional for demo mode)

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/ReinaMacCredy/trading_bot.git
   cd discord_bot/trading_bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

4. **Configure bot settings** (optional)
   ```bash
   # Edit src/config/config.yml for custom parameters
   ```

### **Environment Variables**

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token

# Exchange API Configuration  
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret
EXCHANGE_SANDBOX=true

# Trading Configuration
MAX_RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
ENABLE_PAPER_TRADING=true

# Environment Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 🚀 Running the Bot

### **Local Development**
```bash
python3 main.py
```

### **Docker Development**
```bash
# Quick start with Docker
docker-compose up -d

# Or use the deployment script
./scripts/deploy.sh docker-dev
```

### **Production Deployment**
```bash
# Deploy to production with Docker
./scripts/deploy.sh docker-prod

# Deploy to Heroku
./scripts/deploy.sh heroku

# Deploy to VPS (see hosting guide)
./scripts/deploy.sh vps
```

The bot will:
- ✅ Load configuration from YAML and environment variables
- ✅ Connect to Discord
- ✅ Initialize trading components
- ✅ Start listening for commands

## 🌐 Hosting & Deployment

### **🚀 Quick Deployment Options**

#### **Option 1: One-Click Heroku Deployment**
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

#### **Option 2: Docker Deployment**
```bash
# Development
./scripts/deploy.sh docker-dev

# Production with monitoring
./scripts/deploy.sh docker-prod
```

#### **Option 3: VPS Deployment**
```bash
# Automated VPS setup
./scripts/deploy.sh vps
```

### **📋 Hosting Requirements**

**Minimum Requirements:**
- 1 vCPU, 1GB RAM, 20GB Storage
- Python 3.9+, Docker (optional)
- PostgreSQL or SQLite

**Recommended for Production:**
- 2 vCPU, 2GB RAM, 40GB Storage
- PostgreSQL + Redis
- SSL/TLS certificate
- Monitoring stack

### **🔧 Deployment Commands**

```bash
# Check deployment readiness
./scripts/deploy.sh check

# Deploy to different platforms
./scripts/deploy.sh docker-dev    # Local development
./scripts/deploy.sh docker-prod   # Production with monitoring
./scripts/deploy.sh heroku        # Heroku deployment
./scripts/deploy.sh vps          # VPS deployment

# Health monitoring
curl http://localhost:8080/health  # Check bot health
```

For detailed hosting instructions, see our **[Comprehensive Hosting Guide](doc/en/setup/hosting.md)**.

## 📋 Available Commands

### **🎯 Signal Generation**

- **`b!generate_signal <symbol> [strategy] [risk_reward]`**
  - Generate trading signal with real market data
  - Example: `b!generate_signal BTC SC02 2.5`

- **`b!market_signals [count]`**
  - Generate signals for top market cap coins
  - Example: `b!market_signals 5`

- **`b!live_signal [channel_id]`**
  - Send live signal to specified channel
  - Example: `b!live_signal 123456789012345678`

### **📊 Advanced Analysis**

- **`b!dual_macd_rsi <symbol> [interval] [higher_tf]`**
  - Dual timeframe MACD+RSI analysis
  - Example: `b!dual_macd_rsi BTC 1h 4h`

- **`b!market_regime <symbol> [timeframe]`**
  - Detect market regime and optimize parameters
  - Example: `b!market_regime ETH 1h`

- **`b!indicator <name> <symbol> [interval] [params]`**
  - Analyze with specific indicators (RSI, MACD, EMA)
  - Example: `b!indicator rsi BTC 1h 14 30 70`

### **⚖️ Risk Management**

- **`b!risk_settings [risk] [daily_loss] [trailing_stop]`**
  - Update risk parameters (percentages)
  - Example: `b!risk_settings 2 5 1.5`

- **`b!position_size <symbol> <entry> <stop_loss>`**
  - Calculate optimal position size
  - Example: `b!position_size BTC 60000 58500`

- **`b!position_size_advanced <symbol> [balance] [risk_percent]`**
  - Advanced position sizing with dynamic risk
  - Example: `b!position_size_advanced BTC 1000 2.0`

### **🔧 Optimization**

- **`b!optimize_params [symbol] [timeframe]`**
  - Grid search parameter optimization
  - Example: `b!optimize_params BTC 1h`

- **`b!genetic_optimize <symbol> [timeframe] [generations]`**
  - Genetic algorithm optimization
  - Example: `b!genetic_optimize ETH 1h 20`

### **💰 Trading**

- **`b!advanced_buy <symbol> <quantity> [tp] [sl]`**
  - Advanced buy with TP/SL orders
  - Example: `b!advanced_buy BTC 0.01 61500 58500`

- **`b!price <symbol>`** - Get current price
- **`b!balance`** - Check account balance
- **`b!test_connection`** - Test exchange connectivity

### **📈 Charting & Visualization**

- **`b!chart <symbol> [interval] [limit]`**
  - Generate price charts
  - Example: `b!chart ETH 4h 50`

- **`b!indicator_chart <indicator> <symbol> [interval]`**
  - Chart with indicator visualization
  - Example: `b!indicator_chart macd ETH 4h`

- **`b!strategy_chart <strategy> <symbol> [interval]`**
  - Chart with strategy signals
  - Example: `b!strategy_chart bollinger_bands ETH 4h`

## ⚙️ Configuration System

The bot uses a sophisticated configuration system combining YAML files and environment variables:

### **YAML Configuration (`src/config/config.yml`)**
```yaml
trading:
  risk_management:
    max_risk_per_trade: 0.02
    max_daily_loss: 0.05
    max_positions: 5
  
  indicators:
    rsi:
      period: 14
      overbought: 70
      oversold: 30
    
  symbols: ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
  timeframes:
    primary: "1h"
    secondary: "4h"

discord:
  command_prefix: "b!"
  channels:
    signals: "signals"
    alerts: "alerts"
```

### **Environment Override Support**
Environment variables automatically override YAML settings:
- `SYMBOLS=BTC,ETH,SOL` → Updates trading symbols
- `MAX_RISK_PER_TRADE=0.01` → Updates risk per trade
- `SANDBOX=false` → Switches to live trading

## 🔧 Demo Mode

Without Binance API credentials, the bot runs in **demo mode**:
- ✅ Real market data for analysis
- ✅ Signal generation with live prices  
- ✅ Full technical analysis capabilities
- ⚠️ Simulated account data
- ❌ No actual trading execution

## 📊 Signal Format

Professional trading signals are formatted like this:

```
SC01 trading signals [Reina]
🟢 BTC - SC02
Entry: 43250.50 - TP (2R): 43856.25 - SL: 42947.88
Imminent (Sắp vào Entry): 1
Ratio (Tỉ lệ): 0.89%
Status (Trạng thái): takeprofit
By Reina~
```

## 🚀 Hosting & Deployment

### **Quick Deployment Options**

#### **🐳 Docker (Recommended)**
```bash
# Development
./scripts/deploy.sh docker-dev

# Production with monitoring
./scripts/deploy.sh docker-prod
```

#### **☁️ Cloud Platforms**
- **Heroku**: One-click deployment with `./scripts/deploy.sh heroku`
- **AWS**: EC2, ECS, or Lambda deployment options
- **Google Cloud**: Compute Engine or Cloud Run
- **DigitalOcean**: VPS deployment with automated setup

#### **🖥️ VPS Deployment**
```bash
# Ubuntu 20.04/22.04 LTS
curl -sSL https://raw.githubusercontent.com/your-repo/scripts/install-vps.sh | bash
```

### **Hosting Requirements**
```
Minimum:     Recommended:
1 vCPU       2 vCPU
1GB RAM      2GB RAM  
20GB SSD     40GB SSD
Ubuntu LTS   Ubuntu 22.04 LTS
```

### **Production Features**
- ✅ **Docker containerization** with multi-stage builds
- ✅ **PostgreSQL** database with optimized settings
- ✅ **Redis caching** for performance
- ✅ **Nginx reverse proxy** with SSL/TLS
- ✅ **Prometheus & Grafana** monitoring stack
- ✅ **Automated backups** and log rotation
- ✅ **Health checks** and auto-restart
- ✅ **Security hardening** with non-root containers

**📖 Complete hosting guide: [doc/en/setup/hosting.md](doc/en/setup/hosting.md)**

## 🔐 Security Features

- **Encrypted API key storage** (optional)
- **Environment variable security**
- **Rate limiting** and abuse prevention
- **Secure configuration management**
- **Sandbox mode** for safe testing
- **Production security hardening**

## 🚧 Development Status

- ✅ **Core Bot**: Fully functional Discord integration
- ✅ **Configuration**: Professional YAML + env system
- ✅ **Trading Engine**: Real-time signal generation
- ✅ **Risk Management**: Dynamic position sizing
- ✅ **Technical Analysis**: 10+ indicators implemented
- ✅ **Optimization**: Genetic algorithm + grid search
- 🔄 **Machine Learning**: Basic implementation
- 🔄 **Web Dashboard**: Planned feature
- 🔄 **Advanced Backtesting**: In development

## 📚 Documentation

Comprehensive documentation is maintained in the `memory-bank/` directory:
- **Project Brief**: Core requirements and goals
- **Technical Context**: Architecture and technologies
- **Active Context**: Current development focus
- **Progress Tracking**: Implementation status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Update documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**⚡ Ready to start trading?** Run `python3 main.py` and use `b!help` in Discord! 