"""Service for managing user data and interactions."""
import logging
import time
from typing import Dict, Optional, List
from datetime import datetime
from db import User, LearningSession, MessageHistory, Feedback

logger = logging.getLogger(__name__)

class UserService:
    """Service for managing user-related functionality."""
    
    _rate_limits: Dict[int, List[float]] = {}  # Store rate limit info by user_id
    
    @staticmethod
    async def get_or_create_user(user_data):
        """Get existing user or create a new one."""
        try:
            user = User.objects(telegram_id=str(user_data.id)).first()
            if not user:
                user = User(
                    telegram_id=str(user_data.id),
                    username=user_data.username,
                    first_name=user_data.first_name,
                    last_name=user_data.last_name
                )
                user.save()
                logger.info(f"Created new user: {user.telegram_id}")
            return user
        except Exception as e:
            logger.error(f"Error getting/creating user: {e}", exc_info=True)
            return None
            
    @staticmethod
    async def update_user_activity(user):
        """Update user's last active time and message count."""
        try:
            user.last_active = datetime.utcnow()
            user.message_count += 1
            user.save()
        except Exception as e:
            logger.error(f"Error updating user activity: {e}", exc_info=True)
            
    @staticmethod
    async def save_message_history(user, message_text, is_bot=False):
        """Save message to history."""
        try:
            message = MessageHistory(
                user=user,
                message_text=message_text,
                is_bot=is_bot
            )
            message.save()
        except Exception as e:
            logger.error(f"Error saving message history: {e}", exc_info=True)
            
    @staticmethod
    async def save_feedback(user, feedback_text):
        """Save user feedback."""
        try:
            feedback = Feedback(
                user=user,
                message=feedback_text
            )
            feedback.save()
            return True
        except Exception as e:
            logger.error(f"Error saving feedback: {e}", exc_info=True)
            return False
            
    @staticmethod
    async def start_learning_session(user, topic):
        """Start a new learning session."""
        try:
            session = LearningSession(
                user=user,
                topic=topic
            )
            session.save()
            return session
        except Exception as e:
            logger.error(f"Error starting learning session: {e}", exc_info=True)
            return None
            
    @staticmethod
    async def end_learning_session(session_id):
        """End an existing learning session."""
        try:
            session = LearningSession.objects(id=session_id).first()
            if session and not session.completed:
                session.end_time = datetime.utcnow()
                session.duration = (session.end_time - session.start_time).seconds
                session.completed = True
                session.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Error ending learning session: {e}", exc_info=True)
            return False
            
    @staticmethod
    async def get_user_stats(user):
        """Get learning statistics for a user."""
        try:
            total_sessions = LearningSession.objects(user=user).count()
            completed_sessions = LearningSession.objects(user=user, completed=True).count()
            total_learning_time = 0
            
            for session in LearningSession.objects(user=user, completed=True):
                total_learning_time += session.duration or 0
                
            # Get most studied topics
            topic_count = {}
            for session in LearningSession.objects(user=user):
                topic = session.topic
                topic_count[topic] = topic_count.get(topic, 0) + 1
                
            sorted_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)
            top_topics = sorted_topics[:5]  # Top 5 topics
            
            return {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "total_time": total_learning_time,
                "top_topics": top_topics,
                "message_count": user.message_count
            }
        except Exception as e:
            logger.error(f"Error retrieving user stats: {e}", exc_info=True)
            return None
    
    @classmethod
    def check_rate_limit(cls, user_id: int, limit: int, time_window: int = 60) -> bool:
        """
        Check if a user has exceeded their rate limit.
        
        Args:
            user_id: The user's Telegram ID
            limit: Maximum number of messages allowed in the time window
            time_window: Time window in seconds (default: 60 seconds)
            
        Returns:
            bool: True if user is within rate limit, False if exceeded
        """
        current_time = time.time()
        
        # Initialize if user not in rate limits dict
        if user_id not in cls._rate_limits:
            cls._rate_limits[user_id] = []
            
        # Get user's message timestamps
        timestamps = cls._rate_limits[user_id]
        
        # Remove timestamps outside the time window
        timestamps = [ts for ts in timestamps if current_time - ts < time_window]
        
        # Update timestamps
        cls._rate_limits[user_id] = timestamps
        
        # Check if user exceeded rate limit
        if len(timestamps) >= limit:
            return False
            
        # Add current timestamp
        cls._rate_limits[user_id].append(current_time)
        return True