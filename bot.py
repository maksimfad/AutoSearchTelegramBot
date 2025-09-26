#!/usr/bin/env python3
"""
Telegram Bot for searching user mentions in channels and groups
"""

import asyncio
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
import schedule
from telegram import Update, Bot, Chat, Message
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.error import BadRequest, Forbidden, ChatMigrated, RetryAfter
import json
import aiohttp
from config import (
    TELEGRAM_BOT_TOKEN, SEARCH_INTERVAL_HOURS, SEARCH_TIME_HOUR,
    MAX_MESSAGES_PER_CHAT, FORWARD_DELAY_SECONDS, MAX_MENTIONS_PER_DAY,
    DATA_FILE, LOG_LEVEL, MENTION_PATTERNS, SUPPORTED_CHAT_TYPES
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MentionBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.user_data: Dict[int, Dict] = {}  # user_id -> user info
        self.subscribed_chats: Dict[int, Set[int]] = {}  # user_id -> set of chat_ids
        self.last_search: Dict[int, datetime] = {}  # user_id -> last search time
        self.searching_users: Set[int] = set()  # users currently being searched

        # Load data from storage
        self.load_data()

        # Setup handlers
        self.setup_handlers()

    def setup_handlers(self):
        """Setup command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("register", self.register_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("unregister", self.unregister_command))
        self.application.add_handler(CommandHandler("listchats", self.list_chats_command))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # Handler for forwarded messages
        self.application.add_handler(MessageHandler(filters.FORWARDED, self.handle_forwarded_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_message = (
            f"👋 Welcome to the Mention Bot, {user.first_name}!\n\n"
            "This bot will search for your mentions in channels and groups you subscribe to "
            "and forward them to you daily.\n\n"
            "📋 **How to use:**\n"
            "1. **Register:** Use /register <nickname> to set up monitoring\n"
            "2. **Add chats:** Forward me any message from channels/groups you want to monitor\n"
            "3. **Auto-monitoring:** If you register in a group/channel, it's automatically added!\n\n"
            "📋 **Available Commands:**\n"
            "• /register <nickname> - Set up your nickname for monitoring\n"
            "• /listchats - Show your monitored channels/groups\n"
            "• /status - Check your registration status\n"
            "• /help - Show this help message\n"
            "• /unregister - Stop monitoring completely\n\n"
            "🔍 The bot searches daily at 9:00 AM for your mentions."
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🆘 **Help - How to monitor your mentions:**\n\n"
            "1️⃣ **Register your nickname:**\n"
            "`/register @your_username` or `/register nickname123`\n\n"
            "2️⃣ **Add channels/groups to monitor:**\n"
            "• Forward me any message from the channel/group\n"
            "• Or register directly in the group/channel (auto-added)\n\n"
            "3️⃣ **That's it!** The bot will:\n"
            "• Search your subscribed chats daily at 9:00 AM\n"
            "• Forward any messages mentioning your nickname\n"
            "• Include source information and context\n\n"
            "📋 **Other commands:**\n"
            "• /listchats - Show monitored channels/groups\n"
            "• /status - Check your registration info\n"
            "• /unregister - Stop monitoring\n\n"
            "💡 **Pro tip:** You can forward messages from private channels too!"
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command"""
        user = update.effective_user

        if len(context.args) < 1:
            await update.message.reply_text(
                "Please provide your nickname or username after /register command.\n"
                "Example: /register @your_username or /register nickname123"
            )
            return

        nickname = " ".join(context.args)

        # Get current chat if user is registering from a group/channel
        current_chat = update.effective_chat
        initial_chats = set()

        if current_chat and current_chat.type in ['group', 'supergroup', 'channel']:
            initial_chats.add(current_chat.id)
            chat_type = "channel" if current_chat.type in ['channel', 'supergroup'] else "group"

        self.user_data[user.id] = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'nickname': nickname,
            'registered_at': datetime.now().isoformat(),
            'subscribed_chats': list(initial_chats)
        }

        self.subscribed_chats[user.id] = initial_chats

        # Save data
        self.save_data()

        if initial_chats:
            await update.message.reply_text(
                f"✅ Successfully registered!\n\n"
                f"👤 Nickname to monitor: {nickname}\n"
                f"📊 Auto-added current {chat_type}: {current_chat.title}\n"
                f"🔍 Bot will search for your mentions daily at {SEARCH_TIME_HOUR}:00 AM\n\n"
                f"💡 Tip: Forward me messages from other channels/groups you want to monitor!"
            )
        else:
            await update.message.reply_text(
                f"✅ Successfully registered!\n\n"
                f"👤 Nickname to monitor: {nickname}\n"
                f"📊 No chats detected yet\n"
                f"🔍 Bot will search for your mentions daily at {SEARCH_TIME_HOUR}:00 AM\n\n"
                f"💡 Forward me messages from channels/groups you want to monitor!"
            )

    async def handle_forwarded_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle forwarded messages to add chats to monitoring"""
        user = update.effective_user
        forwarded_message = update.message.forward_origin

        if user.id not in self.user_data:
            await update.message.reply_text(
                "❌ You need to register first using /register <nickname>"
            )
            return

        if not forwarded_message:
            return

        # Get the original chat from forwarded message
        if hasattr(forwarded_message, 'chat'):
            original_chat = forwarded_message.chat
        elif hasattr(update.message, 'forward_from_chat'):
            original_chat = update.message.forward_from_chat
        else:
            await update.message.reply_text(
                "❌ Cannot detect the source chat. Please try forwarding again."
            )
            return

        if not original_chat:
            return

        chat_id = original_chat.id

        # Check if chat is already subscribed
        if chat_id in self.subscribed_chats.get(user.id, set()):
            chat_type = "channel" if original_chat.type in ['channel', 'supergroup'] else "group"
            await update.message.reply_text(
                f"ℹ️ {chat_type.title()} '{original_chat.title}' is already in your monitoring list!"
            )
            return

        # Add chat to user's subscriptions
        if user.id not in self.subscribed_chats:
            self.subscribed_chats[user.id] = set()
        self.subscribed_chats[user.id].add(chat_id)

        # Update user data
        self.user_data[user.id]['subscribed_chats'] = list(self.subscribed_chats[user.id])

        # Save data
        self.save_data()

        chat_type = "📢 Channel" if original_chat.type in ['channel', 'supergroup'] else "👥 Group"
        await update.message.reply_text(
            f"✅ {chat_type} '{original_chat.title}' added to your monitoring list!\n"
            f"🔍 Bot will now search for your mentions in this chat daily."
        )

    async def list_chats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /listchats command"""
        user = update.effective_user

        if user.id not in self.user_data:
            await update.message.reply_text(
                "❌ You need to register first using /register <nickname>"
            )
            return

        subscribed_chats = self.subscribed_chats.get(user.id, set())

        if not subscribed_chats:
            await update.message.reply_text(
                "📭 No subscribed chats found.\n"
                "Use /subscribe in channels/groups you want to monitor."
            )
            return

        chat_list = "📋 **Your Subscribed Chats:**\n\n"

        for chat_id in subscribed_chats:
            try:
                chat = await self.application.bot.get_chat(chat_id)
                chat_type = "📢 Channel" if chat.type in ['channel', 'supergroup'] else "👥 Group"
                chat_list += f"• {chat_type}: {chat.title}\n"
            except Exception as e:
                chat_list += f"• Chat ID: {chat_id} (unable to fetch info)\n"

        await update.message.reply_text(chat_list, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user = update.effective_user

        if user.id not in self.user_data:
            await update.message.reply_text(
                "❌ You are not registered yet. Use /register to set up monitoring."
            )
            return

        user_info = self.user_data[user.id]
        last_search = self.last_search.get(user.id, "Never")
        if isinstance(last_search, datetime):
            last_search = last_search.strftime("%Y-%m-%d %H:%M:%S")

        status_message = (
            f"📊 **Your Status:**\n\n"
            f"👤 Monitored nickname: `{user_info['nickname']}`\n"
            f"📱 Telegram ID: `{user.id}`\n"
            f"👥 Subscribed channels/groups: `{len(user_info['subscribed_chats'])}`\n"
            f"⏰ Last search: `{last_search}`\n"
            f"📅 Registered: `{user_info['registered_at'][:10]}`"
        )

        await update.message.reply_text(status_message, parse_mode='Markdown')

    async def unregister_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unregister command"""
        user = update.effective_user

        if user.id not in self.user_data:
            await update.message.reply_text(
                "❌ You are not registered yet."
            )
            return

        # Remove user data
        del self.user_data[user.id]
        if user.id in self.subscribed_chats:
            del self.subscribed_chats[user.id]
        if user.id in self.last_search:
            del self.last_search[user.id]

        # Save data
        self.save_data()

        await update.message.reply_text(
            "✅ Successfully unregistered! The bot will no longer monitor your mentions."
        )

    async def get_user_subscriptions(self, user_id: int) -> Set[int]:
        """Get user's subscribed channels and groups"""
        subscribed_chats = set()

        try:
            # Note: In a real implementation, getting all user's chats requires
            # special bot permissions or user interaction. For now, we rely
            # on users manually subscribing to chats using /subscribe command.

            # However, we can try to get some basic information about chats
            # the user has interacted with recently

            # This is a simplified approach - in production you'd need:
            # 1. Bot to be admin in groups/channels
            # 2. User to provide chat IDs
            # 3. Or use Telegram Bot API's getChatMember to discover chats

            logger.info(f"Getting subscriptions for user {user_id}")

        except Exception as e:
            logger.error(f"Error getting user subscriptions: {e}")

        return subscribed_chats

    async def search_mentions(self):
        """Daily search for user mentions"""
        logger.info("Starting daily mention search...")

        current_time = datetime.now()
        users_to_search = []

        # Filter users who need searching (either never searched or last search was more than 24h ago)
        for user_id, user_info in self.user_data.items():
            last_search = self.last_search.get(user_id)
            if last_search is None or (current_time - last_search).total_seconds() > (SEARCH_INTERVAL_HOURS * 3600):
                users_to_search.append((user_id, user_info))

        if not users_to_search:
            logger.info("No users need searching at this time.")
            return

        logger.info(f"Searching mentions for {len(users_to_search)} users...")

        for user_id, user_info in users_to_search:
            try:
                if user_id in self.searching_users:
                    logger.info(f"User {user_id} is already being searched, skipping...")
                    continue

                self.searching_users.add(user_id)
                await self.search_mentions_for_user(user_id, user_info)
                self.searching_users.remove(user_id)

            except Exception as e:
                logger.error(f"Error searching mentions for user {user_id}: {e}")
                self.searching_users.discard(user_id)

        logger.info("Daily mention search completed.")

    async def search_mentions_for_user(self, user_id: int, user_info: Dict):
        """Search mentions for a specific user"""
        nickname = user_info['nickname']
        subscribed_chats = user_info['subscribed_chats']

        if not subscribed_chats:
            logger.info(f"No subscribed chats for user {user_id}")
            return

        found_mentions = []
        search_keywords = self._prepare_search_keywords(nickname, user_id)

        logger.info(f"Searching for mentions of user {user_id} with keywords: {search_keywords}")

        for chat_id in subscribed_chats:
            try:
                chat_mentions = await self._search_chat_for_mentions(chat_id, search_keywords, user_id)
                found_mentions.extend(chat_mentions)

                # Add delay to avoid rate limits
                await asyncio.sleep(FORWARD_DELAY_SECONDS)

            except Exception as e:
                logger.error(f"Error searching chat {chat_id} for user {user_id}: {e}")
                continue

        if found_mentions:
            await self.forward_mentions(user_id, found_mentions)
            logger.info(f"Found {len(found_mentions)} mentions for user {user_id}")
        else:
            logger.info(f"No mentions found for user {user_id}")

        self.last_search[user_id] = datetime.now()
        self.save_data()

    def _prepare_search_keywords(self, nickname: str, user_id: int) -> List[str]:
        """Prepare search keywords from nickname and user ID"""
        keywords = []

        # Add nickname variations
        keywords.append(nickname)
        keywords.append(f"@{nickname.replace('@', '')}")
        keywords.append(nickname.replace('@', ''))

        # Add user ID
        keywords.append(str(user_id))

        # Add common mention patterns
        for pattern in MENTION_PATTERNS:
            if '@' in pattern and nickname:
                username = nickname.replace('@', '')
                keywords.append(pattern.replace('{username}', username))
            elif '#' in pattern and nickname:
                keywords.append(pattern.replace('{hashtag}', nickname.replace('#', '')))

        return list(set(keywords))  # Remove duplicates

    async def _search_chat_for_mentions(self, chat_id: int, keywords: List[str], user_id: int) -> List[Dict]:
        """Search a specific chat for mentions"""
        found_mentions = []

        try:
            # Get chat information first
            chat = await self.application.bot.get_chat(chat_id)

            # Only search in supported chat types
            if chat.type not in SUPPORTED_CHAT_TYPES:
                logger.info(f"Skipping unsupported chat type: {chat.type}")
                return found_mentions

            # Check if bot can read messages in this chat
            if not await self._can_read_chat(chat_id):
                logger.warning(f"Cannot read messages in chat {chat_id}")
                return found_mentions

            # Get chat history - this is where you'd implement actual message retrieval
            # Note: The Telegram Bot API has limitations on getting chat history
            # In practice, you'd need to use a different approach or have special permissions

            # For demonstration purposes, we'll simulate finding mentions
            # In a real implementation, you would:
            # 1. Use getChatHistory with proper pagination
            # 2. Search through messages for keywords
            # 3. Handle rate limits and errors

            # Simulate searching recent messages
            simulated_mentions = await self._simulate_message_search(chat_id, keywords, user_id)

            found_mentions.extend(simulated_mentions)

        except RetryAfter as e:
            logger.warning(f"Rate limited when searching chat {chat_id}, retrying after {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
            # Retry once
            try:
                simulated_mentions = await self._simulate_message_search(chat_id, keywords, user_id)
                found_mentions.extend(simulated_mentions)
            except Exception as retry_error:
                logger.error(f"Retry failed for chat {chat_id}: {retry_error}")

        except Exception as e:
            logger.error(f"Error searching chat {chat_id}: {e}")

        return found_mentions

    async def _can_read_chat(self, chat_id: int) -> bool:
        """Check if bot can read messages in a chat"""
        try:
            # Try to get chat info - if successful, we can likely read messages
            chat = await self.application.bot.get_chat(chat_id)
            return True
        except Forbidden:
            logger.warning(f"Bot is forbidden from accessing chat {chat_id}")
            return False
        except Exception as e:
            logger.error(f"Error checking chat access for {chat_id}: {e}")
            return False

    async def _simulate_message_search(self, chat_id: int, keywords: List[str], user_id: int) -> List[Dict]:
        """Simulate message search (replace with actual implementation)"""
        found_mentions = []

        # This is a simulation - in production you'd implement actual message retrieval
        # using the Telegram Bot API or other methods

        # For demo purposes, we'll randomly simulate finding mentions
        # In a real bot, you would:
        # 1. Use bot.get_chat_history(chat_id, limit=MAX_MESSAGES_PER_CHAT)
        # 2. Search through the messages for keywords
        # 3. Extract relevant message information

        try:
            chat = await self.application.bot.get_chat(chat_id)

            # Simulate finding 0-3 mentions (for demo purposes)
            import random
            num_mentions = random.randint(0, 3)

            for i in range(num_mentions):
                mention = {
                    'chat_id': chat_id,
                    'chat_title': chat.title,
                    'message_id': random.randint(1000000, 9999999),
                    'timestamp': datetime.now() - timedelta(hours=random.randint(1, 24)),
                    'matched_keyword': random.choice(keywords),
                    'message_text': f"Sample message containing {random.choice(keywords)}"
                }
                found_mentions.append(mention)

        except Exception as e:
            logger.error(f"Error in simulated search for chat {chat_id}: {e}")

        return found_mentions

    async def forward_mentions(self, user_id: int, mentions: List[Dict]):
        """Forward found mentions to the user"""
        try:
            if not mentions:
                return

            # Limit number of mentions to avoid spam
            if len(mentions) > MAX_MENTIONS_PER_DAY:
                mentions = mentions[:MAX_MENTIONS_PER_DAY]
                logger.info(f"Limited mentions for user {user_id} to {MAX_MENTIONS_PER_DAY}")

            # Send summary message
            summary = (
                f"🔍 **Found {len(mentions)} mention(s) for you:**\n\n"
                f"📅 Search completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            await self.application.bot.send_message(chat_id=user_id, text=summary, parse_mode='Markdown')

            forwarded_count = 0

            for mention in mentions:
                try:
                    # Forward the original message
                    forwarded_msg = await self.application.bot.forward_message(
                        chat_id=user_id,
                        from_chat_id=mention['chat_id'],
                        message_id=mention['message_id']
                    )

                    # Add contextual information
                    context_info = (
                        f"📍 **Source:** {mention['chat_title']}\n"
                        f"🕐 **Time:** {mention['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"🔍 **Matched:** `{mention['matched_keyword']}`\n"
                        f"💬 **Message:** {mention['message_text'][:100]}...\n"
                    )

                    await self.application.bot.send_message(
                        chat_id=user_id,
                        text=context_info,
                        parse_mode='Markdown',
                        reply_to_message_id=forwarded_msg.message_id
                    )

                    forwarded_count += 1

                    # Add delay to avoid rate limits
                    await asyncio.sleep(FORWARD_DELAY_SECONDS)

                except RetryAfter as e:
                    logger.warning(f"Rate limited when forwarding to user {user_id}, waiting {e.retry_after}s")
                    await asyncio.sleep(e.retry_after)
                    # Retry once
                    try:
                        await self.application.bot.forward_message(
                            chat_id=user_id,
                            from_chat_id=mention['chat_id'],
                            message_id=mention['message_id']
                        )
                        forwarded_count += 1
                    except Exception as retry_error:
                        logger.error(f"Retry failed for mention: {retry_error}")

                except Forbidden:
                    logger.error(f"Cannot send messages to user {user_id} (blocked or forbidden)")
                    break

                except Exception as e:
                    logger.error(f"Error forwarding mention to user {user_id}: {e}")

            # Send completion summary
            completion_msg = (
                f"✅ **Forwarding completed!**\n"
                f"📊 Successfully forwarded: {forwarded_count}/{len(mentions)} mentions\n"
                f"⚡ Next search: {SEARCH_TIME_HOUR}:00 AM daily"
            )

            await self.application.bot.send_message(
                chat_id=user_id,
                text=completion_msg,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error forwarding mentions to user {user_id}: {e}")

    def save_data(self):
        """Save user data to file"""
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump({
                    'user_data': self.user_data,
                    'subscribed_chats': {k: list(v) for k, v in self.subscribed_chats.items()},
                    'last_search': {k: v.isoformat() if isinstance(v, datetime) else str(v) for k, v in self.last_search.items()}
                }, f, indent=2)
            logger.info(f"Data saved to {DATA_FILE}")
        except Exception as e:
            logger.error(f"Error saving data to {DATA_FILE}: {e}")

    def load_data(self):
        """Load user data from file"""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)

                self.user_data = data.get('user_data', {})
                self.subscribed_chats = {int(k): set(v) for k, v in data.get('subscribed_chats', {}).items()}
                self.last_search = {}
                for k, v in data.get('last_search', {}).items():
                    try:
                        self.last_search[int(k)] = datetime.fromisoformat(v)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse last_search time for user {k}: {v}")

                logger.info(f"Data loaded from {DATA_FILE}")
            else:
                logger.info(f"No existing data file found at {DATA_FILE}, starting fresh")
        except Exception as e:
            logger.error(f"Error loading data from {DATA_FILE}: {e}")

    def start_scheduler(self):
        """Start the daily search scheduler"""
        schedule_time = f"{SEARCH_TIME_HOUR"02d"}:00"
        schedule.every().day.at(schedule_time).do(lambda: asyncio.create_task(self.search_mentions()))

        logger.info(f"Scheduler started. Bot will search for mentions daily at {schedule_time}")

        # Run the scheduler in a separate thread
        import threading
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()

    def run_scheduler(self):
        """Run the scheduler loop"""
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)

    def run(self):
        """Start the bot"""
        logger.info("Starting Mention Bot...")

        # Start the scheduler
        self.start_scheduler()

        # Start the bot
        self.application.run_polling()

if __name__ == '__main__':
    # Check if token is available
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables or config.py")
        logger.error("Please set TELEGRAM_BOT_TOKEN in your environment or config.py")
        exit(1)

    try:
        bot = MentionBot(TELEGRAM_BOT_TOKEN)
        logger.info("🚀 Mention Bot started successfully!")
        logger.info(f"📊 Configuration: Search at {SEARCH_TIME_HOUR}:00, every {SEARCH_INTERVAL_HOURS}h")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        exit(1)