# Technical Context: Discord Trading Signal Bot

## Technologies Used

### Core Technologies
- **Python 3.8+**: Primary programming language
- **discord.py**: Discord API wrapper for bot functionality
- **python-binance**: Binance API client for cryptocurrency data
- **pandas**: Data analysis and manipulation
- **matplotlib**: Chart generation and visualization

### Dependencies
```
discord.py        # Discord bot API
python-dotenv     # Environment variable management
requests          # HTTP requests
python-binance    # Binance API client
pandas            # Data manipulation
matplotlib        # Chart generation
```

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Discord bot token (from Discord Developer Portal)
- Binance API key and secret (optional, for live data)

### Environment Configuration
- `.env` file with the following variables:
  ```
  DISCORD_TOKEN=your_discord_bot_token
  DISCORD_CHANNEL_ID=your_channel_id
  BINANCE_API_KEY=your_binance_api_key
  BINANCE_API_SECRET=your_binance_api_secret
  ```

## Technical Constraints

### Discord API Limitations
- Rate limits on API requests (50 requests per second)
- Message size limitations (2000 characters per message)
- Embed limitations (up to 25 fields, 6000 characters total)
- Command cooldowns needed to prevent accidental spam

### Binance API Limitations
- Rate limits vary by endpoint
- Requires API key for account-specific operations
- Weight-based rate limiting system

## Security Considerations

### API Key Management
- All API keys stored in environment variables
- Keys never hardcoded in source code
- Binance API keys with minimum required permissions

### Error Handling
- Graceful handling of API errors
- Logging of all errors and exceptions
- User-friendly error messages
- Specific handling for cooldown violations

### Data Integrity
- Duplicate signal detection
- Consistent author attribution
- Status message management for clear user feedback

## External Integrations

### Discord
- Utilizes Discord's command system
- Uses rich embeds for formatted messages
- Reacts to user interactions
- Implements command cooldowns for rate limiting

### Binance
- Fetches real-time cryptocurrency data
- Retrieves account information (optional)
- Accesses historical price data

## Deployment Considerations

### Bot Hosting
- Requires 24/7 runtime
- Can be deployed on:
  - VPS (DigitalOcean, AWS, etc.)
  - Heroku (with worker dyno)
  - Replit (with uptime monitoring)
- Memory requirements: ~100MB
- CPU: Minimal usage except during chart generation

### Maintenance
- Regular updates for discord.py and python-binance
- Monitor for Discord API changes
- Check for Binance API endpoint modifications 
- Review error logs for command usage patterns 