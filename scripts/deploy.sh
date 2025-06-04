#!/bin/bash

# Professional Discord Trading Bot - Deployment Script
# Supports multiple deployment targets: Docker, VPS, Heroku, Cloud platforms

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/deployment.log"

# Functions
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

check_requirements() {
    print_info "Checking deployment requirements..."
    
    # Check if .env file exists
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_warning ".env file not found. Creating from template..."
        cp "$PROJECT_ROOT/env.example" "$PROJECT_ROOT/.env"
        print_warning "Please configure your .env file before continuing deployment."
        exit 1
    fi
    
    # Check required environment variables
    source "$PROJECT_ROOT/.env"
    
    if [ -z "$DISCORD_TOKEN" ]; then
        print_error "DISCORD_TOKEN not set in .env file"
        exit 1
    fi
    
    print_success "Requirements check passed"
}

deploy_docker_dev() {
    print_info "Deploying with Docker (Development)..."
    
    cd "$PROJECT_ROOT"
    
    # Build and start development environment
    docker-compose down
    docker-compose build
    docker-compose up -d
    
    # Wait for services to be ready
    print_info "Waiting for services to start..."
    sleep 30
    
    # Check if bot is running
    if docker-compose ps | grep -q "trading_bot_dev.*Up"; then
        print_success "Bot deployed successfully in development mode"
        
        # Wait for health check
        print_info "Waiting for health check..."
        sleep 30
        
        # Test health endpoint
        if curl -f http://localhost:8080/health &> /dev/null; then
            print_success "Health check passed - Bot is healthy"
        else
            print_warning "Health check failed - Bot may still be starting"
        fi
        
        print_info "Services available at:"
        print_info "  - Bot health: http://localhost:8080/health"
        print_info "  - Bot metrics: http://localhost:8080/metrics"
        print_info "  - Adminer: http://localhost:8080 (wait for bot health server to stop first)"
        print_info "View logs with: docker-compose logs -f tradingbot"
    else
        print_error "Bot deployment failed"
        docker-compose logs tradingbot
        exit 1
    fi
}

deploy_docker_prod() {
    print_info "Deploying with Docker (Production)..."
    
    cd "$PROJECT_ROOT"
    
    # Check if .env.prod exists
    if [ ! -f ".env.prod" ]; then
        print_error ".env.prod file not found. Create it with production environment variables."
        exit 1
    fi
    
    # Build and start production environment
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml build
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    print_info "Waiting for services to start..."
    sleep 60
    
    # Check if bot is running
    if docker-compose -f docker-compose.prod.yml ps | grep -q "trading_bot_prod.*Up"; then
        print_success "Bot deployed successfully in production mode"
        
        # Wait for health check
        print_info "Waiting for health check..."
        sleep 30
        
        # Test health endpoint
        if curl -f http://localhost:8080/health &> /dev/null; then
            print_success "Health check passed - Bot is healthy"
        else
            print_warning "Health check failed - Bot may still be starting"
        fi
        
        print_info "Services available at:"
        print_info "  - Bot health: http://localhost:8080/health"
        print_info "  - Bot metrics: http://localhost:8080/metrics" 
        print_info "  - Grafana: http://localhost:3000 (admin/admin)"
        print_info "  - Prometheus: http://localhost:9090"
        print_info "View logs with: docker-compose -f docker-compose.prod.yml logs -f tradingbot"
    else
        print_error "Bot deployment failed"
        docker-compose -f docker-compose.prod.yml logs tradingbot
        exit 1
    fi
}

