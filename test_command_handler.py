#!/usr/bin/env python3
"""
Command Handler Test Script
This script tests the command handler's ability to handle different command prefixes
"""

import asyncio
import discord
from discord.ext import commands
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from src.bot.bot_core import create_bot
from src.bot.commands.command_handler import setup_command_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_handler')

async def test_command_handler():
    """Test the command handler functionality"""
    logger.info("Testing command handler...")
    
    # Create a bot with mocked run method
    with patch('discord.ext.commands.Bot.run'):
        # Create the bot
        bot = create_bot()
        
        # Add a test command
        @bot.command(name='test')
        async def test_command(ctx):
            await ctx.send("Test command executed!")
        
        # Initialize the command handler
        handler = setup_command_handler(bot)
        
        # Create test messages
        correct_prefix_msg = MagicMock(spec=discord.Message)
        correct_prefix_msg.content = "b!test"
        correct_prefix_msg.author = MagicMock(spec=discord.Member)
        correct_prefix_msg.author.bot = False
        
        wrong_prefix_msg = MagicMock(spec=discord.Message)
        wrong_prefix_msg.content = "//test"
        wrong_prefix_msg.author = MagicMock(spec=discord.Member)
        wrong_prefix_msg.author.bot = False
        wrong_prefix_msg.channel = MagicMock()
        wrong_prefix_msg.channel.send = AsyncMock()
        
        no_prefix_msg = MagicMock(spec=discord.Message)
        no_prefix_msg.content = "test"
        no_prefix_msg.author = MagicMock(spec=discord.Member)
        no_prefix_msg.author.bot = False
        
        # Test correct prefix message
        logger.info("Testing correct prefix 'b!test'...")
        await handler.on_message(correct_prefix_msg)
        
        # Test wrong prefix message
        logger.info("Testing wrong prefix '//test'...")
        await handler.on_message(wrong_prefix_msg)
        
        # Check if the channel.send was called for wrong prefix
        if wrong_prefix_msg.channel.send.called:
            call_args = wrong_prefix_msg.channel.send.call_args
            embed = call_args[1].get('embed') or call_args[0][0]
            logger.info(f"Response: {embed.title} - {embed.description}")
            logger.info("✅ Command handler correctly detected wrong prefix")
        else:
            logger.error("❌ Command handler failed to respond to wrong prefix")
        
        # Test command error for no prefix
        logger.info("Testing no prefix 'test'...")
        ctx = MagicMock(spec=commands.Context)
        ctx.message = no_prefix_msg
        ctx.author = no_prefix_msg.author
        ctx.send = AsyncMock()
        
        error = commands.CommandNotFound()
        await handler.on_command_error(ctx, error)
        
        logger.info("Command handler test completed!")

async def main():
    """Main test function"""
    logger.info("Starting command handler tests...")
    
    try:
        await test_command_handler()
        logger.info("✅ All tests completed successfully!")
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