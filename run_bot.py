#!/usr/bin/env python3
"""
Production runner for Telegram Mention Bot
Handles daemon mode, logging, and graceful shutdown
"""

import os
import sys
import signal
import logging
from datetime import datetime
from bot import MentionBot
from config import TELEGRAM_BOT_TOKEN, LOG_LEVEL

# Configure logging for production
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BotRunner:
    def __init__(self):
        self.bot = None
        self.running = False

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

        if self.bot:
            logger.info("Stopping bot...")
            # The bot will handle cleanup in its own signal handlers

    def run(self):
        """Run the bot with proper signal handling"""
        if not TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            sys.exit(1)

        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            self.bot = MentionBot(TELEGRAM_BOT_TOKEN)
            self.running = True

            logger.info("🚀 Starting Telegram Mention Bot...")
            logger.info(f"📊 Configuration: Search at {self.bot.search_time}:00, every {self.bot.search_interval}h")
            logger.info("Press Ctrl+C to stop the bot")

            self.bot.run()

        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            sys.exit(1)
        finally:
            self.running = False
            logger.info("Bot shutdown complete")

if __name__ == '__main__':
    runner = BotRunner()
    runner.run()