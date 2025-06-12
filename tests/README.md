# Trading Bot Tests

This directory contains tests for the Trading Bot's functionality.

## Signal Command Tests

The `test_signal_command.py` file contains tests for the `b!signal` command (implemented as `tradesignal` in the codebase).

These tests verify that:
1. The `tradesignal` command works correctly with a standard symbol (e.g., "BTC")
2. The `signalcmd` command alias properly forwards to the `tradesignal` command
3. The commands handle unusual symbols correctly (e.g., symbols with numbers, symbols already including "USDT")

### Running the Signal Command Tests

To run the tests for the signal command:

```bash
cd tests
python3 test_signal_command.py
```

## Test Requirements

The tests require:
- Python 3.6+
- discord.py library
- pytest and pytest-asyncio (for some test files)

To install the required libraries:

```bash
pip3 install pytest pytest-asyncio
```

## Command Prefix

Note that all commands in this bot use the `b!` prefix as specified in the requirements. The tests verify that commands work with this prefix. 