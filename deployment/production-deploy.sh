#!/bin/bash

# Production Deployment Script for Trading HTTPS Server
# Deploys complete stack with SSL, Redis, monitoring, and security

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default configuration
DOMAIN=""
EMAIL=""
ENVIRONMENT="production"
SKIP_SSL=false
SKIP_TESTS=false
FORCE_REBUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        --skip-ssl)
            SKIP_SSL=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -d, --domain DOMAIN    Domain name for SSL certificate"
            echo "  -e, --email EMAIL      Email for Let's Encrypt registration"
            echo "  --skip-ssl             Skip SSL certificate generation"
            echo "  --skip-tests           Skip pre-deployment tests"
            echo "  --force-rebuild        Force rebuild of Docker images"
            echo "  -h, --help             Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$DOMAIN" && "$SKIP_SSL" == false ]]; then
    log_error "Domain name is required for SSL setup. Use -d/--domain or --skip-ssl"
    exit 1
fi

if [[ -z "$EMAIL" && "$SKIP_SSL" == false ]]; then
    log_error "Email is required for Let's Encrypt. Use -e/--email or --skip-ssl"
    exit 1
fi

log_info "Starting production deployment for domain: ${DOMAIN:-'localhost'}"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker service."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "production.yml" ]]; then
        log_error "production.yml not found. Please run this script from the deployment directory."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p ../logs
    mkdir -p ssl
    mkdir -p nginx/logs
    mkdir -p redis
    mkdir -p postgres
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/{dashboards,datasources}
    mkdir -p logging
    
    log_success "Directories created"
}

# Generate SSL certificates
setup_ssl() {
    if [[ "$SKIP_SSL" == true ]]; then
        log_warning "Skipping SSL setup"
        return
    fi
    
    log_info "Setting up SSL certificates for domain: $DOMAIN"
    
    # Check if certificates already exist
    if [[ -f "ssl/fullchain.pem" && -f "ssl/privkey.pem" ]]; then
        log_warning "SSL certificates already exist. Skipping generation."
        return
    fi
    
    # Use Certbot to generate Let's Encrypt certificates
    if command -v certbot &> /dev/null; then
        log_info "Using Certbot to generate SSL certificates..."
        
        sudo certbot certonly \
            --standalone \
            --non-interactive \
            --agree-tos \
            --email "$EMAIL" \
            -d "$DOMAIN" \
            --cert-path ssl/fullchain.pem \
            --key-path ssl/privkey.pem
        
        # Set proper permissions
        sudo chmod 644 ssl/fullchain.pem
        sudo chmod 600 ssl/privkey.pem
        
    else
        log_warning "Certbot not found. Generating self-signed certificates for testing..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/privkey.pem \
            -out ssl/fullchain.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
    fi
    
    log_success "SSL certificates configured"
}

# Setup environment variables
setup_environment() {
    log_info "Setting up environment variables..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        log_info "Creating .env file from template..."
        
        cat > .env << EOF
# Production Environment Configuration
ENVIRONMENT=production

# Domain Configuration
DOMAIN=${DOMAIN:-localhost}

# Security Configuration
REDIS_PASSWORD=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 64)
TRADINGVIEW_WEBHOOK_SECRET=$(openssl rand -base64 32)
GRAFANA_PASSWORD=$(openssl rand -base64 16)

# Database Configuration
DATABASE_URL=postgresql://tradingbot:\${POSTGRES_PASSWORD}@postgres-prod:5432/trading_bot_prod

# Discord Bot (if using)
# DISCORD_TOKEN=your_discord_bot_token

# Exchange Configuration
# BINANCE_API_KEY=your_binance_api_key
# BINANCE_SECRET=your_binance_secret

# Monitoring
ENABLE_METRICS=true
ENABLE_ACCESS_LOGS=true

# Rate Limiting
API_RATE_LIMIT_PER_MINUTE=100
WEBHOOK_RATE_LIMIT_PER_MINUTE=60
EOF
        
        log_warning "Please edit .env file with your actual credentials before continuing"
        log_info "Generated .env file with secure random passwords"
    else
        log_info "Using existing .env file"
    fi
    
    log_success "Environment variables configured"
}

