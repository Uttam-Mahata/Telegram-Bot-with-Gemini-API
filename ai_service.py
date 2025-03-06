"""AI service for generating responses using the Gemini API."""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with the Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini client."""
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL
        self._initialize_chat()
        
    def _initialize_chat(self):
        """Initialize a chat session with the system prompt."""
        self.chat = self.client.chats.create(model=self.model_name)
        # Set initial system prompt for educational context
        self.chat.send_message(SYSTEM_PROMPT)
    
    def reset_chat(self):
        """Reset the chat session."""
        self._initialize_chat()
        
    async def get_response(self, message: str) -> str:
        """Get an AI response for a user message."""
        try:
            # Run the API call in a separate thread to not block the event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.chat.send_message_stream(message)
            )
            
            # Collect response chunks
            response_text = ""
            async for chunk in self._async_generator(response):
                response_text += chunk.text
            
            return response_text
        
        except Exception as e:
            logger.error(f"Error getting AI response: {e}", exc_info=True)
            return "I'm having trouble connecting to my knowledge source. Please try again in a moment."

    async def _async_generator(self, generator):
        """Convert a synchronous generator to an async one."""
        for item in generator:
            yield item
    
    async def generate_educational_content(self, topic: str, format_type: str = "explanation") -> str:
        """Generate educational content on a specific topic."""
        formats = {
            "explanation": f"Provide a clear explanation of {topic} suitable for learning.",
            "summary": f"Provide a concise summary of the key points about {topic}.",
            "examples": f"Provide practical examples that illustrate {topic}.",
            "quiz": f"Create a short quiz with answers about {topic}.",
        }
        
        prompt = formats.get(format_type, formats["explanation"])
        
        try:
            response = await self.get_response(prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating educational content: {e}", exc_info=True)
            return f"I couldn't generate content about {topic} at the moment. Please try again later."