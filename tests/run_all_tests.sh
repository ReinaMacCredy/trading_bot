#!/bin/bash
# Run all Trading Bot tests

# Set environment variables for testing
export DISCORD_TOKEN="test_token"
export ENVIRONMENT="test"

# Capture the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "====================================="
echo "Running Trading Bot Tests"
echo "====================================="

# Run each test file
echo "Running Signal Command Test..."
python3 test_signal_command.py

# Add more test runners here as they are developed
# echo "Running Another Test..."
# python3 another_test.py

echo "====================================="
echo "All tests completed"
echo "=====================================" 