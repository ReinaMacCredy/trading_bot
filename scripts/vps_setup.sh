#!/bin/bash

# Discord Trading Bot - VPS Setup Script
# This script sets up the environment and fixes common deployment issues

echo "🚀 Setting up Discord Trading Bot on VPS..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
echo "📍 Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Check if discord.py is installed
if python3 -c "import discord" 2>/dev/null; then
    echo "✅ discord.py is installed"
else
    echo "❌ discord.py not found, installing manually..."
    pip install discord.py>=2.3.0
fi

# Check for other critical dependencies
echo "🔍 Checking critical dependencies..."
python3 -c "
import sys
required_modules = ['discord', 'ccxt', 'pandas', 'numpy', 'dotenv']
missing = []
for module in required_modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError:
        missing.append(module)
        print(f'❌ {module}')

if missing:
    print(f'Missing modules: {missing}')
    sys.exit(1)
else:
    print('All critical modules installed!')
"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Creating from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "📝 Please edit .env file with your actual values"
    else
        echo "❌ env.example not found. Please create .env manually"
    fi
fi

# Make logs directory
mkdir -p logs

echo "🎉 Setup complete! Next steps:"
echo "1. Edit .env file with your Discord token and other settings"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python main.py" 