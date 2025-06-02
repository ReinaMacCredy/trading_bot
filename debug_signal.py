import logging
from trading import TradingBot
from bot import create_signal_embed
import discord
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('debug')

def debug_signal_generation():
    """Debug the signal generation process to find duplicate issues"""
    logger.info("Starting debug of signal generation process")
    
    # Create a trading bot instance
    trading_bot = TradingBot()
    
    # Test parameters
    symbols = ["ETH", "BTC", "SOL"]
    strategies = ["SC01", "SC02", "SC02+FRVP"]
    author = "Reina"
    
    # Test 1: Generate multiple signals for the same symbol/strategy
    logger.info("TEST 1: Multiple signals for the same symbol/strategy")
    symbol = "ETH"
    strategy_code = "SC02"
    
    for i in range(3):
        logger.info(f"Signal generation attempt {i+1} for {symbol}-{strategy_code}")
        signal = trading_bot.generate_trading_signal(symbol, strategy_code, 2.0, author)
        
        if not signal:
            logger.error(f"Failed to generate signal on attempt {i+1}")
            continue
        
        # Log the generated signal
        logger.info(f"Generated signal: Entry={signal['entry_price']}, TP={signal['tp_price']}, SL={signal['sl_price']}")
        
        # Store the signal and check if it's considered a duplicate
        storage_result = trading_bot.store_signal(signal)
        logger.info(f"Signal storage result: {storage_result}")
        
        # Create an embed from the signal
        embed = create_signal_embed(
            f"{signal['symbol']}-{signal['strategy_code']}", 
            "",
            signal['entry_price'], 
            signal['tp_price'], 
            signal['sl_price'], 
            signal['ratio'], 
            signal['status'], 
            signal['imminent']
        )
        
        # Log the embed details
        logger.info(f"Embed footer: {embed.footer.text}")
        
        # Wait a moment between attempts
        time.sleep(1)
    
    # Test 2: Generate signals with very close prices
    logger.info("\nTEST 2: Signals with very close price values")
    
    # Get a base signal
    base_signal = trading_bot.generate_trading_signal("BTC", "SC02", 2.0, author)
    
    if base_signal:
        # Store the original signal
        trading_bot.store_signal(base_signal)
        logger.info(f"Stored base signal: BTC-SC02 at {base_signal['entry_price']}")
        
        # Create a nearly identical signal with small price differences
        similar_signal = base_signal.copy()
        # Adjust price by tiny amount (0.05%)
        similar_signal['entry_price'] = round(float(base_signal['entry_price']) * 1.0005, 2)
        similar_signal['tp_price'] = round(float(base_signal['tp_price']) * 1.0005, 2)
        similar_signal['sl_price'] = round(float(base_signal['sl_price']) * 1.0005, 2)
        
        # Try to store the similar signal
        storage_result = trading_bot.store_signal(similar_signal)
        logger.info(f"Similar signal storage result: {storage_result}")
        logger.info(f"Original: {base_signal['entry_price']}, Similar: {similar_signal['entry_price']}")
    
    # Test 3: Signal clearing and memory management
    logger.info("\nTEST 3: Signal clearing test")
    
    # Print current signal count
    current_signals = trading_bot.get_signals()
    logger.info(f"Current signal count: {len(current_signals)}")
    
    # List all stored signals
    for i, signal in enumerate(current_signals):
        timestamp = signal.get('timestamp', 'unknown')
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime('%H:%M:%S')
            except:
                formatted_time = timestamp
        else:
            formatted_time = str(timestamp)
            
        logger.info(f"Signal {i+1}: {signal.get('symbol', '')}-{signal.get('strategy_code', '')}, Time: {formatted_time}")
    
    logger.info("Debug complete")

def test_signal_dedupe():
    """Specifically test the duplicate prevention logic"""
    logger.info("Testing duplicate detection mechanisms")
    
    # Create a trading bot instance
    trading_bot = TradingBot()
    
    # Generate 5 identical-looking signals (but with new objects each time)
    symbol = "ETH"
    strategy_code = "SC02"
    
    for i in range(5):
        # Generate fresh signal
        signal = trading_bot.generate_trading_signal(symbol, strategy_code, 2.0, "Reina")
        
        if not signal:
            continue
        
        logger.info(f"Signal {i+1} - Price: {signal['entry_price']}")
        
        # Try to store it and see if it's detected as duplicate
        result = trading_bot.store_signal(signal)
        logger.info(f"Storage result for signal {i+1}: {'✅ Stored' if result else '❌ Rejected as duplicate'}")
        
        # Wait briefly between attempts
        time.sleep(1)
    
    # Display final signal count
    signals = trading_bot.get_signals()
    logger.info(f"Total signals stored: {len(signals)}")
    
    # List each stored signal
    for i, s in enumerate(signals):
        logger.info(f"Stored signal {i+1}: {s.get('symbol')}-{s.get('strategy_code')} at {s.get('entry_price')}")

if __name__ == "__main__":
    debug_signal_generation()
    print("\n" + "="*50 + "\n")
    test_signal_dedupe() 