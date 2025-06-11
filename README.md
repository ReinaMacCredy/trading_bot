# Professional Discord Trading Bot

A comprehensive trading platform combining Discord bot functionality with HTTPS web server capabilities for automated trading. Features TradingView webhook integration, Redis-based order management, advanced technical analysis, and professional-grade architecture for both community interaction and automated trading execution.

## 🎯 **Current Status: Implementation Ready - Testing Phase Execution**

✅ **Level 3 Planning Complete** - Comprehensive strategic planning for Testing, Deployment, and Security phases  
✅ **HTTPS Trading Server** - Complete FastAPI-based web server with TradingView webhook integration  
✅ **Redis Order Management** - Professional order queuing system with intelligent matching engine  
✅ **Dual Interface Architecture** - Discord for community signals, Web for automated trading  
✅ **Microservices Pattern** - Independent services with shared trading infrastructure  
🚀 **Testing Phase Starting** - Week 1 execution beginning with unit test suite development and infrastructure setup  
🎯 **Implementation Roadmap Active** - 6-week structured roadmap with weekly milestones and deliverables

## 🚀 Key Features

### **🌐 HTTPS Trading Server & Automation** (COMPLETE - PRODUCTION READY)
- **FastAPI Web Server** - Modern async web framework with automatic API documentation
- **TradingView Webhook Integration** - Real-time webhook processing for TradingView alerts
- **Redis Order Management** - Persistent order queuing with multi-state tracking (pending, matched, executed, failed)
- **Intelligent Order Matching** - Background processing engine that matches orders against TradingView signals
- **RESTful API Interface** - Complete order management API with CRUD operations and real-time status tracking
- **SSL/TLS Support** - Production-ready HTTPS server with certificate management
- **Automated Trading Execution** - Signal-based conditional order execution with risk management
- **Microservices Architecture** - Independent Discord bot and web server with shared trading infrastructure

### **🤖 Modern Discord Integration**
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
│   ├── docker-compose.web.yml   # Web server specific deployment
│   ├── Dockerfile               # Main container
│   ├── Dockerfile.vps          # VPS optimized container
│   ├── Dockerfile.web          # Web server container
│   ├── vps-deployment.sh       # Automated VPS deployment script
│   ├── app.json                # Heroku deployment config
│   └── README.md               # Deployment documentation
├── ⚙️ config/                 # Configuration files
│   ├── env.example             # Environment template
│   ├── web_config.yaml         # Web server configuration
│   └── README.md               # Configuration documentation
├── 📋 logs/                   # Log files & monitoring
│   └── README.md               # Log management guide
├── 🧠 memory-bank/            # AI assistant project documentation
├── 📁 src/                    # Source code
│   ├── config/                 # Configuration management
│   ├── bot/                    # Discord bot core
│   ├── web/                    # HTTPS web server (NEW)
│   │   ├── api/                # API endpoints
│   │   ├── services/           # Business logic services
│   │   ├── models/             # Data models
│   │   ├── handlers/           # Request handlers
│   │   └── main.py             # FastAPI application
│   ├── trading/                # Trading engine & strategies
│   ├── tests/                  # Test suites
│   └── utils/                  # Utilities
├── 📊 data/                   # Market data & databases
├── 📈 results/                # Trading results & analytics
├── 🗂️ legacy/                 # Legacy code (archived)
├── 🧪 tests/                  # Unit & integration tests
├── 📖 doc/                    # Comprehensive documentation
├── 📄 docs/                   # Additional documentation
│   └── WEB_SERVER.md           # Web server documentation
├── 🛠️ scripts/               # Utility scripts
├── main.py                    # Discord bot entry point
├── web_server.py              # Web server entry point (NEW)
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

# Web Server Configuration (NEW)
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=8000
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem

# Redis Configuration (NEW)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# TradingView Integration (NEW)
TRADINGVIEW_WEBHOOK_SECRET=your_webhook_secret

# Trading Configuration
MAX_RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
ENABLE_PAPER_TRADING=true

# Environment Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 🚀 Running the Platform

### **Option 1: Discord Bot Only**
```bash
# Start Discord bot
python3 main.py
```

### **Option 2: Web Server Only**
```bash
# Start HTTPS web server
python3 web_server.py --host 0.0.0.0 --port 8000

# With SSL (production)
python3 web_server.py --host 0.0.0.0 --port 8000 \
  --ssl-cert /path/to/cert.pem \
  --ssl-key /path/to/key.pem
```

### **Option 3: Full Platform (Both Services)**
```bash
# Terminal 1: Start Redis
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Terminal 2: Start Web Server
python3 web_server.py --host 0.0.0.0 --port 8000

# Terminal 3: Start Discord Bot
python3 main.py
```

### **Docker Development**
```bash
# Full stack with both services
cd deployment/
docker compose up -d

# Web server only
cd deployment/
docker compose -f docker-compose.web.yml up -d

# Automated VPS deployment
cd deployment/
chmod +x vps-deployment.sh
./vps-deployment.sh
```

### **Production Deployment**
```bash
# Full production stack (Discord + Web + Monitoring)
cd deployment/
docker compose -f docker-compose.prod.yml up -d

# VPS optimized (lightweight)
cd deployment/
docker compose -f docker-compose.vps.yml up -d

# Heroku one-click deployment
# Click the Deploy to Heroku button
```

**Service Status:**
- **Discord Bot**: Connects to Discord, syncs slash commands, starts health server
- **Web Server**: FastAPI server on port 8000 with API documentation at `/docs`
- **Redis**: Order queue management and signal storage
- **Health Monitoring**: Multiple endpoints for system status

