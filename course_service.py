"""Service for interacting with the course database."""
import logging
from typing import List, Dict, Any, Optional
from mongoengine.errors import DoesNotExist
from db import Course, Subject, Chapter, Topic, Content

logger = logging.getLogger(__name__)

class CourseService:
    """Service for accessing and managing course data."""
    
    @staticmethod
    async def get_courses() -> List[Dict[str, Any]]:
        """Get all courses."""
        try:
            courses = Course.objects.order_by('-created_at')
            return [
                {
                    'id': str(course.id),
                    'name': course.name,
                    'description': course.description
                }
                for course in courses
            ]
        except Exception as e:
            logger.error(f"Error fetching courses: {e}", exc_info=True)
            return []

    @staticmethod
    async def get_subjects(course_id: str) -> List[Dict[str, Any]]:
        """Get subjects for a specific course."""
        try:
            course = Course.objects(id=course_id).first()
            if not course:
                return []
                
            subjects = Subject.objects(course=course)
            return [
                {
                    'id': str(subject.id),
                    'name': subject.name,
                    'description': subject.description
                }
                for subject in subjects
            ]
        except Exception as e:
            logger.error(f"Error fetching subjects: {e}", exc_info=True)
            return []

    @staticmethod
    async def get_chapters(subject_id: str) -> List[Dict[str, Any]]:
        """Get chapters for a specific subject."""
        try:
            subject = Subject.objects(id=subject_id).first()
            if not subject:
                return []
                
            chapters = Chapter.objects(subject=subject)
            return [
                {
                    'id': str(chapter.id),
                    'name': chapter.name,
                    'description': chapter.description
                }
                for chapter in chapters
            ]
        except Exception as e:
            logger.error(f"Error fetching chapters: {e}", exc_info=True)
            return []

    @staticmethod
    async def get_topics(chapter_id: str) -> List[Dict[str, Any]]:
        """Get topics for a specific chapter."""
        try:
            chapter = Chapter.objects(id=chapter_id).first()
            if not chapter:
                return []
                
            topics = Topic.objects(chapter=chapter)
            return [
                {
                    'id': str(topic.id),
                    'name': topic.name,
                    'description': topic.description
                }
                for topic in topics
            ]
        except Exception as e:
            logger.error(f"Error fetching topics: {e}", exc_info=True)
            return []

    @staticmethod
    async def get_content(topic_id: str) -> Optional[str]:
        """Get content for a specific topic."""
        try:
            topic = Topic.objects(id=topic_id).first()
            if not topic:
                return None
                
            content = Content.objects(topic=topic).first()
            if not content:
                return None
                
            return content.text
        except Exception as e:
            logger.error(f"Error fetching content: {e}", exc_info=True)
            return None
            
    @staticmethod
    async def search_topics(query: str) -> List[Dict[str, Any]]:
        """Search for topics matching the query."""
        try:
            # Simple text search implementation
            topics = Topic.objects(name__icontains=query)[:10]  # Limit to 10 results
            results = []
            
            for topic in topics:
                try:
                    chapter = topic.chapter
                    subject = chapter.subject
                    course = subject.course
                    
                    results.append({
                        'id': str(topic.id),
                        'name': topic.name,
                        'description': topic.description,
                        'chapter': chapter.name,
                        'subject': subject.name,
                        'course': course.name
                    })
                except DoesNotExist:
                    # Skip topics with missing references
                    pass
                    
            return results
        except Exception as e:
            logger.error(f"Error searching topics: {e}", exc_info=True)
            return []