import discord
from discord import Embed
from datetime import datetime

async def order_history(ctx):
    """Display recent order history"""
    bot = ctx.bot
    history = bot.exchange_client.get_order_history()
    embed = Embed(title="Order History", color=0x2F3136)
    if not history:
        embed.description = "No orders have been placed yet."
    else:
        for order in history[-10:]:
            embed.add_field(
                name=f"{order.order_type.capitalize()} {order.side.upper()} {order.symbol}",
                value=(f"ID: {order.order_id}\nAmount: {order.amount}\nPrice: {order.price}"\
                       f"\nTime: {order.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\nStatus: {order.status}"),
                inline=False,
            )
    await ctx.send(embed=embed)

async def active_commands(ctx):
    """Show commands that have been used"""
    bot = ctx.bot
    active, _ = bot.get_command_status()
    embed = Embed(title="Active Commands", color=0x2F3136)
    embed.description = ", ".join(active) if active else "None"
    await ctx.send(embed=embed)

async def inactive_commands(ctx):
    """Show commands that exist but haven't been used"""
    bot = ctx.bot
    active, inactive = bot.get_command_status()
    embed = Embed(title="Inactive Commands", color=0x2F3136)
    embed.description = ", ".join(inactive) if inactive else "None"
    await ctx.send(embed=embed)

async def status_commands(ctx):
    """Show all commands grouped by active and inactive"""
    bot = ctx.bot
    active, inactive = bot.get_command_status()
    desc = "Active: " + (", ".join(active) if active else "None") + "\n\nInactive: " + (", ".join(inactive) if inactive else "None")
    embed = Embed(title="Command Status", description=desc, color=0x2F3136)
    await ctx.send(embed=embed)
