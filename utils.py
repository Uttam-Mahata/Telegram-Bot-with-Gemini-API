"""Utility functions for the learning bot."""
import re
import logging
from typing import Optional
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

def sanitize_markdown(text: str) -> str:
    """
    Sanitize text for Telegram's Markdown parser.
    
    Escapes Markdown special characters that might cause parsing issues.
    """
    if not text:
        return ""
    
    # Characters that need to be escaped in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Escape by adding a \ before each special character
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    
    return text

async def safe_send_message(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    text: str,
    parse_mode: Optional[str] = None,
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> bool:
    """
    Send a message with fallback options if formatting fails.
    
    Args:
        update: The update object
        context: The context object
        text: The message text to send
        parse_mode: Optional parsing mode (Markdown, MarkdownV2, HTML)
        reply_markup: Optional inline keyboard markup
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    if not update.effective_chat:
        logger.error("No effective chat found in update")
        return False
        
    # Strategy 1: Try with the requested parse mode
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        return True
    except BadRequest as e:
        logger.warning(f"Failed to send message with {parse_mode}: {e}")
        
        # Strategy 2: If Markdown failed, try with MarkdownV2 and sanitized text
        if parse_mode == "Markdown":
            try:
                sanitized_text = sanitize_markdown(text)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=sanitized_text,
                    parse_mode="MarkdownV2",
                    reply_markup=reply_markup
                )
                return True
            except BadRequest as e:
                logger.warning(f"Failed to send sanitized message with MarkdownV2: {e}")
        
        # Strategy 3: Fall back to plain text without formatting
        try:
            # Strip markdown characters that might be problematic
            plain_text = re.sub(r'[*_`[\]()]', '', text)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=plain_text,
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send plain text message: {e}")
            return False

def split_message(text: str, max_length: int = 4000) -> list:
    """Split a message into chunks that fit within Telegram's limits."""
    if len(text) <= max_length:
        return [text]
        
    # Try to split at paragraph breaks first
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed the limit, start a new chunk
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                # If a single paragraph is too long, split it by sentences
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = sentence + ". "
                        else:
                            # If a single sentence is too long, split by character
                            sub_chunks = [
                                paragraph[i:i+max_length] 
                                for i in range(0, len(paragraph), max_length)
                            ]
                            chunks.extend(sub_chunks)
                    else:
                        current_chunk += sentence + ". "
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk if it exists
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks