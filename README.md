# Professional Discord Trading Bot

A professional-grade Discord bot for cryptocurrency trading signals, analysis, and automated trading. Features advanced configuration management, multi-exchange support, and comprehensive technical analysis capabilities.

## 🎯 **Current Status: Production Ready**

✅ **Fully Operational** - All systems running smoothly with comprehensive health monitoring  
✅ **Health Server Optimized** - Intelligent port selection prevents startup conflicts  
✅ **Slash Commands Active** - Modern Discord UI with real-time trading functionality  
✅ **Multi-Exchange Support** - Unified access to crypto and forex markets  
✅ **Production Deployed** - Reliable operation with advanced error recovery

## 🚀 Key Features

-### **Modern Discord Integration**
- **Slash Commands Support** - Modern Discord UI with auto-completion and validation
- **Dual Command System** - Both `/` slash commands and `b!` prefix commands supported
- **Interactive Parameters** - Type-safe command parameters with suggestions
- **Rich Embeds** - Professional formatting with real-time data visualization
- **Health Monitoring** - Intelligent port selection with fallback mechanisms
- **Error Recovery** - Graceful handling of connection issues and conflicts

### **Trading Signals & Analysis**
- **Real-time signal generation** using live market data from multiple exchanges
- **Professional signal formatting** similar to trading channels (SC01/SC02)
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
- **Order history tracking** with comprehensive trade analytics
- **Command usage monitoring** for bot performance insights

## 🏗️ Project Structure

```
trading_bot/
├── 🚀 deployment/            # Docker & deployment configurations
│   ├── docker-compose.yml       # Development environment  
│   ├── docker-compose.prod.yml  # Production stack (full monitoring)
│   ├── docker-compose.vps.yml   # VPS optimized (lightweight)
│   ├── Dockerfile               # Main container
│   ├── Dockerfile.vps          # VPS optimized container
│   ├── vps-deployment.sh       # Automated VPS deployment script
│   ├── app.json                # Heroku deployment config
│   └── README.md               # Deployment documentation
├── ⚙️ config/                 # Configuration files
│   ├── env.example             # Environment template
│   └── README.md               # Configuration documentation
├── 📋 logs/                   # Log files & monitoring
│   └── README.md               # Log management guide
├── 🧠 memory-bank/            # AI assistant project documentation
├── 📁 src/                    # Source code
│   ├── config/                 # Configuration management
│   ├── bot/                    # Discord bot core
│   ├── trading/                # Trading engine & strategies
│   ├── tests/                  # Test suites
│   └── utils/                  # Utilities
├── 📊 data/                   # Market data & databases
├── 📈 results/                # Trading results & analytics
├── 🗂️ legacy/                 # Legacy code (archived)
├── 🧪 tests/                  # Unit & integration tests
├── 📖 doc/                    # Comprehensive documentation
├── 🛠️ scripts/               # Utility scripts
├── main.py                    # Bot entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### **📁 Organized Structure Benefits:**
- **🚀 deployment/** - All Docker & hosting configs in one place
- **⚙️ config/** - Centralized configuration management  
- **📋 logs/** - Structured log file organization
- **🧠 memory-bank/** - AI assistant maintains project context
- **📖 doc/** - Comprehensive documentation (English + Vietnamese)

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
   cp config/env.example .env
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
cd deployment/
docker compose up -d

# Or use the automated VPS deployment
cd deployment/
chmod +x vps-deployment.sh
./vps-deployment.sh
```

### **Production Deployment**
```bash
# Deploy to production with Docker (full monitoring stack)
cd deployment/
docker compose -f docker-compose.prod.yml up -d

# Deploy to VPS (lightweight)
cd deployment/
docker compose -f docker-compose.vps.yml up -d

# Heroku one-click deployment (see app.json)
# Click the Deploy to Heroku button
```

The bot will:
- ✅ Load configuration from YAML and environment variables
- ✅ Connect to Discord
- ✅ Initialize trading components
- ✅ Start health server with intelligent port selection
- ✅ Sync slash commands automatically
- ✅ Begin listening for commands

**Health Monitoring:**
- Health server runs on http://localhost:8080/health (or next available port)
- Automatic port fallback to 8081, 8082, 8083, 8084 if needed
- Real-time status monitoring with uptime tracking

## 🌐 Hosting & Deployment

### **🚀 Quick Deployment Options**

#### **Option 1: One-Click Heroku Deployment**
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

