"""
Discord Bot Command Handler
This module ensures all commands use the correct prefix
"""

import discord
from discord.ext import commands
import logging
from typing import Optional, Union
from src.config.config_loader import get_config

logger = logging.getLogger(__name__)

class CommandHandler:
    """
    Command handler to ensure all commands use the correct prefix
    """
    
    def __init__(self, bot):
        """Initialize the command handler with the bot instance"""
        self.bot = bot
        self.config = get_config()
        self.command_prefix = self.config.discord.command_prefix
        
        # Register event handlers
        self.bot.add_listener(self.on_message, 'on_message')
        self.bot.add_listener(self.on_command_error, 'on_command_error')
        
        logger.info(f"Command handler initialized with prefix: {self.command_prefix}")
        
    async def on_message(self, message: discord.Message):
        """
        Intercept messages and handle command prefix issues
        
        If a message starts with the wrong prefix (//) but contains a valid command,
        inform the user about the correct prefix
        """
        if message.author.bot:
            return
            
        # Skip messages that are already using the correct prefix
        if message.content.startswith(self.command_prefix):
            return
            
        # Check for the wrong prefix
        wrong_prefix = "//"
        if message.content.startswith(wrong_prefix):
            # Extract the command name
            potential_cmd = message.content[len(wrong_prefix):].split(" ")[0]
            
            # Check if this is a valid command
            command = self.bot.get_command(potential_cmd)
            if command:
                # It's a valid command but with the wrong prefix
                correct_cmd = message.content.replace(wrong_prefix, self.command_prefix, 1)
                
                embed = discord.Embed(
                    title="⚠️ Command Prefix Changed",
                    description=f"Please use `{self.command_prefix}` instead of `{wrong_prefix}`",
                    color=0xFFAA00
                )
                embed.add_field(name="Try this instead:", value=f"`{correct_cmd}`")
                await message.channel.send(embed=embed, delete_after=15)
                logger.info(f"Informed user {message.author} about correct command prefix")
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Handle command errors related to prefix issues
        """
        # Only process CommandNotFound errors that might be related to prefix issues
        if isinstance(error, commands.CommandNotFound):
            cmd_name = ctx.message.content.split(" ")[0]
            
            # If using wrong prefix, the handler will take care of it
            if cmd_name.startswith("//"):
                return
                
            # Check if it might be a valid command with no prefix
            potential_cmds = []
            for cmd in self.bot.commands:
                if cmd_name == cmd.name or cmd_name in cmd.aliases:
                    potential_cmds.append(cmd.name)
            
            if potential_cmds:
                suggestions = ", ".join([f"`{self.command_prefix}{cmd}`" for cmd in potential_cmds])
                embed = discord.Embed(
                    title="❓ Command Not Found",
                    description=f"Did you forget the `{self.command_prefix}` prefix?",
                    color=0xFFAA00
                )
                embed.add_field(name="Try:", value=suggestions)
                await ctx.send(embed=embed, delete_after=15)
                logger.info(f"Suggested command prefix to user {ctx.author}")

def setup_command_handler(bot) -> CommandHandler:
    """Initialize and set up the command handler for the given bot"""
    return CommandHandler(bot) 