deploy_heroku() {
    print_info "Deploying to Heroku..."
    
    # Check if Heroku CLI is installed
    if ! command -v heroku &> /dev/null; then
        print_error "Heroku CLI not found. Please install it first."
        print_info "Visit: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    
    # Check if logged in to Heroku
    if ! heroku auth:whoami &> /dev/null; then
        print_error "Not logged in to Heroku. Please run 'heroku login' first."
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Check if Heroku app exists
    if [ -n "$HEROKU_APP_NAME" ]; then
        APP_NAME="$HEROKU_APP_NAME"
    else
        read -p "Enter your Heroku app name: " APP_NAME
    fi
    
    # Set environment variables
    print_info "Setting environment variables..."
    heroku config:set ENVIRONMENT=production --app "$APP_NAME"
    heroku config:set DISCORD_TOKEN="$DISCORD_TOKEN" --app "$APP_NAME"
    heroku config:set BINANCE_API_KEY="$BINANCE_API_KEY" --app "$APP_NAME"
    heroku config:set BINANCE_SECRET="$BINANCE_SECRET" --app "$APP_NAME"
    
    # Add addons if they don't exist
    heroku addons:create heroku-postgresql:mini --app "$APP_NAME" || true
    heroku addons:create heroku-redis:mini --app "$APP_NAME" || true
    
    # Deploy
    git add .
    git commit -m "Deploy to Heroku" || true
    git push heroku main
    
    # Scale worker
    heroku ps:scale worker=1 --app "$APP_NAME"
    
    print_success "Bot deployed to Heroku successfully"
    print_info "View logs with: heroku logs --tail --app $APP_NAME"
}

check_status() {
    print_info "Checking bot status..."
    
    # Check Docker containers
    if docker-compose ps | grep -q "trading_bot_dev.*Up"; then
        print_success "Development bot is running"
        
        # Check health endpoint
        if curl -f http://localhost:8080/health &> /dev/null; then
            health_status=$(curl -s http://localhost:8080/health | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Status: {data['status']}, Uptime: {data['uptime_seconds']}s\")")
            print_success "Health check: $health_status"
        else
            print_warning "Health endpoint not responding"
        fi
    fi
    
    if docker-compose -f docker-compose.prod.yml ps 2>/dev/null | grep -q "trading_bot_prod.*Up"; then
        print_success "Production bot is running"
        
        # Check health endpoint  
        if curl -f http://localhost:8080/health &> /dev/null; then
            health_status=$(curl -s http://localhost:8080/health | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Status: {data['status']}, Uptime: {data['uptime_seconds']}s\")")
            print_success "Health check: $health_status"
        else
            print_warning "Health endpoint not responding"
        fi
    fi
    
    # If no Docker containers, check if bot is running locally
    if pgrep -f "python.*main.py" &> /dev/null; then
        print_success "Bot process is running locally"
    else
        print_warning "No bot processes found"
    fi
}

stop_bot() {
    print_info "Stopping bot services..."
    
    # Stop Docker containers
    if docker-compose ps | grep -q "trading_bot_dev.*Up"; then
        print_info "Stopping development environment..."
        docker-compose down
        print_success "Development environment stopped"
    fi
    
    if docker-compose -f docker-compose.prod.yml ps 2>/dev/null | grep -q "trading_bot_prod.*Up"; then
        print_info "Stopping production environment..."
        docker-compose -f docker-compose.prod.yml down
        print_success "Production environment stopped"
    fi
    
    # Stop local processes
    if pgrep -f "python.*main.py" &> /dev/null; then
        print_info "Stopping local bot processes..."
        pkill -f "python.*main.py"
        print_success "Local bot processes stopped"
    fi
}

show_help() {
    echo "Professional Discord Trading Bot - Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  docker-dev     Deploy with Docker (Development)"
    echo "  docker-prod    Deploy with Docker (Production)"
    echo "  heroku        Deploy to Heroku"
    echo "  check         Check deployment requirements"
    echo "  status        Check bot status and health"
    echo "  stop          Stop all bot services"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 docker-dev"
    echo "  $0 heroku"
    echo "  $0 status"
    echo "  $0 stop"
}

# Main script
main() {
    case "${1:-help}" in
        "docker-dev")
            check_requirements
            deploy_docker_dev
            ;;
        "docker-prod")
            check_requirements
            deploy_docker_prod
            ;;
        "heroku")
            check_requirements
            deploy_heroku
            ;;
        "check")
            check_requirements
            ;;
        "status")
            check_status
            ;;
        "stop")
            stop_bot
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"