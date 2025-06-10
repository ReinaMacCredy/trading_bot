#!/bin/bash

# Discord Trading Bot - VPS Deployment Script
# Automated deployment script for cfp.io.vn VPS
# Author: Trading Bot Team
# Version: 1.0.0

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
LOG_FILE="$PROJECT_ROOT/vps-deployment.log"
BOT_USER="cfp"
BOT_DIR="/home/cfp/trading_bot"
COMPOSE_FILE="docker-compose.vps.yml"

# Functions
print_header() {
    echo -e "${PURPLE}=================================================${NC}"
    echo -e "${PURPLE}    Discord Trading Bot - VPS Deployment      ${NC}"
    echo -e "${PURPLE}=================================================${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root for security reasons"
        print_info "Please run as user 'cfp' or your designated bot user"
        exit 1
    fi
}

check_system() {
    print_info "Checking system requirements..."
    
    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        print_error "Cannot determine OS type"
        exit 1
    fi
    
    . /etc/os-release
    print_info "Detected OS: $PRETTY_NAME"
    
    # Check architecture
    ARCH=$(uname -m)
    print_info "Architecture: $ARCH"
    
    # Check available memory
    MEMORY_GB=$(free -g | awk 'NR==2{printf "%.1f", $2}')
    print_info "Available memory: ${MEMORY_GB}GB"
    
    if (( $(echo "$MEMORY_GB < 1.0" | bc -l) )); then
        print_warning "Low memory detected. Bot may require memory optimization"
    fi
    
    # Check disk space
    DISK_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    print_info "Available disk space: ${DISK_GB}GB"
    
    if (( DISK_GB < 5 )); then
        print_error "Insufficient disk space. Need at least 5GB free"
        exit 1
    fi
    
    print_success "System requirements check passed"
}

install_docker() {
    print_info "Installing Docker and Docker Compose..."
    
    if command -v docker &> /dev/null; then
        print_info "Docker already installed: $(docker --version)"
    else
        print_info "Installing Docker..."
        
        # Update package index
        sudo apt-get update
        
        # Install packages to allow apt to use a repository over HTTPS
        sudo apt-get install -y \
            ca-certificates \
            curl \
            gnupg \
            lsb-release
        
        # Add Docker's official GPG key
        sudo mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        
        # Set up the repository
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker Engine
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
        # Add user to docker group
        sudo usermod -aG docker $USER
        
        print_success "Docker installed successfully"
    fi
    
    # Verify Docker Compose
    if docker compose version &> /dev/null; then
        print_info "Docker Compose available: $(docker compose version)"
    else
        print_error "Docker Compose not available"
        exit 1
    fi
}

setup_environment() {
    print_info "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env
            print_warning ".env file created from template. Please configure it with your credentials."
            print_info "Required variables to configure:"
            print_info "  - DISCORD_TOKEN"
            print_info "  - BINANCE_API_KEY"
            print_info "  - BINANCE_SECRET"
            
            read -p "Press Enter when you have configured the .env file..."
        else
            print_error "env.example not found. Cannot create .env file."
            exit 1
        fi
    fi
    
    # Validate required environment variables
    source .env
    
    if [ -z "$DISCORD_TOKEN" ] || [ "$DISCORD_TOKEN" = "your_discord_bot_token_here" ]; then
        print_error "DISCORD_TOKEN not properly configured in .env file"
        exit 1
    fi
    
    if [ -z "$BINANCE_API_KEY" ] || [ "$BINANCE_API_KEY" = "your_binance_api_key_here" ]; then
        print_warning "BINANCE_API_KEY not configured. Using demo mode."
    fi
    
    # Create necessary directories
    mkdir -p logs data results
    chmod 755 logs data results
    
    print_success "Environment setup completed"
}

build_and_deploy() {
    print_info "Building and deploying bot..."
    
    # Stop any existing containers
    if docker compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        print_info "Stopping existing containers..."
        docker compose -f "$COMPOSE_FILE" down
    fi
    
    # Remove old images to save space
    print_info "Cleaning up old Docker images..."
    docker image prune -f
    
    # Build the application
    print_info "Building bot image..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    
    # Start the services
    print_info "Starting services..."
    docker compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to start
    print_info "Waiting for services to start..."
    sleep 30
    
    # Check health
    check_health
}

check_health() {
    print_info "Performing health checks..."
    
    # Check if containers are running
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "trading_bot_vps.*Up"; then
        print_success "Bot container is running"
    else
        print_error "Bot container failed to start"
        print_info "Container logs:"
        docker compose -f "$COMPOSE_FILE" logs tradingbot
        exit 1
    fi
    
    # Wait for health check endpoint
    print_info "Waiting for health check endpoint..."
    for i in {1..30}; do
        if curl -f http://localhost:8080/health &> /dev/null; then
            print_success "Health check passed - Bot is healthy"
            break
        fi
        
        if [ $i -eq 30 ]; then
            print_warning "Health check endpoint not responding. Bot may still be starting."
            print_info "Check logs: docker compose -f $COMPOSE_FILE logs tradingbot"
        else
            sleep 5
        fi
    done
}

