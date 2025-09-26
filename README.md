# Telegram Mention Bot

A Telegram bot that searches for user mentions in subscribed channels and groups and forwards them to users daily.

## Features

- 🔍 **Daily Search**: Automatically searches for your mentions once per day
- 📢 **Multi-Chat Support**: Monitor multiple channels and groups
- 👥 **User Registration**: Register your nickname for monitoring
- 📱 **Message Forwarding**: Forwards found mentions with context
- ⏰ **Configurable Schedule**: Set custom search times
- 🔧 **Easy Management**: Simple commands for chat subscription management

## Commands

- `/start` - Welcome message and command overview
- `/register <nickname>` - Register your nickname for monitoring
- `/addchannel @username` - Add channel by username or chat ID
- `/help` - Detailed usage instructions
- `/listchats` - Show your monitored channels/groups
- `/status` - Check your registration status
- `/unregister` - Stop monitoring completely

## Setup

### 1. Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### 2. Installation

1. Clone or download this project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create environment configuration:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

### 3. Configuration

The bot can be configured via environment variables in `.env`:

- `TELEGRAM_BOT_TOKEN` - Your bot token (required)
- `SEARCH_INTERVAL_HOURS` - Search interval in hours (default: 24)
- `SEARCH_TIME_HOUR` - Hour for daily search (default: 9)
- `MAX_MESSAGES_PER_CHAT` - Max messages to search per chat (default: 100)
- `MAX_MENTIONS_PER_DAY` - Max mentions to forward per day (default: 50)
- `DATA_FILE` - Path to data storage file (default: bot_data.json)
- `LOG_LEVEL` - Logging level (default: INFO)

### 4. Running the Bot

```bash
python bot.py
```

The bot will start and begin monitoring according to your schedule.

## How It Works

1. **Registration**: Users register with `/register <nickname>` to set up monitoring
2. **Adding Chats**: Users can add channels/groups in several ways:
   - Forward any message from the channel/group to the bot
   - Register directly in the group/channel (auto-added)
   - Use `/addchannel @username` or `/addchannel -1001234567890`
3. **Daily Search**: The bot searches all monitored chats daily at the configured time
4. **Message Forwarding**: Found mentions are forwarded to users with source information

**Important**: The bot can only monitor chats where it has been added as a member and has permission to read messages.

## Important Notes

### Bot Permissions & Limitations

**Important**: The bot **cannot** automatically access all channels you are subscribed to, because:

1. **Privacy**: Telegram doesn't allow bots to see users' subscription lists
2. **API Limitations**: Bot API doesn't provide methods to get user's channels
3. **Permissions**: Bot can only access chats where it's explicitly added

**To monitor channels:**

1. **Add the bot** to the channels/groups you want to monitor
2. **Grant permissions** for the bot to read messages
3. **Add the chats** using one of these methods:
   - Forward a message from the chat
   - Register directly in the chat
   - Use `/addchannel @username` or `/addchannel -1001234567890`

**Note**: Bot monitors your nickname/ID only in chats where you've explicitly added it.

## Understanding Telegram Bot Limitations

**This bot works differently than you might expect:**

❌ **Cannot automatically monitor all your subscriptions** - Telegram doesn't allow bots to access users' channel lists for privacy reasons

❌ **Cannot read your channel list** - Bot API doesn't provide this functionality

✅ **Can monitor chats where it's explicitly added** - This is the only way it works

✅ **Searches for your nickname/ID in those chats** - And forwards mentions to you

### How to Use It Properly:

1. **Choose channels you want monitored** (the ones that actually mention you)
2. **Add the bot to those channels** as a member or admin
3. **Tell the bot to monitor them** using forwarding, `/addchannel`, or registration
4. **Bot searches daily** for your nickname/ID in those specific chats

This is actually **more efficient** because:
- You control exactly which chats are monitored
- No unnecessary searching through hundreds of channels
- Bot only looks in places where you're actually mentioned

### Limitations

- **Message History**: The bot can only search recent messages (last 100 by default)
- **Private Groups**: The bot cannot access private groups where it's not a member
- **Rate Limits**: Telegram has rate limits; the bot includes delays to respect them
- **Search Accuracy**: The bot searches for text patterns and may have false positives

### Data Storage

User data is stored in `bot_data.json` by default. This includes:
- User registration information
- Subscribed chat IDs
- Last search timestamps

## Development

### Project Structure

```
├── bot.py              # Main bot application
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── bot_data.json       # User data storage
├── .env               # Environment variables
└── README.md          # This file
```

### Adding Features

The bot is designed to be extensible. Key areas for enhancement:

1. **Real Message Search**: Implement actual message retrieval using Telegram API
2. **Advanced Filtering**: Add filters for message types, date ranges, etc.
3. **Web Interface**: Create a web dashboard for monitoring
4. **Database Integration**: Replace JSON storage with a proper database

### Troubleshooting

**Bot not finding mentions:**
- ✅ Ensure the bot is added to the channels/groups you want to monitor
- ✅ Check that you're using the correct nickname format in `/register`
- ✅ Verify the bot has permission to read messages in those chats
- ✅ Make sure you've added the chats using forwarding, `/addchannel`, or registration
- ✅ Check `/listchats` to see if your channels are actually being monitored

**Bot not adding forwarded chats:**
- Check that the message was actually **forwarded** (not just copied)
- Ensure the original message is from a **channel or group**
- Make sure the bot is a **member** of that channel/group
- Try forwarding again if the first attempt didn't work

**Cannot add channel by username:**
- Make sure the username is correct (e.g., @mychannel)
- Ensure the bot is a member of that channel
- Try using the chat ID instead: `/addchannel -1001234567890`
- Check that the channel is public or the bot has access

**Bot not responding:**
- Check that the bot token is correct
- Ensure the bot is not rate-limited
- Check the logs for error messages

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify your configuration
3. Ensure all dependencies are installed correctly

## License

This project is provided as-is for educational purposes.