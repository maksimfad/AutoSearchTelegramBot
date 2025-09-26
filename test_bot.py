#!/usr/bin/env python3
"""
Test script for Telegram Mention Bot
Tests basic functionality without starting the full bot
"""

import os
import sys
import asyncio
from config import TELEGRAM_BOT_TOKEN
from bot import MentionBot

async def test_bot_setup():
    """Test basic bot setup and configuration"""
    print("🧪 Testing Telegram Mention Bot Setup...")

    # Check token
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment")
        return False

    print(f"✅ Bot token found (length: {len(TELEGRAM_BOT_TOKEN)})")

    # Test bot initialization
    try:
        bot = MentionBot(TELEGRAM_BOT_TOKEN)
        print("✅ Bot initialized successfully")
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return False

    # Test data loading
    try:
        bot.load_data()
        print("✅ Data loading works")
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False

    # Test configuration
    print(f"✅ Search time: {bot.search_time}:00")
    print(f"✅ Search interval: {bot.search_interval} hours")

    return True

def test_imports():
    """Test that all required modules can be imported"""
    print("\n📦 Testing imports...")

    required_modules = [
        'telegram',
        'telegram.ext',
        'schedule',
        'asyncio',
        'json',
        'logging',
        'os',
        'datetime'
    ]

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - Not installed")
            return False

    return True

def main():
    """Run all tests"""
    print("🚀 Telegram Mention Bot - Test Suite")
    print("=" * 50)

    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please install dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)

    # Test bot setup
    if asyncio.run(test_bot_setup()):
        print("\n✅ All tests passed! Bot is ready to run.")
        print("\nTo start the bot:")
        print("python run_bot.py")
        print("\nOr with Docker:")
        print("docker-compose up -d")
    else:
        print("\n❌ Bot setup tests failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()