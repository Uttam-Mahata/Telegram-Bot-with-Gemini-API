"""Configuration module for the learning bot."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/learning_bot")

# Rate limiting settings (messages per user per minute)
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "20"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# AI prompt settings
SYSTEM_PROMPT = """You are an Educational Assistant bot designed to help users learn new subjects.
Your primary goal is to explain concepts clearly, provide useful examples, and guide the learning process.
Be patient, encouraging, and adapt your explanations to the user's level of understanding.
For technical subjects, provide code examples when relevant.
For any question outside the educational realm, kindly guide the conversation back to learning."""

# Feature flags
ENABLE_COURSE_EXPLORATION = os.getenv("ENABLE_COURSE_EXPLORATION", "True").lower() == "true"
ENABLE_CONTENT_GENERATION = os.getenv("ENABLE_CONTENT_GENERATION", "True").lower() == "true"
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "True").lower() == "true"

# Help message
HELP_MESSAGE = """
📚 *Learning Bot Commands* 📚

*Basic Commands:*
/start - Start the bot and get a welcome message
/help - Show this help message
/learn <topic> - Begin learning about a specific topic
/search <term> - Search for learning resources

*Course Commands:*
/courses - List available courses
/subjects <course_id> - List subjects in a course
/chapters <subject_id> - List chapters in a subject
/topics <chapter_id> - List topics in a chapter
/content <topic_id> - Get detailed content for a topic

*Other Commands:*
/feedback <message> - Send feedback about the bot
/stats - View your learning statistics

For any question, just ask me directly and I'll try to help you learn!
"""

# Welcome message
WELCOME_MESSAGE = """
👋 Welcome to the Learning Bot!

I'm your AI-powered educational assistant, designed to help you learn new concepts, explore subjects, and deepen your understanding.

*What I can do:*
• Answer educational questions
• Explain complex concepts
• Guide you through courses
• Provide learning resources

To get started, try asking me something like:
"Explain quantum computing for beginners"
"Help me understand photosynthesis"
"What are the key principles of machine learning?"

Or use /help to see all available commands.

Happy learning! 🎓
"""