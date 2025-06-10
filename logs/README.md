# 📋 Logs Directory

Thư mục này chứa tất cả file log của Discord Trading Bot.

## 📁 Log Files Structure

```
logs/
├── discord.log          # Bot activity và Discord events
├── trading.log          # Trading operations và signals
├── error.log           # Error logs và exceptions
└── system.log          # System health và performance
```

## 📊 Log Levels

- **DEBUG** - Chi tiết debug (development)
- **INFO** - Thông tin chính (production)
- **WARNING** - Cảnh báo quan trọng
- **ERROR** - Lỗi cần xử lý
- **CRITICAL** - Lỗi nghiêm trọng

## 🔧 Log Configuration

### Environment Variables
```bash
LOG_LEVEL=INFO              # Set log level
LOG_FILE_SIZE=10MB          # Max file size
LOG_BACKUP_COUNT=5          # Number of backup files
LOG_FORMAT=json             # Log format (json/text)
```

### Log Rotation
- Auto-rotation khi file > 10MB
- Giữ lại 5 file backup
- Compress old files
- Daily rotation option

## 📈 Monitoring Logs

### Real-time Monitoring
```bash
# Theo dõi tất cả logs
tail -f logs/*.log

# Theo dõi log cụ thể
tail -f logs/trading.log

# Theo dõi errors
tail -f logs/error.log | grep ERROR
```

### Log Analysis
```bash
# Tìm errors trong 24h qua
find logs/ -name "*.log" -mtime -1 -exec grep -l "ERROR" {} \;

# Đếm số lượng signals
grep "Signal generated" logs/trading.log | wc -l

# Kiểm tra bot uptime
grep "Bot started" logs/discord.log
```

## 🚨 Log Monitoring

### Important Log Patterns
- **Bot startup**: `Bot started successfully`
- **Signal generation**: `Signal generated for`
- **API errors**: `Exchange API error`
- **Connection issues**: `Connection lost`
- **Memory warnings**: `High memory usage`

### Alert Conditions
- ERROR level logs
- API connection failures
- Memory/disk warnings
- Excessive duplicate signals

## 🧹 Log Maintenance

### Cleanup Commands
```bash
# Xóa logs cũ hơn 30 ngày
find logs/ -name "*.log" -mtime +30 -delete

# Compress logs cũ
gzip logs/*.log.1 logs/*.log.2

# Archive logs theo tháng
tar -czf logs/archive/$(date +%Y-%m)-logs.tar.gz logs/*.log.*
```

### Docker Log Management
```bash
# View container logs
docker logs trading_bot_container

# Follow container logs
docker logs -f trading_bot_container

# Log with timestamps
docker logs -t trading_bot_container
```

## 📊 Log Formats

### JSON Format (Production)
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "module": "trading",
  "message": "Signal generated for BTCUSDT",
  "data": {
    "symbol": "BTCUSDT",
    "price": 45000.00,
    "signal_type": "BUY"
  }
}
```

### Text Format (Development)
```
2024-01-01 12:00:00 [INFO] trading: Signal generated for BTCUSDT price=45000.00
``` 