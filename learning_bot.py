"""
Telegram Learning Bot - An educational assistant powered by Google Gemini API

This bot helps users learn various subjects, explore course content,
and provides educational answers to their questions.

Usage:
    python learning_bot.py
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys

import signal

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    BotCommand, Message
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler
)

from config import (
    TELEGRAM_BOT_TOKEN, LOG_LEVEL, LOG_FORMAT, WELCOME_MESSAGE,
    HELP_MESSAGE, RATE_LIMIT, ENABLE_COURSE_EXPLORATION
)
from db import initialize_db
from ai_service import AIService
from course_service import CourseService
from user_service import UserService

# Configure logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('learning_bot.log')
    ]
)

logger = logging.getLogger(__name__)

# Initialize services
ai_service = AIService()
user_service = UserService()

class LearningBot:
    """Telegram bot for educational purposes."""
    
    def __init__(self):
        """Initialize the bot with handlers."""
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self._register_handlers()
        
    def _register_handlers(self):
        """Register command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("learn", self.learn))
        self.application.add_handler(CommandHandler("search", self.search))
        self.application.add_handler(CommandHandler("feedback", self.feedback))
        self.application.add_handler(CommandHandler("stats", self.stats))
        
        # Course exploration commands
        if ENABLE_COURSE_EXPLORATION:
            self.application.add_handler(CommandHandler("courses", self.list_courses))
            self.application.add_handler(CommandHandler("subjects", self.list_subjects))
            self.application.add_handler(CommandHandler("chapters", self.list_chapters))
            self.application.add_handler(CommandHandler("topics", self.list_topics))
            self.application.add_handler(CommandHandler("content", self.get_content))
        
        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.button_click))
        
        # Message handler (should be last)
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
        
    async def set_commands(self):
        """Set bot commands menu."""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help information"),
            BotCommand("learn", "Learn about a specific topic"),
            BotCommand("search", "Search for learning resources"),
            BotCommand("courses", "List available courses"),
            BotCommand("feedback", "Send feedback about the bot"),
            BotCommand("stats", "View your learning statistics")
        ]
        await self.application.bot.set_my_commands(commands)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        if not update.effective_user:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
            
        await update.message.reply_text(
            WELCOME_MESSAGE,
            parse_mode="Markdown"
        )
        
        # Log the interaction
        await user_service.update_user_activity(user)
        
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        if not update.effective_user:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
            
        await update.message.reply_text(
            HELP_MESSAGE,
            parse_mode="Markdown"
        )
        
        # Log the interaction
        await user_service.update_user_activity(user)
    
    async def learn(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /learn command."""
        if not update.effective_user or not update.message:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
        
        # Get the topic from the command arguments
        topic = " ".join(context.args) if context.args else ""
        
        if not topic:
            await update.message.reply_text(
                "Please specify a topic to learn about.\n"
                "Example: /learn quantum computing"
            )
            return
            
        # Tell the user we're preparing content
        await update.message.reply_text(f"Preparing learning content about {topic}...")
        
        # Start a learning session
        session = await user_service.start_learning_session(user, topic)
        
        # Generate content
        content = await ai_service.generate_educational_content(topic)
        
        # Format content with a learn more button
        keyboard = [
            [InlineKeyboardButton("Examples", callback_data=f"examples:{topic}")],
            [InlineKeyboardButton("Quiz Me", callback_data=f"quiz:{topic}")],
            [InlineKeyboardButton("Summarize", callback_data=f"summary:{topic}")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📚 *Learning: {topic}*\n\n{content}",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
        # Log the interaction
        await user_service.update_user_activity(user)
        await user_service.save_message_history(user, f"/learn {topic}")
    
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /search command to find learning resources."""
        if not update.effective_user or not update.message:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
        
        # Get the query from the command arguments
        query = " ".join(context.args) if context.args else ""
        
        if not query:
            await update.message.reply_text(
                "Please specify what you'd like to search for.\n"
                "Example: /search machine learning"
            )
            return
            
        # Tell the user we're searching
        await update.message.reply_text(f"Searching for resources about '{query}'...")
        
        # Search for topics in the database
        topics = await CourseService.search_topics(query)
        
        if not topics:
            # If no database results, use AI to suggest learning paths
            suggestions = await ai_service.generate_educational_content(
                f"Suggest a learning path for someone interested in {query}. "
                "Include 3-5 specific topics they should study in sequence."
            )
            
            await update.message.reply_text(
                f"I couldn't find specific courses about '{query}' in my database, "
                f"but I can suggest a learning path:\n\n{suggestions}"
            )
        else:
            # Create a formatted response with the found topics
            response = f"📚 *Found {len(topics)} resources about '{query}'*\n\n"
            
            for i, topic in enumerate(topics[:5], 1):
                response += f"{i}. *{topic['name']}*\n"
                response += f"   From: {topic['course']} > {topic['subject']} > {topic['chapter']}\n"
                response += f"   /content_{topic['id']}\n\n"
            
            if len(topics) > 5:
                response += f"...and {len(topics) - 5} more results.\n"
                
            await update.message.reply_text(response, parse_mode="Markdown")
        
        # Log the interaction
        await user_service.update_user_activity(user)
        await user_service.save_message_history(user, f"/search {query}")
    
    async def feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /feedback command."""
        if not update.effective_user or not update.message:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
        
        # Get the feedback message
        feedback_text = " ".join(context.args) if context.args else ""
        
        if not feedback_text:
            await update.message.reply_text(
                "Please include your feedback after the command.\n"
                "Example: /feedback I really enjoyed learning about quantum physics!"
            )
            return
            
        # Save the feedback
        success = await user_service.save_feedback(user, feedback_text)
        
        if success:
            await update.message.reply_text(
                "Thank you for your feedback! We appreciate your input to help improve the learning experience."
            )
        else:
            await update.message.reply_text(
                "Sorry, there was an error saving your feedback. Please try again later."
            )
        
        # Log the interaction
        await user_service.update_user_activity(user)

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /stats command to show user learning statistics."""
        if not update.effective_user or not update.message:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
        
        # Get user stats
        stats = await user_service.get_user_stats(user)
        
        if not stats:
            await update.message.reply_text("Sorry, I couldn't retrieve your learning statistics. Please try again later.")
            return
            
        # Format time in hours and minutes
        hours, remainder = divmod(stats["total_time"], 3600)
        minutes, _ = divmod(remainder, 60)
        time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Format the response
        response = "📊 *Your Learning Statistics* 📊\n\n"
        response += f"• Learning sessions: {stats['completed_sessions']}/{stats['total_sessions']} completed\n"
        response += f"• Total learning time: {time_str}\n"
        response += f"• Total interactions: {stats['message_count']}\n\n"
        
        if stats["top_topics"]:
            response += "*Your top topics:*\n"
            for topic, count in stats["top_topics"]:
                response += f"• {topic}: {count} sessions\n"
        
        await update.message.reply_text(response, parse_mode="Markdown")
        
        # Log the interaction
        await user_service.update_user_activity(user)

    async def list_courses(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /courses command to list available courses."""
        if not update.effective_user or not update.message:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
        
        # Get courses
        courses = await CourseService.get_courses()
        
        if not courses:
            await update.message.reply_text(
                "No courses are currently available. Check back later for new content!"
            )
            return
            
        # Format the response
        response = "📚 *Available Courses* 📚\n\n"
        
        for i, course in enumerate(courses, 1):
            response += f"{i}. *{course['name']}*\n"
            response += f"   {course['description']}\n"
            response += f"   To view subjects: /subjects {course['id']}\n\n"
            
        await update.message.reply_text(response, parse_mode="Markdown")
        
        # Log the interaction
        await user_service.update_user_activity(user)
        await user_service.save_message_history(user, "/courses")
            
    async def list_subjects(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /subjects command to list subjects for a course."""
        if not update.effective_user or not update.message:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
        
        # Get the course ID from the command arguments
        course_id = context.args[0] if context.args else ""
        
        if not course_id:
            await update.message.reply_text(
                "Please specify a course ID.\n"
                "Example: /subjects 60a1b2c3d4e5f6g7h8i9j0k"
            )
            return
            
        # Get subjects
        subjects = await CourseService.get_subjects(course_id)
        
        if not subjects:
            await update.message.reply_text(
                "No subjects found for this course. It might not exist or have no content yet."
            )
            return
            
        # Format the response
        response = "📖 *Course Subjects* 📖\n\n"
        
        for i, subject in enumerate(subjects, 1):
            response += f"{i}. *{subject['name']}*\n"
            response += f"   {subject['description']}\n"
            response += f"   To view chapters: /chapters {subject['id']}\n\n"
            
        await update.message.reply_text(response, parse_mode="Markdown")
        
        # Log the interaction
        await user_service.update_user_activity(user)
        await user_service.save_message_history(user, f"/subjects {course_id}")
            
    async def list_chapters(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /chapters command to list chapters for a subject."""
        if not update.effective_user or not update.message:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
        
        # Get the subject ID from the command arguments
        subject_id = context.args[0] if context.args else ""
        
        if not subject_id:
            await update.message.reply_text(
                "Please specify a subject ID.\n"
                "Example: /chapters 60a1b2c3d4e5f6g7h8i9j0k"
            )
            return
            
        # Get chapters
        chapters = await CourseService.get_chapters(subject_id)
        
        if not chapters:
            await update.message.reply_text(
                "No chapters found for this subject. It might not exist or have no content yet."
            )
            return
            
        # Format the response
        response = "📝 *Subject Chapters* 📝\n\n"
        
        for i, chapter in enumerate(chapters, 1):
            response += f"{i}. *{chapter['name']}*\n"
            response += f"   {chapter['description']}\n"
            response += f"   To view topics: /topics {chapter['id']}\n\n"
            
        await update.message.reply_text(response, parse_mode="Markdown")
        
        # Log the interaction
        await user_service.update_user_activity(user)
        await user_service.save_message_history(user, f"/chapters {subject_id}")
    
    async def list_topics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /topics command to list topics for a chapter."""
        if not update.effective_user or not update.message:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
        
        # Get the chapter ID from the command arguments
        chapter_id = context.args[0] if context.args else ""
        
        if not chapter_id:
            await update.message.reply_text(
                "Please specify a chapter ID.\n"
                "Example: /topics 60a1b2c3d4e5f6g7h8i9j0k"
            )
            return
            
        # Get topics
        topics = await CourseService.get_topics(chapter_id)
        
        if not topics:
            await update.message.reply_text(
                "No topics found for this chapter. It might not exist or have no content yet."
            )
            return
            
        # Format the response
        response = "🔍 *Chapter Topics* 🔍\n\n"
        
        for i, topic in enumerate(topics, 1):
            response += f"{i}. *{topic['name']}*\n"
            response += f"   {topic['description']}\n"
            response += f"   To view content: /content {topic['id']}\n\n"
            
        await update.message.reply_text(response, parse_mode="Markdown")
        
        # Log the interaction
        await user_service.update_user_activity(user)
        await user_service.save_message_history(user, f"/topics {chapter_id}")
    
    async def get_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /content command to get content for a topic."""
        if not update.effective_user or not update.message:
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
        
        # Get the topic ID from the command arguments
        topic_id = context.args[0] if context.args else ""
        
        # Also handle /content_ID format from search results
        if not topic_id and update.message.text.startswith("/content_"):
            topic_id = update.message.text.split("/content_")[1]
        
        if not topic_id:
            await update.message.reply_text(
                "Please specify a topic ID.\n"
                "Example: /content 60a1b2c3d4e5f6g7h8i9j0k"
            )
            return
            
        # Get content
        content_text = await CourseService.get_content(topic_id)
        
        if not content_text:
            await update.message.reply_text(
                "No content found for this topic. It might not exist or have no content yet."
            )
            return
            
        # Send the content in manageable chunks due to Telegram message length limits
        MAX_LENGTH = 4000
        message_parts = []
        
        # Split content into parts if needed
        for i in range(0, len(content_text), MAX_LENGTH):
            message_parts.append(content_text[i:i + MAX_LENGTH])
            
        # Send first part with topic header
        await update.message.reply_text(f"📘 *Learning Content*\n\n{message_parts[0]}", parse_mode="Markdown")
        
        # Send any additional parts
        for part in message_parts[1:]:
            await update.message.reply_text(part, parse_mode="Markdown")
        
        # Log the interaction
        await user_service.update_user_activity(user)
        await user_service.save_message_history(user, f"/content {topic_id}")
    
    async def button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboard buttons."""
        query = update.callback_query
        await query.answer()  # Answer the callback query to stop the loading icon
        
        if not query.from_user:
            return
            
        user = await user_service.get_or_create_user(query.from_user)
        if not user:
            await query.edit_message_text("Error initializing user. Please try again.")
            return
            
        # Parse the callback data
        try:
            action, topic = query.data.split(":", 1)
        except ValueError:
            await query.edit_message_text("Invalid button data. Please try again.")
            return
            
        # Process different button actions
        if action == "examples":
            content = await ai_service.generate_educational_content(topic, "examples")
            await query.edit_message_text(
                f"📚 *Examples: {topic}*\n\n{content}",
                parse_mode="Markdown",
                reply_markup=query.message.reply_markup
            )
        elif action == "quiz":
            content = await ai_service.generate_educational_content(topic, "quiz")
            await query.edit_message_text(
                f"🧠 *Quiz: {topic}*\n\n{content}",
                parse_mode="Markdown",
                reply_markup=query.message.reply_markup
            )
        elif action == "summary":
            content = await ai_service.generate_educational_content(topic, "summary")
            await query.edit_message_text(
                f"📝 *Summary: {topic}*\n\n{content}",
                parse_mode="Markdown",
                reply_markup=query.message.reply_markup
            )
        else:
            await query.edit_message_text(
                f"Unknown action: {action}",
                reply_markup=query.message.reply_markup
            )
            
        # Log the interaction
        await user_service.update_user_activity(user)
        await user_service.save_message_history(user, f"Button: {action}:{topic}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle regular text messages."""
        if not update.effective_user or not update.message or not update.message.text:
            return
            
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Apply rate limiting
        if not user_service.check_rate_limit(user_id, RATE_LIMIT):
            await update.message.reply_text(
                "You're sending messages too quickly. Please wait a moment before sending more."
            )
            return
            
        user = await user_service.get_or_create_user(update.effective_user)
        if not user:
            await update.message.reply_text("Error initializing user. Please try again.")
            return
            
        # Save user message to history
        await user_service.save_message_history(user, message_text)
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Get AI response
            response = await ai_service.get_response(message_text)
            
            # Send the response
            await update.message.reply_text(response, parse_mode="Markdown")
            
            # Save bot response to history
            await user_service.save_message_history(user, response, is_bot=True)
            
        except Exception as e:
            logger.error(f"Error in handle_message: {e}", exc_info=True)
            await update.message.reply_text(
                "I'm sorry, I encountered an error while processing your request. Please try again later."
            )
            
        # Log the interaction
        await user_service.update_user_activity(user)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the telegram-python-bot framework."""
        logger.error("Exception while handling an update:", exc_info=context.error)
        
        # Get the error message
        error_message = str(context.error)
        
        # Extract the chat ID if possible
        chat_id = None
        if update and isinstance(update, Update) and update.effective_chat:
            chat_id = update.effective_chat.id
            
        if chat_id:
            # Send a friendly error message to the user
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Sorry, I encountered an unexpected error while processing your request. "
                         "The error has been logged and will be addressed soon."
                )
            except Exception as e:
                logger.error(f"Error sending error message: {e}", exc_info=True)
                
    async def run(self) -> None:
        """Start the bot."""
        # Initialize database connection
        try:
            initialize_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize database: {e}", exc_info=True)
            sys.exit(1)
            
        # Set up bot commands
        await self.set_commands()
        
        # Start the bot - FIX: Only start polling once
        await self.application.initialize()
        await self.application.start()
        
        # Start polling with configured parameters
        await self.application.updater.start_polling(
            poll_interval=0.0,
            timeout=10,
            bootstrap_retries=-1,
            read_timeout=2
        )
        
        logger.info("Bot started successfully")
        
        # Keep the application running until it's stopped
        stop_signal = asyncio.Future()
        
        # Add a handler for keyboard interrupt
        try:
            await stop_signal
        except asyncio.CancelledError:
            pass
        finally:
            # Properly shut down the bot
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Bot has been shut down")


async def main() -> None:
    """Main function to start the bot."""
    bot = LearningBot()
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for signal_name in ('SIGINT', 'SIGTERM'):
        try:
            loop.add_signal_handler(
                getattr(signal, signal_name),
                lambda: asyncio.create_task(shutdown(bot))
            )
        except (NotImplementedError, ImportError):
            # Windows doesn't support SIGINT/SIGTERM
            pass
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
        await shutdown(bot)


async def shutdown(bot):
    """Shutdown the bot gracefully."""
    logger.info("Received shutdown signal. Closing connections...")
    try:
        await bot.application.updater.stop()
        await bot.application.stop()
        await bot.application.shutdown()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


if __name__ == '__main__':
    # Import signal here to avoid issues if not available
    try:
        import signal
    except ImportError:
        pass
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)