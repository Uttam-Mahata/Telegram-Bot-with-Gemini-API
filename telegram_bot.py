import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Initialize Google Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chat = client.chats.create(model="gemini-1.5-flash")

# Define command handler for /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hi! I am your bot. Send me a message and I will respond using Google Gemini API.')

# Define message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    response = get_gemini_response(user_message)
    await update.message.reply_text(response)

# Function to call Google Gemini API
def get_gemini_response(message: str) -> str:
    response = chat.send_message_stream(message)
    response_text = ""
    for chunk in response:
        response_text += chunk.text
    return response_text

def run_bot():
    # Create the Application and pass it your bot's token
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Register command handler
    application.add_handler(CommandHandler("start", start))

    # Register message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot using run_polling() method
    print("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        run_bot()
    except Exception as e:
        print(f"Error running bot: {e}")
        sys.exit(1)