setup_systemd() {
    print_info "Setting up systemd service..."
    
    # Create systemd service file
    sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<EOF
[Unit]
Description=Discord Trading Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PWD
ExecStart=/usr/bin/docker compose -f $COMPOSE_FILE up -d
ExecStop=/usr/bin/docker compose -f $COMPOSE_FILE down
TimeoutStartSec=0
User=$USER
Group=docker

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable trading-bot.service
    
    print_success "Systemd service configured"
    print_info "Use 'sudo systemctl start trading-bot' to start"
    print_info "Use 'sudo systemctl stop trading-bot' to stop"
    print_info "Use 'sudo systemctl status trading-bot' to check status"
}

setup_monitoring() {
    print_info "Setting up monitoring scripts..."
    
    # Create monitoring script
    cat > monitor_bot.sh << 'EOF'
#!/bin/bash

# Bot monitoring script
COMPOSE_FILE="docker-compose.vps.yml"

check_bot_status() {
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "trading_bot_vps.*Up"; then
        echo "✅ Bot is running"
        
        # Check health endpoint
        if curl -f http://localhost:8080/health &> /dev/null; then
            echo "✅ Health check passed"
        else
            echo "⚠️  Health check failed"
        fi
    else
        echo "❌ Bot is not running"
        echo "Starting bot..."
        docker compose -f "$COMPOSE_FILE" up -d
    fi
}

show_logs() {
    echo "Recent bot logs:"
    docker compose -f "$COMPOSE_FILE" logs --tail=20 tradingbot
}

show_stats() {
    echo "Container stats:"
    docker stats --no-stream $(docker compose -f "$COMPOSE_FILE" ps -q)
}

case "$1" in
    status)
        check_bot_status
        ;;
    logs)
        show_logs
        ;;
    stats)
        show_stats
        ;;
    restart)
        echo "Restarting bot..."
        docker compose -f "$COMPOSE_FILE" restart tradingbot
        ;;
    *)
        echo "Usage: $0 {status|logs|stats|restart}"
        exit 1
        ;;
esac
EOF
    
    chmod +x monitor_bot.sh
    
    # Create log rotation config
    sudo tee /etc/logrotate.d/trading-bot > /dev/null <<EOF
$PWD/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
    
    print_success "Monitoring setup completed"
    print_info "Use './monitor_bot.sh status' to check bot status"
    print_info "Use './monitor_bot.sh logs' to view recent logs"
    print_info "Use './monitor_bot.sh stats' to view resource usage"
}

show_deployment_info() {
    print_success "🎉 VPS Deployment completed successfully!"
    echo ""
    print_info "📊 Deployment Summary:"
    print_info "  - Bot Status: $(docker compose -f "$COMPOSE_FILE" ps tradingbot --format 'table {{.State}}')"
    print_info "  - Health Endpoint: http://localhost:8080/health"
    print_info "  - Logs: docker compose -f $COMPOSE_FILE logs tradingbot"
    print_info "  - Monitor: ./monitor_bot.sh status"
    echo ""
    print_info "🔧 Management Commands:"
    print_info "  - View logs: docker compose -f $COMPOSE_FILE logs -f tradingbot"
    print_info "  - Restart bot: docker compose -f $COMPOSE_FILE restart tradingbot"
    print_info "  - Stop bot: docker compose -f $COMPOSE_FILE down"
    print_info "  - Update bot: git pull && docker compose -f $COMPOSE_FILE up -d --build"
    echo ""
    print_info "🔍 Monitoring:"
    print_info "  - ./monitor_bot.sh status - Check bot status"
    print_info "  - ./monitor_bot.sh logs - View recent logs"
    print_info "  - ./monitor_bot.sh stats - View resource usage"
    echo ""
    print_info "⚙️  Systemd Service:"
    print_info "  - sudo systemctl start trading-bot"
    print_info "  - sudo systemctl stop trading-bot"
    print_info "  - sudo systemctl status trading-bot"
}

# Main execution
main() {
    print_header
    
    print_info "Starting VPS deployment process..."
    echo "Deployment log: $LOG_FILE" | tee "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    check_root
    check_system
    install_docker
    setup_environment
    build_and_deploy
    setup_systemd
    setup_monitoring
    show_deployment_info
    
    print_success "🚀 Bot is now running on your VPS!"
}

# Run main function
main "$@" 