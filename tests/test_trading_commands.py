#!/usr/bin/env python3
"""
Trading Commands Test Script
This script tests the trading signal command functionality
"""

import discord
from discord.ext import commands
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import logging
import pytest
import pytest_asyncio

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
logger = logging.getLogger('test_trading_commands')

class TestTradingCommands:
    """Test case for trading commands"""
    
    @pytest_asyncio.fixture
    async def cog_setup(self):
        """Set up test environment"""
        # Create a mock bot
        bot = MagicMock(spec=commands.Bot)
        bot.latency = 0.05  # 50ms latency for testing
        
        # Create the trading commands cog
        cog = TradingCommands(bot)
        
        # Create a mock context for commands
        ctx = MagicMock(spec=commands.Context)
        ctx.send = AsyncMock()
        
        return bot, cog, ctx
    
    @pytest.mark.asyncio
    async def test_tradesignal_command(self, cog_setup):
        """Test the tradesignal command with a valid symbol"""
        # Get setup objects
        _, cog, ctx = cog_setup
        
        # Test with a valid symbol
        symbol = "BTC"
        
        # The tradesignal is a method that is registered as a command
        # We need to call it directly as a method, not through the command system
        logger.info(f"Testing tradesignal command with symbol: {symbol}")
        await cog.tradesignal(ctx, symbol)
        
        # Verify the command response
        assert ctx.send.called, "The send method was not called"
        
        # Check the content of the response
        call_args = ctx.send.call_args
        embed = call_args[1].get('embed')
        
        assert embed is not None, "No embed was sent in the response"
        assert f"Trading Signal: {symbol.upper()}USDT" in embed.title, "Title does not contain the symbol"
        assert "Signal" in [field.name for field in embed.fields], "Signal field is missing"
        
        logger.info("✅ tradesignal command test passed")
    
    @pytest.mark.asyncio
    async def test_signalcmd_command(self, cog_setup):
        """Test the signalcmd command (which is the alias for b!signal)"""
        # Get setup objects
        _, cog, ctx = cog_setup
        
        # Test with a valid symbol
        symbol = "ETH"
        
        # We need to test the 'signalcmd' command
        # First verify it exists in the cog
        assert hasattr(cog, 'signal'), "Signal command not found in the cog"
        
        # Mock the tradesignal method to verify it's called by the signalcmd command
        cog.tradesignal = AsyncMock()
        
        # Execute the command
        logger.info(f"Testing signalcmd command with symbol: {symbol}")
        await cog.signal(ctx, symbol)
        
        # Verify the tradesignal method was called with the correct arguments
        cog.tradesignal.assert_called_once_with(ctx, symbol)
        
        logger.info("✅ signalcmd command test passed")
    
    @pytest.mark.asyncio
    async def test_tradesignal_with_unusual_input(self, cog_setup):
        """Test tradesignal command with unusual input"""
        # Get setup objects
        _, cog, ctx = cog_setup
        
        # Reset mock
        ctx.send.reset_mock()
        
        # Execute the command with a valid but unusual symbol name
        unusual_symbol = "12BTC"
        
        logger.info(f"Testing tradesignal command with unusual symbol: {unusual_symbol}")
        await cog.tradesignal(ctx, unusual_symbol)
        
        # Verify the command still works with unusual input
        assert ctx.send.called, "The send method was not called"
        
        # Check the content of the response
        call_args = ctx.send.call_args
        embed = call_args[1].get('embed')
        
        assert embed is not None, "No embed was sent in the response"
        assert unusual_symbol.upper() in embed.title, "Title does not contain the symbol"
        
        logger.info("✅ tradesignal with unusual input test passed")

if __name__ == "__main__":
    # Set up test environment
    os.environ["DISCORD_TOKEN"] = "test_token"
    os.environ["ENVIRONMENT"] = "test"
    
    # Run the tests
    pytest.main(["-xvs", __file__]) 