**Access Points:**
- Discord Bot: Available in your Discord server
- Web API: http://localhost:8000/docs (API documentation)
- Health Check: http://localhost:8080/health (Discord bot health)
- Web Health: http://localhost:8000/status/health (Web server health)

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

## 📋 Available Interfaces

The platform provides multiple interfaces for different use cases:

### **🌐 Web API Endpoints** (NEW - Automated Trading)
RESTful API for automated trading and TradingView integration:
```
POST /webhooks/tradingview          # Receive TradingView alerts
POST /orders/create                 # Create new trading order
GET  /orders/status/{order_id}      # Get order status
PUT  /orders/cancel/{order_id}      # Cancel pending order
GET  /orders/user/{user_id}         # Get user order history
GET  /orders/queue/stats            # View queue statistics
GET  /status/health                 # Web server health check
GET  /docs                          # Interactive API documentation
```

### **⚡ Discord Slash Commands** (Community Interface)
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

### **✅ Completed Infrastructure (Production Ready)**
- ✅ **HTTPS Trading Server**: Complete FastAPI-based web server with TradingView webhooks
- ✅ **Redis Order Management**: Professional order queuing with intelligent matching engine
- ✅ **Automated Trading**: TradingView signal processing with conditional order execution
- ✅ **Microservices Architecture**: Dual-interface platform with shared trading infrastructure
- ✅ **Core Bot**: Fully functional Discord integration with dual command system
- ✅ **Slash Commands**: Modern Discord interface with auto-completion
- ✅ **Configuration**: Professional YAML + env system
- ✅ **Trading Engine**: Real-time signal generation
- ✅ **Risk Management**: Dynamic position sizing
- ✅ **Technical Analysis**: 10+ indicators implemented
- ✅ **Optimization**: Genetic algorithm + grid search
- ✅ **FinRL Integration**: Deep reinforcement learning capabilities

### **🚀 Current Implementation (Week 1-2: Testing Phase)**
- 🚀 **Unit Test Suite Development**: Comprehensive test coverage for Redis service, order matching, API endpoints
- 🚀 **Test Infrastructure Setup**: Docker test environment with mock services and realistic data
- 🚀 **Integration Testing**: End-to-end TradingView webhook processing validation
- 🚀 **Performance Testing**: Load testing infrastructure and baseline establishment
- 🚀 **API Endpoint Testing**: Comprehensive validation of webhook and order management endpoints

### **⏳ Planned Implementation (Week 3-6)**
- ⏳ **Production Deployment** (Week 3-4): SSL certificates, Redis production setup, monitoring implementation
- ⏳ **Security & Optimization** (Week 5-6): Authentication, webhook verification, performance optimization
- 🔄 **Web Frontend Dashboard**: User interface for order management (post-security phase)
- 🔄 **Advanced Authentication**: User management and permissions (Week 5-6)
- 🔄 **Machine Learning**: Enhanced implementation in progress
- 🔄 **Advanced Backtesting**: In development

## 📚 Documentation

Comprehensive documentation is available:

### **User Guides**
- **[HTTPS Web Server Guide](docs/WEB_SERVER.md)**: Complete web server documentation and API reference
- **[Slash Commands Guide](doc/en/slash-commands.md)**: Modern Discord command interface
- **[Slash Commands (Vietnamese)](doc/vi/slash-commands.md)**: Hướng dẫn lệnh slash tiếng Việt
- **[Hosting Guide](doc/en/setup/hosting.md)**: Complete deployment instructions

### **Technical Documentation**
- **[Web Server API](docs/WEB_SERVER.md)**: FastAPI server, TradingView webhooks, and order management
- **[Configuration Guide](doc/en/setup/configuration.md)**: YAML and environment variable setup
- **[Architecture Overview](memory-bank/systemPatterns.md)**: Microservices pattern and component design

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

## 🎯 Current Implementation Roadmap

### **Week 1-2: Testing Phase (Current)**
**Focus**: Comprehensive testing infrastructure development and validation
- **Unit Testing**: pytest framework setup with async FastAPI support
- **Integration Testing**: End-to-end TradingView webhook processing validation
- **Performance Testing**: Load testing infrastructure and baseline establishment
- **Success Criteria**: >95% test coverage, <100ms webhook processing, 100% integration success

### **Week 3-4: Production Deployment**
**Focus**: Production infrastructure setup and deployment automation
- **SSL Configuration**: HTTPS setup with Let's Encrypt certificate management
- **Redis Production**: Persistent storage with authentication and backup procedures
- **Monitoring**: Comprehensive system health monitoring and alerting implementation
- **Success Criteria**: 99.9% uptime target, automated deployment, comprehensive monitoring

### **Week 5-6: Security & Optimization**
**Focus**: Security hardening and performance optimization
- **Authentication**: JWT-based user authentication and role-based authorization
- **Security Testing**: Webhook verification, rate limiting, penetration testing
- **Performance**: Caching strategies and resource optimization
- **Success Criteria**: Security audit passed, performance targets met, production validated

---

**⚡ Ready to start trading?** 

**Discord Interface**: Run `python3 main.py` and use `/help` in Discord!  
**Web API**: Run `python3 web_server.py` and visit `http://localhost:8000/docs`!  
**Full Platform**: Use Docker Compose for both services: `cd deployment && docker compose up -d`!  
**Testing Phase**: Follow the Week 1-2 roadmap to contribute to testing infrastructure development! 