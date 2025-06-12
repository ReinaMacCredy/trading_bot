# Code Refactoring: Legacy to Modern Architecture

## Overview

This document outlines the refactoring process of moving legacy code to proper locations in the modern project architecture. The goal was to ensure all code follows the established project structure while maintaining compatibility.

## Changes Made

The following files were refactored:

1. `legacy/strategies.py` → `src/trading/strategies/legacy_strategies.py`
   - Moved trading strategy implementations to the proper strategies directory
   - Updated import paths to reference the new locations
   - Renamed potential duplicates to avoid naming conflicts with modern implementations

2. `legacy/indicators.py` → `src/trading/indicators/legacy_indicators.py`
   - Moved technical indicator implementations to the indicators directory
   - Maintained the original `IndicatorFactory` for backward compatibility
   - Updated import references to use proper module paths

3. `legacy/bot.py` → `src/bot/legacy_bot.py`
   - Moved Discord bot utilities to the bot directory
   - Maintained important functions like `create_signal_embed` for signal generation

4. `legacy/trading.py` → `src/trading/core/legacy_trading.py`
   - Moved core trading functionality to the trading/core directory
   - Updated import references to use the new module paths
   - Ensured compatibility with existing API clients

## Module Updates

The following module initialization files were updated to include the legacy components:

- `src/trading/strategies/__init__.py`: Added legacy strategy imports with appropriate aliases to avoid conflicts
- `src/trading/indicators/__init__.py`: Added legacy indicator imports
- `src/bot/__init__.py`: Added essential bot utility functions
- `src/trading/core/__init__.py`: Added the legacy TradingBot class

## Next Steps

1. Gradually transition from legacy components to modern implementations
2. Update calling code to use the new module paths
3. Add unit tests for the legacy components to ensure compatibility during transition
4. Document any API differences between legacy and modern implementations 