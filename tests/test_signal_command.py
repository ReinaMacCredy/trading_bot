#!/usr/bin/env python3
"""
Simple test for the b!signal command (tradesignal)
This script tests the functionality of the tradesignal command directly
"""

import discord
from discord.ext import commands
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
import logging
import asyncio

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.bot.cogs.trading_commands import TradingCommands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_signal')

async def test_tradesignal_command():
    """Test the tradesignal command functionality directly"""
    
    # Create a mock bot
    bot = MagicMock(spec=commands.Bot)
    bot.latency = 0.05  # 50ms latency for testing
    
    # Create the trading commands cog
    cog = TradingCommands(bot)
    
    # Create a mock context for commands
    ctx = MagicMock(spec=commands.Context)
    ctx.send = AsyncMock()
    
    # Test with BTC symbol
    symbol = "BTC"
    
    logger.info(f"Testing tradesignal command with symbol: {symbol}")
    
    # Call the function directly - not through the command system
    # The implementation of tradesignal is a method
    await cog.tradesignal.callback(cog, ctx, symbol)
    
    # Verify the command response
    assert ctx.send.called, "The send method was not called"
    
    # Check the content of the response
    call_args = ctx.send.call_args
    embed = call_args[1].get('embed')
    
    assert embed is not None, "No embed was sent in the response"
    assert f"Trading Signal: {symbol.upper()}USDT" in embed.title, "Title does not contain the symbol"
    assert "Signal" in [field.name for field in embed.fields], "Signal field is missing"
    
    logger.info("✅ tradesignal command test passed")
    return True

async def test_signal_command_alias():
    """Test the signalcmd command (b!signal alias)"""
    
    # Create a mock bot
    bot = MagicMock(spec=commands.Bot)
    
    # Create the trading commands cog
    cog = TradingCommands(bot)
    
    # Create a mock context for commands
    ctx = MagicMock(spec=commands.Context)
    ctx.send = AsyncMock()
    
    # Test with ETH symbol
    symbol = "ETH"
    
    logger.info(f"Testing signalcmd command with symbol: {symbol}")
    
    # Mock the tradesignal method to verify it's called
    original_tradesignal = cog.tradesignal
    cog.tradesignal = AsyncMock()
    
    # Call the function directly
    await cog.signal.callback(cog, ctx, symbol)
    
    # Verify tradesignal was called with correct arguments
    cog.tradesignal.assert_called_once_with(ctx, symbol)
    
    # Restore original method
    cog.tradesignal = original_tradesignal
    
    logger.info("✅ signalcmd command test passed")
    return True

async def test_unusual_symbol():
    """Test the tradesignal command with unusual symbols"""
    
    # Create a mock bot
    bot = MagicMock(spec=commands.Bot)
    
    # Create the trading commands cog
    cog = TradingCommands(bot)
    
    # Create a mock context for commands
    ctx = MagicMock(spec=commands.Context)
    ctx.send = AsyncMock()
    
    # Test with an unusual symbol
    unusual_symbol = "12BTC"
    
    logger.info(f"Testing tradesignal command with unusual symbol: {unusual_symbol}")
    
    # Call the function directly
    await cog.tradesignal.callback(cog, ctx, unusual_symbol)
    
    # Verify the command response
    assert ctx.send.called, "The send method was not called"
    
    # Check the content of the response
    call_args = ctx.send.call_args
    embed = call_args[1].get('embed')
    
    assert embed is not None, "No embed was sent in the response"
    assert unusual_symbol.upper() in embed.title, "Title does not contain the symbol"
    
    # Reset the mock
    ctx.send.reset_mock()
    
    # Test with a symbol that already includes USDT
    symbol_with_usdt = "BTCUSDT"
    
    logger.info(f"Testing tradesignal command with symbol that includes USDT: {symbol_with_usdt}")
    
    # Call the function directly
    await cog.tradesignal.callback(cog, ctx, symbol_with_usdt)
    
    # Verify the command response
    assert ctx.send.called, "The send method was not called"
    
    # Check the content of the response
    call_args = ctx.send.call_args
    embed = call_args[1].get('embed')
    
    assert embed is not None, "No embed was sent in the response"
    assert symbol_with_usdt in embed.title, "Title does not contain the symbol"
    
    logger.info("✅ unusual symbol tests passed")
    return True

async def main():
    """Main test function"""
    logger.info("Starting signal command tests...")
    
    try:
        # Test the main tradesignal command
        result1 = await test_tradesignal_command()
        
        # Test the signal command alias
        result2 = await test_signal_command_alias()
        
        # Test handling of unusual symbols
        result3 = await test_unusual_symbol()
        
        if result1 and result2 and result3:
            logger.info("✅ All tests completed successfully!")
        else:
            logger.error("❌ Some tests failed!")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Set up test environment
    os.environ["DISCORD_TOKEN"] = "test_token"
    os.environ["ENVIRONMENT"] = "test"
    
    # Run the tests
    asyncio.run(main()) 