#### **Option 2: Docker Deployment**
```bash
# Development environment
cd deployment/
docker compose up -d

# Production with monitoring stack
cd deployment/
docker compose -f docker-compose.prod.yml up -d

# VPS optimized (lightweight)
cd deployment/
docker compose -f docker-compose.vps.yml up -d
```

#### **Option 3: Automated VPS Deployment**
```bash
# One-command VPS setup for cfp.io.vn
cd deployment/
chmod +x vps-deployment.sh
./vps-deployment.sh
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

### **🔧 Quick Deployment Commands**

```bash
# Navigate to deployment directory
cd deployment/

# Local development (PostgreSQL + Redis + Adminer)
docker compose up -d

# Production (Full monitoring: Prometheus, Grafana, Nginx)
docker compose -f docker-compose.prod.yml up -d

# VPS optimized (SQLite + Redis + Watchtower)
docker compose -f docker-compose.vps.yml up -d

# Automated VPS deployment
chmod +x vps-deployment.sh && ./vps-deployment.sh

# Health monitoring
curl http://localhost:8080/health  # Check bot health
```

For detailed hosting instructions, see our **[Comprehensive Hosting Guide](doc/en/setup/hosting.md)**.

## 📋 Available Commands

All bot interactions are handled through modern **slash commands** (`/`).

### **⚡ Slash Commands (Recommended)**
Modern Discord interface with auto-completion and parameter validation:
```
/price <symbol> [exchange]           # Get real-time cryptocurrency prices
/signal <symbol> [strategy] [timeframe] # Generate professional trading signals  
/stats                               # View bot statistics and system status
/help                                # Modern help system with full feature list
```

### **💹 Trading Commands (Prefix)**
```
b!buy <symbol> <quantity>     # Place market buy order
b!sell <symbol> <quantity>    # Place market sell order  
b!price <symbol>             # Get current price
b!balance                    # Check account balance
b!orders                     # View recent order history
b!market_signals [count]     # Generate multiple market signals
b!live_signal [channel_id]   # Send live trading signal
```

### **📊 Analysis Commands (Prefix)**
```
b!chart <symbol>             # Generate price chart
b!signal <symbol>            # Generate trading signal
b!signals                    # Show recent signals
b!analyze <symbol>           # Technical analysis
b!indicators <symbol>        # Available indicators
```

### **⚙️ Configuration Commands (Prefix)**
```
b!risk <percentage>          # Set risk per trade
b!setdaily <percentage>      # Set daily loss limit
b!settings                   # View current settings
b!health                     # Bot health and status check
b!sync [guild_id]           # Sync slash commands (Admin only)
```

### **📈 Strategy Commands**
```
b!optimize <symbol>          # Optimize parameters
b!backtest <symbol>          # Run strategy backtest
b!strategy <name>            # Switch trading strategy
```

### **🔍 Information & Analytics Commands (Prefix)**
```
b!help                       # Show comprehensive help system
b!actcmd                     # Show active commands
b!inactcmd                   # Show inactive commands  
b!cmdsta                     # Show command status summary
```

### **📊 Order History & Analytics**
- **Comprehensive order tracking** with persistent history storage
- **Real-time order recording** for all trade types (market, limit, stop, OCO)
- **Command usage analytics** to monitor bot performance and user patterns
- **Rich order history display** with detailed order information and timestamps
- **Command status monitoring** showing which features are actively used

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
  command_prefix: "/"
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

- ✅ **Core Bot**: Fully functional Discord integration with dual command system
- ✅ **Slash Commands**: Modern Discord interface with auto-completion
- ✅ **Configuration**: Professional YAML + env system
- ✅ **Trading Engine**: Real-time signal generation
- ✅ **Risk Management**: Dynamic position sizing
- ✅ **Technical Analysis**: 10+ indicators implemented
- ✅ **Optimization**: Genetic algorithm + grid search
- ✅ **FinRL Integration**: Deep reinforcement learning capabilities
- 🔄 **Machine Learning**: Enhanced implementation in progress
- 🔄 **Web Dashboard**: Planned feature
- 🔄 **Advanced Backtesting**: In development

## 📚 Documentation

Comprehensive documentation is available:

### **User Guides**
- **[Slash Commands Guide](doc/en/slash-commands.md)**: Modern Discord command interface
- **[Slash Commands (Vietnamese)](doc/vi/slash-commands.md)**: Hướng dẫn lệnh slash tiếng Việt
- **[Hosting Guide](doc/en/setup/hosting.md)**: Complete deployment instructions

### **Project Documentation**
Maintained in the `memory-bank/` directory:
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