# Discord Slash Commands

The Discord Trading Bot now supports modern slash commands alongside traditional prefix commands. Slash commands provide a more intuitive and user-friendly experience with auto-completion and parameter validation.

## Available Slash Commands

### `/price <symbol> [exchange]`
Get real-time cryptocurrency prices with market data.

**Parameters:**
- `symbol` (required): Cryptocurrency symbol (e.g., BTC, ETH, ADA)
- `exchange` (optional): Exchange to query (binance, coinbase, kraken, bybit) - default: binance

**Example:**
```
/price symbol:BTC exchange:binance
```

**Features:**
- Real-time price data
- 24-hour change percentage
- 24-hour high/low prices
- Exchange information
- Professional embed formatting

### `/signal <symbol> [strategy] [timeframe]`
Generate professional trading signals with customizable parameters.

**Parameters:**
- `symbol` (required): Cryptocurrency symbol (e.g., BTC, ETH)
- `strategy` (optional): Trading strategy (SC01, SC02, SC02+FRVP) - default: SC01
- `timeframe` (optional): Analysis timeframe (1h, 4h, 1d) - default: 1h

**Example:**
```
/signal symbol:ETH strategy:SC02 timeframe:4h
```

**Features:**
- Professional signal formatting
- Entry, take profit, and stop loss prices
- Risk/reward ratio calculation
- Strategy and timeframe selection
- Real-time market data integration

### `/stats`
Display comprehensive bot statistics and system status.

**Example:**
```
/stats
```

**Features:**
- Bot uptime information
- Server and user counts
- Commands executed counter
- Error statistics
- Exchange connection status
- Last heartbeat timestamp

### `/help`
Modern help system showing available commands and features.

**Example:**
```
/help
```

**Features:**
- Complete command reference
- Slash and prefix command listings
- Feature descriptions
- Supported exchanges list
- Usage examples

## Setting Up Slash Commands

### Automatic Synchronization
Slash commands are automatically synchronized when the bot starts up. This process registers all commands with Discord.

### Manual Synchronization
Administrators can manually sync commands using the prefix command:

```
b!sync [guild_id]
```

**Parameters:**
- `guild_id` (optional): Sync to specific server (faster) or globally (slower)

**Examples:**
```
b!sync                    # Global sync (takes up to 1 hour)
b!sync 123456789012345678 # Guild-specific sync (immediate)
```

## Command Features

### Modern Discord Integration
- **Auto-completion**: Parameters show suggestions as you type
- **Validation**: Discord validates parameters before sending
- **Descriptions**: Each command and parameter has helpful descriptions
- **Error Handling**: User-friendly error messages
- **Deferred Responses**: Proper handling of processing time

### Professional Formatting
- **Rich Embeds**: Beautiful formatting with colors and icons
- **Timestamps**: All responses include generation time
- **Consistent Style**: Matches existing bot design language
- **Status Indicators**: Visual feedback for different states

### Integration with Existing Systems
- **Exchange Client**: Full integration with trading systems
- **Risk Management**: Same risk calculations as prefix commands
- **Error Handling**: Consistent error handling across command types
- **Logging**: Full logging integration for debugging

## Command Comparison

| Feature | Prefix Commands | Slash Commands |
|---------|----------------|----------------|
| Ease of Use | Manual typing | Auto-completion |
| Parameter Validation | Runtime | Pre-validation |
| Discovery | Help command | Discord interface |
| Mobile Experience | Standard | Enhanced |
| Error Prevention | Runtime errors | Type validation |

## Best Practices

### For Users
1. **Use slash commands** for better experience and fewer typos
2. **Try auto-completion** by typing `/` and selecting commands
3. **Check parameter descriptions** if unsure about inputs
4. **Use prefix commands** for complex or advanced operations

### For Administrators
1. **Sync commands after updates** using `b!sync`
2. **Use guild-specific sync** for testing (faster)
3. **Monitor logs** for synchronization issues
4. **Global sync** for production deployment

## Troubleshooting

### Commands Not Appearing
1. Check bot permissions in server settings
2. Ensure bot has "Use Slash Commands" permission
3. Try manual sync: `b!sync [guild_id]`
4. Wait up to 1 hour for global sync

### Permission Issues
- Bot needs "Use Slash Commands" permission
- Commands may be restricted by server settings
- Check Discord server integration settings

### Sync Failures
- Verify bot token is valid
- Check network connectivity
- Review bot logs for error details
- Try guild-specific sync first

## Technical Details

### Implementation
- Built using `discord.app_commands`
- Automatic type validation
- Deferred response pattern for long operations
- Error handling with ephemeral messages

### Performance
- Commands sync automatically on startup
- Guild-specific sync: immediate
- Global sync: up to 1 hour
- Response time: sub-second for most operations 