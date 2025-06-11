"""
Admin Commands Cog for Discord Trading Bot
Implements admin-related commands
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal
import logging
from datetime import datetime
import platform
import psutil
import sys
import os

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    """Admin commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Admin commands cog initialized")
    
    @commands.command(name="health")
    async def health(self, ctx):
        """Show bot health and status information"""
        try:
            # System info
            uptime = datetime.now() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
            uptime_str = str(uptime).split('.')[0] if uptime else "Unknown"
            
            # Create the embed
            embed = discord.Embed(
                title="🏥 Bot Health Status",
                description="Current health and performance metrics",
                color=0x00ff00 if self.bot.is_ready else 0xff0000,
                timestamp=datetime.now()
            )
            
            # Basic stats
            embed.add_field(
                name="🤖 Bot Status",
                value=f"{'✅ Online' if self.bot.is_ready else '❌ Issues Detected'}",
                inline=True
            )
            
            embed.add_field(
                name="⏱️ Uptime",
                value=uptime_str,
                inline=True
            )
            
            embed.add_field(
                name="🏠 Servers",
                value=f"{len(self.bot.guilds)}",
                inline=True
            )
            
            # System info
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            embed.add_field(
                name="💻 CPU Usage",
                value=f"{cpu_usage}%",
                inline=True
            )
            
            embed.add_field(
                name="🧠 Memory Usage",
                value=f"{memory_usage}%",
                inline=True
            )
            
            embed.add_field(
                name="🐍 Python Version",
                value=f"{platform.python_version()}",
                inline=True
            )
            
            # Command stats
            command_count = getattr(self.bot, 'command_count', 0)
            error_count = getattr(self.bot, 'error_count', 0)
            
            embed.add_field(
                name="📊 Commands Processed",
                value=f"{command_count}",
                inline=True
            )
            
            embed.add_field(
                name="⚠️ Errors",
                value=f"{error_count}",
                inline=True
            )
            
            embed.add_field(
                name="🔄 Error Rate",
                value=f"{(error_count / command_count * 100) if command_count > 0 else 0:.2f}%",
                inline=True
            )
            
            # Exchange info
            exchange_name = "Demo Mode"
            sandbox_mode = True
            
            embed.add_field(
                name="💱 Exchange",
                value=exchange_name,
                inline=True
            )
            
            embed.add_field(
                name="🏝️ Sandbox Mode",
                value=f"{'✅ Enabled' if sandbox_mode else '❌ Disabled'}",
                inline=True
            )
            
            embed.add_field(
                name="📡 Connection Status",
                value="✅ Connected (Demo)",
                inline=True
            )
            
            embed.set_footer(text=f"Bot ID: {self.bot.user.id} | Environment: Demo")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in health command: {e}")
            await ctx.send(f"❌ Error fetching health status: {str(e)}")
    
    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx, guild_id: Optional[int] = None):
        """Sync slash commands to Discord"""
        try:
            await ctx.send("⏳ Syncing slash commands to Discord...")
            
            if guild_id:
                guild = discord.Object(id=guild_id)
                self.bot.tree.copy_global_to(guild=guild)
                await self.bot.tree.sync(guild=guild)
                await ctx.send(f"✅ Slash commands synced to guild ID: {guild_id}")
            else:
                await self.bot.tree.sync()
                await ctx.send("✅ Global slash commands synced to Discord")
            
        except Exception as e:
            logger.error(f"Error in sync command: {e}")
            await ctx.send(f"❌ Error syncing slash commands: {str(e)}")
    
    @commands.command(name="stats")
    async def stats(self, ctx):
        """Show bot statistics"""
        try:
            # Bot stats
            uptime = datetime.now() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
            uptime_str = str(uptime).split('.')[0] if uptime else "Unknown"
            command_count = getattr(self.bot, 'command_count', 0)
            
            # Get active commands
            active_commands, inactive_commands = [], []
            if hasattr(self.bot, 'get_command_status'):
                active_commands, inactive_commands = self.bot.get_command_status()
            
            embed = discord.Embed(
                title="📊 Bot Statistics",
                description=f"Trading Bot Statistics and Information",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="⏱️ Uptime",
                value=uptime_str,
                inline=True
            )
            
            embed.add_field(
                name="🏠 Servers",
                value=f"{len(self.bot.guilds)}",
                inline=True
            )
            
            embed.add_field(
                name="📊 Commands Used",
                value=f"{command_count}",
                inline=True
            )
            
            embed.add_field(
                name="🟢 Active Commands",
                value=f"{len(active_commands)}",
                inline=True
            )
            
            embed.add_field(
                name="🔴 Inactive Commands",
                value=f"{len(inactive_commands)}",
                inline=True
            )
            
            embed.add_field(
                name="📈 Total Commands",
                value=f"{len(self.bot.commands)}",
                inline=True
            )
            
            embed.set_footer(text="Trading Bot | Demo Mode")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            await ctx.send(f"❌ Error fetching bot statistics: {str(e)}")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
    logger.info("Admin commands cog loaded") 