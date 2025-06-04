# Health Server Port Conflict Resolution

## Overview

The Discord Trading Bot includes a comprehensive health monitoring server that automatically handles port conflicts and provides real-time status monitoring. This guide covers common health server issues and their solutions.

## Port Conflict Resolution

### Problem: Health Server Port Binding Errors

**Error Message:**
```
OSError: [Errno 48] Address already in use
Failed to start health server: [Errno 48] error while attempting to bind on address ('0.0.0.0', 8080): address already in use
```

### Automatic Solution (Built-in)

The bot now includes **intelligent port selection** that automatically resolves port conflicts:

1. **Primary Port**: Attempts to bind to port 8080
2. **Fallback Ports**: Automatically tries ports 8081, 8082, 8083, 8084
3. **Graceful Degradation**: Continues operation even if no ports are available

**Log Output (Success):**
```
2025-06-04 19:29:30,316 - bot - WARNING - Port 8080 is already in use, trying next port...
2025-06-04 19:29:30,317 - bot - INFO - Health server started on port 8081
```

### Manual Port Management

If you need to manually manage ports:

#### 1. Check Current Port Usage
```bash
# Check what's using port 8080
lsof -i :8080

# Check multiple ports
lsof -i :8080-8084
```

#### 2. Kill Conflicting Processes
```bash
# Find the process using port 8080
ps aux | grep python

# Kill specific process by PID
kill <PID>

# Or kill all Python processes (use with caution)
pkill -f "python.*main.py"
```

#### 3. Custom Port Configuration
You can modify the port range in `main.py`:

```python
# In start_health_server() function
ports_to_try = [8080, 8081, 8082, 8083, 8084]
# Change to your preferred ports:
ports_to_try = [9000, 9001, 9002, 9003, 9004]
```

## Health Monitoring

### Health Endpoints

The health server provides several monitoring endpoints:

1. **Health Check**: `http://localhost:<port>/health`
   - Returns bot status, uptime, and component health
   - HTTP 200 for healthy, HTTP 503 for unhealthy

2. **Metrics**: `http://localhost:<port>/metrics`
   - Provides detailed metrics in JSON format
   - Supports Prometheus format with `Accept: text/plain` header

3. **Kubernetes Style**: `http://localhost:<port>/healthz`
   - Kubernetes-compatible health check endpoint

### Health Status Monitoring

#### Check Bot Health via API
```bash
# Check health (replace 8081 with actual port)
curl http://localhost:8081/health

# Get metrics
curl http://localhost:8081/metrics

# Prometheus format
curl -H "Accept: text/plain" http://localhost:8081/metrics
```

#### Expected Health Response
```json
{
  "status": "healthy",
  "uptime_seconds": 305,
  "bot_ready": true,
  "trading_bot_initialized": true,
  "last_heartbeat": "2025-06-04T19:34:30.332000",
  "environment": "development"
}
```

## Common Issues and Solutions

### Issue 1: Health Server Not Starting

**Symptoms:**
- No health server logs
- Health endpoints unreachable
- No port conflict warnings

**Solutions:**
1. Check if aiohttp is installed: `pip install aiohttp>=3.8.0`
2. Verify the health server task is starting in logs
3. Check for firewall blocking ports 8080-8084

### Issue 2: Multiple Bot Instances

**Symptoms:**
- Port conflicts on startup
- Multiple health servers running
- Duplicate Discord bot responses

**Solutions:**
1. Check for existing bot processes: `ps aux | grep "python.*main.py"`
2. Kill duplicate processes: `pkill -f "python.*main.py"`
3. Use process managers like systemd for single-instance deployment

### Issue 3: Health Check File Issues

**Symptoms:**
- Docker health checks failing
- Process monitoring not working

**Solutions:**
1. Check `/tmp/bot_healthy` file permissions
2. Verify Docker health check configuration
3. Monitor logs for health file update errors

## Production Deployment

### Recommended Health Monitoring

1. **External Monitoring**: Use external services to monitor health endpoints
2. **Process Management**: Use systemd, supervisord, or Docker for process management
3. **Alerting**: Set up alerts for health check failures
4. **Load Balancing**: Use multiple ports for high-availability deployments

### Systemd Service Example

```ini
[Unit]
Description=Discord Trading Bot
After=network.target

[Service]
Type=simple
User=tradingbot
WorkingDirectory=/opt/trading_bot
ExecStart=/opt/trading_bot/venv/bin/python main.py
Restart=always
RestartSec=10
Environment=ENVIRONMENT=production

[Install]
WantedBy=multi-user.target
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/health || curl -f http://localhost:8081/health || exit 1
```

## Monitoring Best Practices

1. **Multiple Health Endpoints**: Always check multiple possible ports
2. **Graceful Degradation**: Design monitoring to handle port changes
3. **Comprehensive Logging**: Monitor logs for port conflict warnings
4. **Automated Recovery**: Use process managers for automatic restart
5. **External Monitoring**: Don't rely solely on internal health checks

## Advanced Configuration

### Custom Health Server Configuration

You can extend the health server functionality by modifying the `start_health_server()` function in `main.py`:

```python
# Add custom health checks
async def custom_health_check():
    # Your custom health logic
    return {"custom_metric": "value"}

# Add custom endpoints
app.router.add_get('/custom', custom_endpoint)
```

### Environment-Specific Port Configuration

```env
# Development
HEALTH_SERVER_PORTS=8080,8081,8082

# Production  
HEALTH_SERVER_PORTS=9090,9091,9092

# Docker
HEALTH_SERVER_PORTS=8080
```

This comprehensive health monitoring system ensures reliable bot operation across all deployment environments. 