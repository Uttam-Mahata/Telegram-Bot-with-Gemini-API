# Telegram Bot with Gemini API

A Telegram bot that uses Google's Gemini API to generate responses to user messages. The bot processes text messages and responds using the Gemini 1.5 Flash model.

## Features

- Responds to text messages using Google's Gemini AI
- Simple command interface with `/start` command
- Real-time streaming responses from Gemini API
- Error handling and logging

## Prerequisites

- Python 3.7 or higher
- A Telegram Bot Token (obtained from [@BotFather](https://t.me/botfather))
- Google Gemini API Key

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd Telegram\ Bot\ with\ Gemini\ API
```

2. Install the required dependencies:
```bash
pip install python-telegram-bot google-generativeai python-dotenv
```

3. Create a `.env` file in the project root directory with your API keys:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

## Usage

1. Start the bot:
```bash
python telegram_bot.py
```

2. Open Telegram and search for your bot using its username

3. Start a conversation with the bot using the `/start` command

4. Send any text message to the bot, and it will respond using the Gemini API

## Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot API token
- `GEMINI_API_KEY`: Your Google Gemini API key

## Error Handling

The bot includes basic error handling and logging:
- Logs are written to console with timestamp and log level
- Application errors are caught and logged before exit

## Contributing

Feel free to submit issues and enhancement requests!