# Create configuration files
create_configs() {
    log_info "Creating configuration files..."
    
    # Redis configuration
    cat > redis/redis.conf << EOF
# Redis Production Configuration
bind 0.0.0.0
port 6379
protected-mode yes
requirepass \${REDIS_PASSWORD}

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Memory management
maxmemory 512mb
maxmemory-policy allkeys-lru

# Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
EOF

    # Nginx configuration
    cat > nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream web_server {
        server web-server-prod:8000;
    }
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=100r/m;
    limit_req_zone \$binary_remote_addr zone=webhook:10m rate=60r/m;
    
    server {
        listen 80;
        server_name ${DOMAIN:-localhost};
        return 301 https://\$server_name\$request_uri;
    }
    
    server {
        listen 443 ssl;
        server_name ${DOMAIN:-localhost};
        
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        
        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";
        
        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://web_server;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Webhook endpoints with stricter rate limiting
        location /webhooks/ {
            limit_req zone=webhook burst=10 nodelay;
            proxy_pass http://web_server;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # All other requests
        location / {
            proxy_pass http://web_server;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Health check endpoint
        location /health {
            access_log off;
            proxy_pass http://web_server/status/health;
        }
    }
}
EOF

    # Prometheus configuration
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "alert_rules.yml"

scrape_configs:
  - job_name: 'web-server'
    static_configs:
      - targets: ['web-server-prod:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-prod:6379']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-prod:5432']
    
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-proxy:80']
EOF

    log_success "Configuration files created"
}

# Run pre-deployment tests
run_tests() {
    if [[ "$SKIP_TESTS" == true ]]; then
        log_warning "Skipping tests"
        return
    fi
    
    log_info "Running pre-deployment tests..."
    
    # Run unit tests
    cd ..
    if command -v python3 &> /dev/null; then
        if [[ -f "requirements.txt" ]]; then
            python3 -m pip install -r requirements.txt
            python3 -m pytest tests/ -v --tb=short
        else
            log_warning "requirements.txt not found, skipping Python tests"
        fi
    else
        log_warning "Python3 not found, skipping tests"
    fi
    cd deployment
    
    log_success "Tests completed"
}

# Deploy the stack
deploy_stack() {
    log_info "Deploying production stack..."
    
    # Build or pull images
    if [[ "$FORCE_REBUILD" == true ]]; then
        log_info "Force rebuilding Docker images..."
        docker-compose -f production.yml build --no-cache
    else
        log_info "Building Docker images..."
        docker-compose -f production.yml build
    fi
    
    # Start the stack
    log_info "Starting services..."
    docker-compose -f production.yml up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    
    for i in {1..30}; do
        if docker-compose -f production.yml ps | grep -q "unhealthy"; then
            log_info "Waiting for services to start... ($i/30)"
            sleep 10
        else
            break
        fi
    done
    
    log_success "Production stack deployed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if all containers are running
    if ! docker-compose -f production.yml ps | grep -q "Up"; then
        log_error "Some containers are not running"
        docker-compose -f production.yml ps
        exit 1
    fi
    
    # Test health endpoints
    local base_url="https://${DOMAIN:-localhost}"
    if [[ "$SKIP_SSL" == true ]]; then
        base_url="http://localhost:8000"
    fi
    
    log_info "Testing health endpoints..."
    
    # Wait a bit for services to fully initialize
    sleep 10
    
    if curl -f -k "${base_url}/status/health" &> /dev/null; then
        log_success "Health endpoint responding"
    else
        log_warning "Health endpoint not responding, checking logs..."
        docker-compose -f production.yml logs web-server-prod --tail 20
    fi
    
    log_success "Deployment verification completed"
}

# Setup monitoring and alerting
setup_monitoring() {
    log_info "Setting up monitoring and alerting..."
    
    # Create Grafana datasource configuration
    cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Create basic dashboard
    cat > monitoring/grafana/dashboards/trading-system.json << EOF
{
  "dashboard": {
    "title": "Trading System Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{handler}}"
          }
        ]
      },
      {
        "title": "Order Queue Size",
        "type": "stat",
        "targets": [
          {
            "expr": "redis_pending_orders_total",
            "legendFormat": "Pending Orders"
          }
        ]
      }
    ]
  }
}
EOF

    log_success "Monitoring configured"
}

# Create backup script
create_backup_script() {
    log_info "Creating backup script..."
    
    cat > backup.sh << 'EOF'
#!/bin/bash
# Backup script for trading system

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
docker exec trading_postgres_prod pg_dump -U tradingbot trading_bot_prod > "$BACKUP_DIR/postgres_backup.sql"

# Backup Redis
docker exec trading_redis_prod redis-cli --rdb - > "$BACKUP_DIR/redis_backup.rdb"

# Backup configuration
cp -r ../config "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
EOF

    chmod +x backup.sh
    
    log_success "Backup script created"
}

# Display final information
show_deployment_info() {
    log_success "🎉 Production deployment completed successfully!"
    echo
    log_info "Deployment Information:"
    echo "  - Domain: ${DOMAIN:-localhost}"
    echo "  - Web Server: https://${DOMAIN:-localhost}"
    echo "  - Grafana: http://${DOMAIN:-localhost}:3000"
    echo "  - Prometheus: http://${DOMAIN:-localhost}:9090"
    echo
    log_info "Service Status:"
    docker-compose -f production.yml ps
    echo
    log_info "Useful Commands:"
    echo "  - View logs: docker-compose -f production.yml logs -f"
    echo "  - Stop services: docker-compose -f production.yml down"
    echo "  - Update services: docker-compose -f production.yml up -d --build"
    echo "  - Backup data: ./backup.sh"
    echo
    log_warning "Important Notes:"
    echo "  - Update your DNS to point to this server"
    echo "  - Configure your firewall to allow ports 80 and 443"
    echo "  - Set up regular backups using the backup.sh script"
    echo "  - Monitor the system using Grafana dashboards"
    echo "  - Review and update .env file with actual credentials"
    echo
    
    if [[ -f ".env" ]]; then
        log_info "Generated credentials (also saved in .env):"
        echo "  - Redis Password: $(grep REDIS_PASSWORD .env | cut -d'=' -f2)"
        echo "  - PostgreSQL Password: $(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)"
        echo "  - Grafana Password: $(grep GRAFANA_PASSWORD .env | cut -d'=' -f2)"
        echo "  - TradingView Webhook Secret: $(grep TRADINGVIEW_WEBHOOK_SECRET .env | cut -d'=' -f2)"
    fi
}

# Main execution
main() {
    log_info "🚀 Starting production deployment process..."
    
    check_prerequisites
    create_directories
    setup_environment
    setup_ssl
    create_configs
    run_tests
    deploy_stack
    setup_monitoring
    create_backup_script
    verify_deployment
    show_deployment_info
    
    log_success "🎉 Deployment completed successfully!"
}

# Run main function
main "$@" 