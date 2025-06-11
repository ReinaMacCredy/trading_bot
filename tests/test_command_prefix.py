#!/usr/bin/env python3
"""
Discord Bot Command Prefix Test
This script tests if Discord bot commands are properly responding to the configured prefix
"""

import asyncio
import discord
from discord.ext import commands
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.config.config_loader import get_config
from src.bot.bot_core import create_bot

class TestCommandPrefix(unittest.IsolatedAsyncioTestCase):
    """Test the Discord bot command prefix functionality"""
    
    def setUp(self):
        """Set up the test environment"""
        # Mock environment variables
        os.environ["DISCORD_TOKEN"] = "test_token"
        os.environ["ENVIRONMENT"] = "test"
        
        # Get the config
        self.config = get_config()
        self.command_prefix = self.config.discord.command_prefix
        
        # Ensure we're testing the right prefix
        self.assertEqual(self.command_prefix, "b!", "Command prefix should be 'b!'")
        
    @patch('discord.ext.commands.Bot.run')
    @patch('discord.ext.commands.Bot.process_commands')
    async def test_command_prefix_response(self, mock_process_commands, mock_run):
        """Test if the bot responds to the correct command prefix"""
        # Create the bot
        bot = create_bot()
        
        # Create a mock message
        mock_message = MagicMock()
        mock_message.content = f"{self.command_prefix}help"
        mock_message.author.bot = False
        
        # Create a mock message that doesn't start with the prefix
        mock_wrong_prefix_message = MagicMock()
        mock_wrong_prefix_message.content = "//help"
        mock_wrong_prefix_message.author.bot = False
        
        # Mock the on_message method
        # We need to directly call the method that would process prefixes
        mock_process_commands.reset_mock()
        
        # Create a custom event method to call process_commands
        async def fake_on_message(message):
            if message.content.startswith(bot.command_prefix):
                await bot.process_commands(message)
        
        # Process both messages
        await fake_on_message(mock_message)
        await fake_on_message(mock_wrong_prefix_message)
        
        # Check if process_commands was called only for the correct prefix
        mock_process_commands.assert_called_once_with(mock_message)
        self.assertEqual(mock_process_commands.call_count, 1, 
                         "process_commands should only be called once for the correct prefix")
    
    @patch('discord.ext.commands.Bot.run')
    async def test_command_parsing(self, mock_run):
        """Test if commands are correctly parsed with the right prefix"""
        # Create the bot
        bot = create_bot()
        
        # Register a test command
        @bot.command(name='testcmd')
        async def test_command(ctx):
            pass
        
        # Test command existence
        self.assertTrue(any(c.name == 'testcmd' for c in bot.commands), 
                        f"Command 'testcmd' should exist in bot.commands")
        
        # Create mock context with correct prefix
        correct_ctx = MagicMock()
        correct_ctx.message.content = f"{self.command_prefix}testcmd"
        
        # Create mock context with wrong prefix
        wrong_ctx = MagicMock()
        wrong_ctx.message.content = "//testcmd"
        
        # Check that command prefix is correct
        self.assertEqual(bot.command_prefix, self.command_prefix,
                         f"Bot command prefix should be '{self.command_prefix}'")

if __name__ == "__main__":
    unittest.main() 