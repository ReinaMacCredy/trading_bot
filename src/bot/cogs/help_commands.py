"""
Help Commands Cog for Discord Trading Bot
Implements help-related commands
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class HelpCommands(commands.Cog):
    """Help commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Help commands cog initialized")
    
    @commands.command(name="h_help")
    async def help_command(self, ctx, command: Optional[str] = None):
        """Show help information for commands"""
        try:
            prefix = "b!"  # According to memory, we use b! prefix
            
            if command:
                await self._show_command_help(ctx, command, prefix)
            else:
                await self._show_general_help(ctx, prefix)
                
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await ctx.send(f"❌ Error showing help: {str(e)}")
    
    async def _show_general_help(self, ctx, prefix):
        """Show general help information"""
        embed = discord.Embed(
            title="📚 Trading Bot Help",
            description=f"Use `{prefix}help <command>` for more information on a specific command.",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        # Group commands by category
        categories = {
            "🤖 Bot Commands": ["help", "stats", "health", "sync"],
            "💰 Trading Commands": ["buy", "sell", "balance", "portfolio", "position_size"],
            "📊 Strategy Commands": ["strategies", "analyze"],
            "📈 Analysis Commands": ["indicator", "help_indicators"],
            "💼 Portfolio Commands": ["portfolio", "position_size"]
        }
        
        for category, cmds in categories.items():
            value = ", ".join(f"`{prefix}{cmd}`" for cmd in cmds)
            embed.add_field(name=category, value=value, inline=False)
        
        embed.add_field(
            name="🔗 Slash Commands",
            value="This bot also supports slash commands! Type `/` to see available options.",
            inline=False
        )
        
        embed.set_footer(text=f"Trading Bot | Prefix: {prefix}")
        
        await ctx.send(embed=embed)
    
    async def _show_command_help(self, ctx, command_name, prefix):
        """Show help for a specific command"""
        command = self.bot.get_command(command_name)
        
        if not command:
            await ctx.send(f"❌ Command `{command_name}` not found.")
            return
        
        embed = discord.Embed(
            title=f"📚 Command Help: {command_name}",
            description=command.help or "No description available.",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        # Command usage
        usage = f"{prefix}{command.name}"
        if command.signature:
            usage += f" {command.signature}"
        
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
        
        # Command aliases
        if command.aliases:
            aliases = ", ".join(f"`{prefix}{alias}`" for alias in command.aliases)
            embed.add_field(name="Aliases", value=aliases, inline=False)
        
        # Example
        examples = self._get_command_examples(command.name, prefix)
        if examples:
            embed.add_field(name="Examples", value=examples, inline=False)
        
        embed.set_footer(text=f"Trading Bot | Prefix: {prefix}")
        
        await ctx.send(embed=embed)
    
    def _get_command_examples(self, command_name, prefix):
        """Get examples for specific commands"""
        examples = {
            "buy": f"`{prefix}buy BTC 0.1`\n`{prefix}buy ETH 2`",
            "sell": f"`{prefix}sell BTC 0.05`\n`{prefix}sell ETH 1`",
            "balance": f"`{prefix}balance`",
            "analyze": f"`{prefix}analyze SC01 BTC 1h`\n`{prefix}analyze SC02 ETH 4h`",
            "indicator": f"`{prefix}indicator RSI BTC 1h`\n`{prefix}indicator MACD ETH 4h`",
            "position_size": f"`{prefix}position_size BTC 50000 48000`",
            "portfolio": f"`{prefix}portfolio`",
            "strategies": f"`{prefix}strategies`",
            "health": f"`{prefix}health`",
            "stats": f"`{prefix}stats`",
            "sync": f"`{prefix}sync`\n`{prefix}sync 123456789012345678`"
        }
        
        return examples.get(command_name)
    
    @commands.command(name="commands")
    async def list_commands(self, ctx):
        """List all available commands"""
        try:
            prefix = "b!"  # According to memory, we use b! prefix
            
            embed = discord.Embed(
                title="🤖 Available Commands",
                description=f"List of all available commands. Use `{prefix}help <command>` for more details.",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            # Get all commands
            commands_list = [cmd.name for cmd in self.bot.commands]
            commands_list.sort()
            
            # Format commands in chunks
            chunks = [commands_list[i:i + 10] for i in range(0, len(commands_list), 10)]
            
            for i, chunk in enumerate(chunks, 1):
                field_value = ", ".join(f"`{prefix}{cmd}`" for cmd in chunk)
                embed.add_field(name=f"Commands {i}", value=field_value, inline=False)
            
            embed.set_footer(text=f"Trading Bot | Total Commands: {len(commands_list)}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in list_commands command: {e}")
            await ctx.send(f"❌ Error listing commands: {str(e)}")

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
    logger.info("Help commands cog loaded") 