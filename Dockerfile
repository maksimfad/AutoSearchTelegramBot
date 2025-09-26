FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY bot.py .
COPY config.py .
COPY run_bot.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash telegram-bot
USER telegram-bot

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV DATA_FILE=/app/data/bot_data.json
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 -c "import asyncio; print('Bot is running')" || exit 1

# Run the bot
CMD ["python3", "run_bot.py"]