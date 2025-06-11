#!/bin/bash

# Simple Trading Bot Deployment Script
# Usage: ./simple-deploy.sh [bot|web|all]

set -e

MODE=${1:-bot}
echo "🚀 Starting Simple Trading Bot Deployment - Mode: $MODE"

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo "❌ Error: .env file not found in root directory"
    echo "📝 Please create .env file with:"
    echo "   DISCORD_TOKEN=your_discord_token"
    echo "   BINANCE_API_KEY=your_api_key (optional)"
    echo "   BINANCE_SECRET=your_secret (optional)"
    exit 1
fi

# Load environment
export $(cat ../.env | grep -v '^#' | xargs)

case $MODE in
    "bot")
        echo "🤖 Deploying Discord Bot only..."
        docker-compose -f simple-deploy.yml up --build -d bot
        ;;
    "web")
        echo "🌐 Deploying Web Server with Redis..."
        docker-compose -f simple-deploy.yml --profile web up --build -d
        ;;
    "all")
        echo "🔥 Deploying Full Stack (Bot + Web + Redis)..."
        docker-compose -f simple-deploy.yml --profile web up --build -d
        ;;
    *)
        echo "❌ Invalid mode. Use: bot, web, or all"
        exit 1
        ;;
esac

echo "✅ Deployment completed!"
echo "📊 Check status: docker-compose -f simple-deploy.yml ps"
echo "📋 View logs: docker-compose -f simple-deploy.yml logs -f"
echo "🛑 Stop: docker-compose -f simple-deploy.yml down" 