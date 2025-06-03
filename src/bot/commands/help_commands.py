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
        "b!faq: How to use the trading bot\n"
        "b!tip: Get some tips about Trading Bot\n"
        "b!help: Help command\n"
        "b!setup: Setup command with some common setup options\n"
        "b!invite: Get the invite links for me and my clones\n"
        "b!support: Do you need any additional help or is the bot not functioning correctly?\n"
        "b!categories: Show a list of all available categories\n"
    )
    embed.add_field(name="\u200b", value=getting_started_text, inline=False)
    
    # Information section
    embed.add_field(name="Information", value="", inline=False)
    
    info_text = (
        "b!ping: Get my ping to Discord\n"
        "b!about: Get some information about the bot\n"
        "b!stats: Get some stats about the bot\n"
        "b!shards: Get some stats about the shards\n"
        "b!dashboard: Get a link to the dashboard\n"
        "b!changelogs: Get a list of all changelogs, ordered by most recent\n"
    )
    embed.add_field(name="\u200b", value=info_text, inline=False)
    
    # Other section
    embed.add_field(name="Other", value="", inline=False)
    
    other_text = (
        "b!vote: Vote for the bot on bot lists to support it!\n"
        "b!clean: Deletes all command related messages\n"
        "b!premium: Do you wish to support this project? Consider donating\n"
    )
    embed.add_field(name="\u200b", value=other_text, inline=False)
    
    await ctx.send(embed=embed) 