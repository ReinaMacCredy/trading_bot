import discord
from discord.ext import commands
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("discord.log", encoding='utf-8', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

def create_signal_embed(pair, strategy, entry_price, tp_price, sl_price, ratio="0.0%", status="takeprofit", imminent=1, author="Reina"):
    """Create a Discord embed for a trading signal"""
    # Split the pair into its components
    pair_components = pair.split("-")
    coin = pair_components[0].strip()
    strategy_code = pair_components[1].strip() if len(pair_components) > 1 else ""
    
    # Format the ratio if it doesn't end with %
    if not ratio.endswith("%"):
        ratio = f"{ratio}%"
    
    # Create the embed
    embed = discord.Embed(
        title=f"{coin} - {strategy_code}",
        description="",
        color=0x7CFC00  # Green color
    )
    
    # Format the embed content like the example
    entry_text = f"Entry: {entry_price}"
    tp_text = f"TP (2R): {tp_price}"
    sl_text = f"SL: {sl_price}"
    
    embed.description = f"{entry_text} - {tp_text} - {sl_text}\n"
    embed.description += f"Imminent (Sắp vào Entry): {imminent}\n"
    embed.description += f"Ratio (Tỉ lệ): {ratio}\n"
    embed.description += f"Status (Trạng thái): {status}"
    
    # Always use "Reina" as the author for consistency, ignoring any passed value
    embed.set_footer(text=f"By Reina~")
    
    return embed

def run_bot():
    """This function is deprecated. Use main.py instead."""
    logger.warning("bot.py's run_bot() is deprecated. Please use main.py to run the bot.")
    logger.warning("This will not start a bot instance to avoid duplicate signals.") 