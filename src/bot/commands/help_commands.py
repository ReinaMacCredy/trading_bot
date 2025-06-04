import discord
from discord.ext import commands
from discord import Embed

async def help_command(ctx):
    """Display help information for the trading bot"""
    
    embed = Embed(title="Trading Bot", color=0x2F3136)
    embed.set_author(name="Trading Bot", icon_url="https://i.imgur.com/8dQlQAW.png")
    embed.set_footer(text="Page 1/1")
    
    # Meta section
    embed.add_field(name="Meta", value="------------------------", inline=False)
    embed.add_field(name="Meta commands related to the bot", value="------------------------", inline=False)
    
    # Getting Started section
    embed.add_field(name="Getting Started", value="", inline=False)
    
    getting_started_text = (
        "/faq: How to use the trading bot\n"
        "/tip: Get some tips about Trading Bot\n"
        "/help: Help command\n"
        "/setup: Setup command with some common setup options\n"
        "/invite: Get the invite links for me and my clones\n"
        "/support: Do you need any additional help or is the bot not functioning correctly?\n"
        "/categories: Show a list of all available categories\n"
    )
    embed.add_field(name="\u200b", value=getting_started_text, inline=False)
    
    # Information section
    embed.add_field(name="Information", value="", inline=False)
    
    info_text = (
        "/ping: Get my ping to Discord\n"
        "/about: Get some information about the bot\n"
        "/stats: Get some stats about the bot\n"
        "/shards: Get some stats about the shards\n"
        "/dashboard: Get a link to the dashboard\n"
        "/changelogs: Get a list of all changelogs, ordered by most recent\n"
    )
    embed.add_field(name="\u200b", value=info_text, inline=False)
    
    # Other section
    # Slash Commands section
    embed.add_field(name="Slash Commands", value="", inline=False)
    
    slash_text = (
        "/price <symbol>: Get current cryptocurrency price\n"
        "/signal <symbol>: Generate a trading signal\n"
        "/stats: View bot statistics and status\n"
        "/help: Show slash command help\n"
    )
    embed.add_field(name="\u200b", value=slash_text, inline=False)
    
    embed.add_field(name="Other", value="", inline=False)
    
    other_text = (
        "/sync: Sync slash commands (Admin only)\n"
        "/vote: Vote for the bot on bot lists to support it!\n"
        "/clean: Deletes all command related messages\n"
        "/premium: Do you wish to support this project? Consider donating\n"
    )
    embed.add_field(name="\u200b", value=other_text, inline=False)
    
    embed.set_footer(text="Page 1/1 | Use / for slash commands!")
    
    await ctx.send(embed=embed) 