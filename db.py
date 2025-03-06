"""Database module for the learning bot."""
import logging
from datetime import datetime
from mongoengine import (
    connect, Document, StringField, DateTimeField, 
    ReferenceField, IntField, BooleanField, ListField,
    DictField
)
from config import MONGODB_URI

logger = logging.getLogger(__name__)

def initialize_db():
    """Initialize database connection."""
    try:
        connect(host=MONGODB_URI)
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

# User model for tracking interactions
class User(Document):
    telegram_id = StringField(required=True, unique=True)
    username = StringField()
    first_name = StringField()
    last_name = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    last_active = DateTimeField(default=datetime.utcnow)
    message_count = IntField(default=0)
    is_blocked = BooleanField(default=False)
    preferences = DictField(default={})
    learning_history = ListField(default=[])
    
    meta = {'collection': 'users'}

# Learning Session model for tracking learning activities
class LearningSession(Document):
    user = ReferenceField(User, required=True)
    topic = StringField(required=True)
    start_time = DateTimeField(default=datetime.utcnow)
    end_time = DateTimeField()
    duration = IntField()  # Duration in seconds
    completed = BooleanField(default=False)
    interactions = IntField(default=0)
    
    meta = {'collection': 'learning_sessions'}

# Feedback model
class Feedback(Document):
    user = ReferenceField(User, required=True)
    message = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'feedback'}

# Message History model
class MessageHistory(Document):
    user = ReferenceField(User, required=True)
    message_text = StringField(required=True)
    is_bot = BooleanField(default=False)
    timestamp = DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'message_history'}

# Course models (imported from your course generation system)
class Course(Document):
    name = StringField(required=True)
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'courses'}

class Subject(Document):
    name = StringField(required=True)
    course = ReferenceField('Course', required=True)
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'subjects'}

class Chapter(Document):
    name = StringField(required=True)
    subject = ReferenceField('Subject', required=True)
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'chapters'}

class Topic(Document):
    name = StringField(required=True)
    chapter = ReferenceField('Chapter', required=True)
    description = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'topics'}

class Content(Document):
    topic = ReferenceField('Topic', required=True)
    text = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'contents'}