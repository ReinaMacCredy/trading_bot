"""
Command Resolver Module
Handles command registration conflicts between main.py and cogs
"""

import logging
import os
import inspect
from typing import Dict, List, Set, Callable, Any

logger = logging.getLogger(__name__)

# Store conflicting command names
CONFLICTING_COMMANDS = {
    "chart": "main.py",
    "analyze": "main.py",
    "health": "main.py",
    "indicator": "main.py",
    "help": "main.py",
    "strategies": "main.py",
    "position_size": "main.py",
}

def is_conflicting_command(command_name: str) -> bool:
    """Check if a command name conflicts with existing commands"""
    return command_name in CONFLICTING_COMMANDS

def get_command_owner(command_name: str) -> str:
    """Get the owner of a command (main.py or cog name)"""
    return CONFLICTING_COMMANDS.get(command_name, "unknown")

def register_cog_command_ownership(cog_name: str, command_names: List[str]) -> None:
    """Register a cog as the owner of specific commands"""
    for cmd in command_names:
        CONFLICTING_COMMANDS[cmd] = cog_name
    logger.debug(f"Registered commands {command_names} to {cog_name}")

def should_skip_command(cog_name: str, command_name: str) -> bool:
    """Determine if a command should be skipped in a specific cog"""
    if command_name not in CONFLICTING_COMMANDS:
        return False
    
    # If this cog is registered as the owner, don't skip it
    if CONFLICTING_COMMANDS[command_name] == cog_name:
        return False
    
    # Otherwise, skip it as it belongs to another owner
    logger.info(f"Skipping command '{command_name}' in {cog_name} as it's owned by {CONFLICTING_COMMANDS[command_name]}")
    return True

def resolve_command_conflicts(bot) -> None:
    """
    Handle command conflicts by prioritizing main.py commands over cog commands
    This should be run after all cogs are loaded
    """
    command_sources = {}
    
    # First, categorize all commands by their source
    for cmd_name, cmd in bot.all_commands.items():
        source = getattr(cmd.callback, '__module__', 'unknown')
        if 'cogs' in source:
            cog_name = source.split('.')[-1]
        else:
            cog_name = 'main'
            
        if cmd_name not in command_sources:
            command_sources[cmd_name] = []
        command_sources[cmd_name].append(cog_name)
    
    # Log any conflicts
    conflicts = {cmd: sources for cmd, sources in command_sources.items() if len(sources) > 1}
    if conflicts:
        logger.warning(f"Command conflicts detected: {conflicts}") 