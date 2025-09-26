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
- `/subscribe` - Add current chat to monitoring list (use in groups/channels)
- `/unsubscribe` - Remove current chat from monitoring list
- `/listchats` - Show your subscribed channels/groups
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
2. **Chat Subscription**: Users add channels/groups using `/subscribe` command in those chats
3. **Daily Search**: The bot searches all subscribed chats daily at the configured time
4. **Message Forwarding**: Found mentions are forwarded to users with source information

## Important Notes

### Bot Permissions

For the bot to work effectively, it needs to be added to the channels/groups you want to monitor:

1. Add the bot as an administrator in channels
2. Add the bot as a member in groups
3. Use `/subscribe` command in each chat you want to monitor

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
- Ensure the bot is added to the channels/groups
- Check that you're using the correct nickname format
- Verify the bot has permission to read messages

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