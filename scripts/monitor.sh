#!/bin/bash

# Professional Discord Trading Bot - Monitoring Script
# Continuous health monitoring with alerting capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/monitoring.log"
HEALTH_URL="http://localhost:8080/health"
METRICS_URL="http://localhost:8080/metrics"
CHECK_INTERVAL=30  # seconds
ALERT_THRESHOLD=3  # failed checks before alert

# Counters
failed_checks=0
total_checks=0
last_alert_time=0

# Functions
log_message() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

print_info() {
    log_message "${BLUE}[INFO]${NC} $1"
}

print_success() {
    log_message "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    log_message "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    log_message "${RED}[ERROR]${NC} $1"
}

check_health() {
    local health_response
    local status_code
    
    # Increment total checks
    ((total_checks++))
    
    # Check if health endpoint is responding
    if health_response=$(curl -s -w "%{http_code}" "$HEALTH_URL" 2>/dev/null); then
        status_code="${health_response: -3}"
        health_data="${health_response%???}"
        
        if [ "$status_code" = "200" ]; then
            # Parse health data
            if command -v python3 &> /dev/null; then
                bot_status=$(echo "$health_data" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null || echo "unknown")
                uptime=$(echo "$health_data" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('uptime_seconds', 0))" 2>/dev/null || echo "0")
                bot_ready=$(echo "$health_data" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('bot_ready', False))" 2>/dev/null || echo "false")
            else
                bot_status="unknown"
                uptime="0"
                bot_ready="false"
            fi
            
            if [ "$bot_status" = "healthy" ]; then
                print_success "Bot is healthy - Uptime: ${uptime}s, Ready: $bot_ready"
                failed_checks=0
                return 0
            else
                print_warning "Bot reports unhealthy status: $bot_status"
                ((failed_checks++))
                return 1
            fi
        else
            print_error "Health endpoint returned status code: $status_code"
            ((failed_checks++))
            return 1
        fi
    else
        print_error "Health endpoint not responding"
        ((failed_checks++))
        return 1
    fi
}

send_alert() {
    local message="$1"
    local current_time=$(date +%s)
    
    # Rate limit alerts (minimum 5 minutes between alerts)
    if [ $((current_time - last_alert_time)) -lt 300 ]; then
        return
    fi
    
    last_alert_time=$current_time
    
    print_error "ALERT: $message"
    
    # You can extend this to send Discord notifications, emails, etc.
    # For example:
    # curl -X POST -H 'Content-type: application/json' \
    #   --data "{\"text\":\"🚨 Bot Alert: $message\"}" \
    #   "$DISCORD_WEBHOOK_URL"
}

check_docker_containers() {
    # Check if Docker containers are running
    if command -v docker-compose &> /dev/null; then
        if docker-compose ps 2>/dev/null | grep -q "trading_bot.*Up"; then
            print_info "Docker containers are running"
            return 0
        elif docker-compose -f docker-compose.prod.yml ps 2>/dev/null | grep -q "trading_bot.*Up"; then
            print_info "Production Docker containers are running"
            return 0
        else
            print_warning "No Docker containers found running"
            return 1
        fi
    fi
    return 1
}

check_local_process() {
    # Check if bot is running locally
    if pgrep -f "python.*main.py" &> /dev/null; then
        print_info "Local bot process is running"
        return 0
    else
        print_warning "No local bot process found"
        return 1
    fi
}

get_system_metrics() {
    if command -v python3 &> /dev/null; then
        # Get system resource usage
        python3 << 'EOF'
import psutil
import json
import sys

try:
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics = {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_available_gb": round(memory.available / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 2)
    }
    
    print(json.dumps(metrics))
except Exception as e:
    print(f'{{"error": "{e}"}}')
EOF
    fi
}

show_summary() {
    print_info "=== Monitoring Summary ==="
    print_info "Total checks: $total_checks"
    print_info "Failed checks: $failed_checks"
    
    if [ $total_checks -gt 0 ]; then
        success_rate=$((100 * (total_checks - failed_checks) / total_checks))
        print_info "Success rate: ${success_rate}%"
    fi
    
    # Show system metrics
    local metrics
    if metrics=$(get_system_metrics); then
        if command -v python3 &> /dev/null && [ "$metrics" != '{"error": "*"}' ]; then
            echo "$metrics" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' not in data:
        print(f'System: CPU {data[\"cpu_percent\"]}%, RAM {data[\"memory_percent\"]}%, Disk {data[\"disk_percent\"]}%')
except:
    pass
"
        fi
    fi
}

monitor_continuous() {
    print_info "Starting continuous monitoring (interval: ${CHECK_INTERVAL}s)"
    print_info "Press Ctrl+C to stop monitoring"
    
    # Set up signal handler for graceful shutdown
    trap 'print_info "Monitoring stopped"; show_summary; exit 0' INT TERM
    
    while true; do
        # Check if bot process exists
        if ! check_docker_containers && ! check_local_process; then
            send_alert "No bot processes found running"
        fi
        
        # Check health endpoint
        if ! check_health; then
            if [ $failed_checks -ge $ALERT_THRESHOLD ]; then
                send_alert "Bot health check failed $failed_checks times"
            fi
        fi
        
        # Show periodic summary
        if [ $((total_checks % 20)) -eq 0 ]; then
            show_summary
        fi
        
        sleep $CHECK_INTERVAL
    done
}

monitor_once() {
    print_info "Running single health check..."
    
    check_docker_containers
    check_local_process
    check_health
    
    show_summary
}

show_help() {
    echo "Professional Discord Trading Bot - Monitoring Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  monitor        Start continuous monitoring (default)"
    echo "  check          Run single health check"
    echo "  summary        Show monitoring summary"
    echo "  help           Show this help message"
    echo ""
    echo "Options:"
    echo "  --interval N   Set check interval in seconds (default: 30)"
    echo "  --threshold N  Set alert threshold (default: 3)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start continuous monitoring"
    echo "  $0 check              # Single health check"
    echo "  $0 monitor --interval 60"
    echo "  $0 summary"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        --threshold)
            ALERT_THRESHOLD="$2"
            shift 2
            ;;
        monitor)
            COMMAND="monitor"
            shift
            ;;
        check)
            COMMAND="check"
            shift
            ;;
        summary)
            COMMAND="summary"
            shift
            ;;
        help|--help|-h)
            COMMAND="help"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Default command is monitor
COMMAND="${COMMAND:-monitor}"

# Main execution
case "$COMMAND" in
    "monitor")
        monitor_continuous
        ;;
    "check")
        monitor_once
        ;;
    "summary")
        show_summary
        ;;
    "help")
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac 