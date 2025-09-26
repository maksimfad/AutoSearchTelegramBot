#!/usr/bin/env python3
"""
Configuration settings for the Mention Bot
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Search Configuration
SEARCH_INTERVAL_HOURS = int(os.getenv('SEARCH_INTERVAL_HOURS', '24'))  # Daily by default
SEARCH_TIME_HOUR = int(os.getenv('SEARCH_TIME_HOUR', '9'))  # 9 AM by default
MAX_MESSAGES_PER_CHAT = int(os.getenv('MAX_MESSAGES_PER_CHAT', '100'))
FORWARD_DELAY_SECONDS = float(os.getenv('FORWARD_DELAY_SECONDS', '1.0'))

# Bot Settings
MAX_MENTIONS_PER_DAY = int(os.getenv('MAX_MENTIONS_PER_DAY', '50'))
ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() == 'true'

# File paths
DATA_FILE = os.getenv('DATA_FILE', 'bot_data.json')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Supported file formats for data storage
SUPPORTED_FORMATS = ['json']

# Chat types to search in
SUPPORTED_CHAT_TYPES = ['group', 'supergroup', 'channel']

# Message search patterns
MENTION_PATTERNS = [
    r'@{username}',
    r'#{hashtag}',
    r't\.me/{username}',
    r'telegram\.me/{username}',
]

# Bot capabilities
BOT_CAPABILITIES = {
    'can_read_messages': True,
    'can_forward_messages': True,
    'can_send_messages': True,
}

# Error handling
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = float(os.getenv('RETRY_DELAY', '5.0'))