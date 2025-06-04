#!/usr/bin/env python3
"""
Discord Bot Test Script
This script helps diagnose common issues with Discord bot setup
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    print("🔍 Checking Python packages...")
    
    required_packages = [
        'discord',
        'python-dotenv',
        'ccxt',
        'pandas',
        'numpy',
        'aiohttp'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - installed")
        except ImportError:
            print(f"❌ {package} - missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed!")
        return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\n🔍 Checking environment configuration...")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("💡 Create .env file from env.example")
        return False
    
    print("✅ .env file exists")
    
    # Check for Discord token
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        discord_token = os.getenv('DISCORD_TOKEN')
        if not discord_token:
            print("❌ DISCORD_TOKEN not found in .env")
            print("💡 Add your Discord bot token to .env file")
            return False
        
        if discord_token == "your_discord_bot_token_here":
            print("❌ DISCORD_TOKEN is still placeholder value")
            print("💡 Replace with your actual Discord bot token")
            return False
            
        print("✅ DISCORD_TOKEN is configured")
        return True
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def check_bot_permissions():
    """Check if bot has necessary Discord permissions"""
    print("\n🔍 Checking bot permissions...")
    print("📋 Your bot needs these permissions:")
    print("   - Send Messages")
    print("   - Read Message History") 
    print("   - Use Slash Commands")
    print("   - Embed Links")
    print("   - Attach Files")
    print("   - Add Reactions")
    print("\n💡 Make sure these are enabled in Discord Developer Portal")

def test_basic_connection():
    """Test basic Discord connection"""
    print("\n🔍 Testing Discord connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import discord
        from discord.ext import commands
        
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("❌ Cannot test connection - no token found")
            return False
        
        # Create a simple test bot
        intents = discord.Intents.default()
        intents.message_content = True
        
        test_bot = commands.Bot(command_prefix='test!', intents=intents)
        
        @test_bot.event
        async def on_ready():
            print(f"✅ Bot connected as {test_bot.user}")
            print(f"📊 Connected to {len(test_bot.guilds)} server(s)")
            await test_bot.close()
        
        print("🔗 Attempting connection...")
        test_bot.run(token)
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🤖 Discord Trading Bot Diagnostic Tool")
    print("=" * 50)
    
    # Check 1: Requirements
    packages_ok = check_requirements()
    
    # Check 2: Environment
    env_ok = check_env_file()
    
    # Check 3: Permissions
    check_bot_permissions()
    
    # Check 4: Connection (if other checks pass)
    if packages_ok and env_ok:
        try:
            test_basic_connection()
        except KeyboardInterrupt:
            print("\n⚠️  Connection test interrupted")
    
    print("\n" + "=" * 50)
    print("🎯 Diagnostic Summary:")
    
    if packages_ok and env_ok:
        print("✅ Setup looks good! Try running the bot with: python3 main.py")
    else:
        print("❌ Setup issues found. Fix the above problems and try again.")
    
    print("\n💡 Common solutions:")
    print("   1. Copy env.example to .env and add your Discord token")
    print("   2. Install dependencies: pip install -r requirements.txt")  
    print("   3. Check bot permissions in Discord Developer Portal")
    print("   4. Make sure bot is invited to your server")
    print("   5. Try commands with 'b!' prefix (e.g., b!help)")

if __name__ == "__main__":
    main() 