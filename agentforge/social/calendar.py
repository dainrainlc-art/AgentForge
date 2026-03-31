"""
Content Calendar - Plan and organize social media content
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum
from uuid import uuid4

from agentforge.social.content_adapter import Platform
from agentforge.social.scheduler import ScheduledPost


class CalendarEventType(str, Enum):
    POST = "post"
    CAMPAIGN = "campaign"
    THEME = "theme"
    HOLIDAY = "holiday"
    EVENT = "event"


class ContentStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"


class CalendarEvent(BaseModel):
    """Calendar event model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: Optional[str] = None
    event_type: CalendarEventType = CalendarEventType.POST
    platforms: List[Platform] = Field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: ContentStatus = ContentStatus.DRAFT
    content: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    media_urls: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    author: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentTheme(BaseModel):
    """Content theme for organizing posts"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    color: str = "#3B82F6"
    platforms: List[Platform] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    posting_schedule: Dict[str, List[int]] = Field(default_factory=dict)
    active: bool = True


class ContentCalendar:
    """Content calendar management"""
    
    def __init__(self):
        self._events: Dict[str, CalendarEvent] = {}
        self._themes: Dict[str, ContentTheme] = {}
        self._initialize_default_themes()
    
    def _initialize_default_themes(self) -> None:
        """Initialize default content themes"""
        
        default_themes = [
            ContentTheme(
                id="product_updates",
                name="Product Updates",
                description="Announcements about new features and updates",
                color="#10B981",
                hashtags=["#NewFeature", "#Update", "#ProductNews"]
            ),
            ContentTheme(
                id="educational",
                name="Educational Content",
                description="Tips, tutorials, and how-to guides",
                color="#6366F1",
                hashtags=["#Tips", "#Tutorial", "#HowTo"]
            ),
            ContentTheme(
                id="engagement",
                name="Engagement Posts",
                description="Questions, polls, and interactive content",
                color="#F59E0B",
                hashtags=["#Question", "#Poll", "#Discussion"]
            ),
            ContentTheme(
                id="promotional",
                name="Promotional",
                description="Sales, offers, and promotional content",
                color="#EF4444",
                hashtags=["#Offer", "#Deal", "#Sale"]
            ),
            ContentTheme(
                id="behind_scenes",
                name="Behind the Scenes",
                description="Company culture and team content",
                color="#8B5CF6",
                hashtags=["#BehindTheScenes", "#Team", "#Culture"]
            ),
        ]
        
        for theme in default_themes:
            self._themes[theme.id] = theme
        
        logger.info(f"Initialized {len(default_themes)} default themes")
    
    def create_event(
        self,
        title: str,
        event_type: CalendarEventType = CalendarEventType.POST,
        platforms: Optional[List[Platform]] = None,
        scheduled_time: Optional[datetime] = None,
        content: Optional[str] = None,
        **kwargs
    ) -> CalendarEvent:
        """Create a new calendar event"""
        
        event = CalendarEvent(
            title=title,
            event_type=event_type,
            platforms=platforms or [],
            scheduled_time=scheduled_time,
            content=content,
            **kwargs
        )
        
        self._events[event.id] = event
        
        logger.info(f"Created calendar event: {event.title}")
        
        return event
    
    def update_event(
        self,
        event_id: str,
        **kwargs
    ) -> Optional[CalendarEvent]:
        """Update an existing event"""
        
        if event_id not in self._events:
            return None
        
        event = self._events[event_id]
        
        for key, value in kwargs.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        event.updated_at = datetime.now()
        
        logger.info(f"Updated event: {event.title}")
        
        return event
    
    def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        
        if event_id not in self._events:
            return False
        
        del self._events[event_id]
        
        logger.info(f"Deleted event: {event_id}")
        
        return True
    
    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """Get an event by ID"""
        return self._events.get(event_id)
    
    def get_events_by_date(
        self,
        date: datetime,
        platform: Optional[Platform] = None
    ) -> List[CalendarEvent]:
        """Get events for a specific date"""
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        events = [
            e for e in self._events.values()
            if e.scheduled_time
            and start_of_day <= e.scheduled_time < end_of_day
        ]
        
        if platform:
            events = [e for e in events if platform in e.platforms]
        
        return sorted(events, key=lambda e: e.scheduled_time or datetime.min)
    
    def get_events_by_range(
        self,
        start_date: datetime,
        end_date: datetime,
        platform: Optional[Platform] = None
    ) -> List[CalendarEvent]:
        """Get events within a date range"""
        
        events = [
            e for e in self._events.values()
            if e.scheduled_time
            and start_date <= e.scheduled_time < end_date
        ]
        
        if platform:
            events = [e for e in events if platform in e.platforms]
        
        return sorted(events, key=lambda e: e.scheduled_time or datetime.min)
    
    def get_events_by_status(
        self,
        status: ContentStatus
    ) -> List[CalendarEvent]:
        """Get events by status"""
        
        return [e for e in self._events.values() if e.status == status]
    
    def get_events_by_theme(
        self,
        theme_id: str
    ) -> List[CalendarEvent]:
        """Get events by theme tag"""
        
        return [e for e in self._events.values() if theme_id in e.tags]
    
    def get_upcoming_events(
        self,
        days: int = 7,
        platform: Optional[Platform] = None
    ) -> List[CalendarEvent]:
        """Get upcoming events"""
        
        now = datetime.now()
        end_date = now + timedelta(days=days)
        
        return self.get_events_by_range(now, end_date, platform)
    
    def create_theme(
        self,
        name: str,
        description: str,
        color: str = "#3B82F6",
        hashtags: Optional[List[str]] = None
    ) -> ContentTheme:
        """Create a new content theme"""
        
        theme = ContentTheme(
            name=name,
            description=description,
            color=color,
            hashtags=hashtags or []
        )
        
        self._themes[theme.id] = theme
        
        logger.info(f"Created theme: {name}")
        
        return theme
    
    def get_theme(self, theme_id: str) -> Optional[ContentTheme]:
        """Get a theme by ID"""
        return self._themes.get(theme_id)
    
    def list_themes(self, active_only: bool = True) -> List[ContentTheme]:
        """List all themes"""
        
        themes = list(self._themes.values())
        
        if active_only:
            themes = [t for t in themes if t.active]
        
        return themes
    
    def get_calendar_overview(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get calendar overview for a date range"""
        
        events = self.get_events_by_range(start_date, end_date)
        
        daily_counts = {}
        current = start_date
        
        while current < end_date:
            date_str = current.strftime("%Y-%m-%d")
            daily_counts[date_str] = len([
                e for e in events
                if e.scheduled_time and e.scheduled_time.date() == current.date()
            ])
            current += timedelta(days=1)
        
        platform_counts = {}
        for platform in Platform:
            platform_counts[platform.value] = len([
                e for e in events if platform in e.platforms
            ])
        
        status_counts = {}
        for status in ContentStatus:
            status_counts[status.value] = len([
                e for e in events if e.status == status
            ])
        
        return {
            "total_events": len(events),
            "daily_counts": daily_counts,
            "platform_distribution": platform_counts,
            "status_distribution": status_counts,
            "themes": [t.model_dump() for t in self.list_themes()],
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    def suggest_content_slots(
        self,
        platform: Platform,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Suggest optimal content slots"""
        
        now = datetime.now()
        suggestions = []
        
        existing_events = self.get_events_by_range(
            now,
            now + timedelta(days=days)
        )
        
        occupied_slots = set()
        for event in existing_events:
            if event.scheduled_time and platform in event.platforms:
                slot_key = event.scheduled_time.strftime("%Y-%m-%d %H")
                occupied_slots.add(slot_key)
        
        optimal_hours = {
            Platform.TWITTER: [9, 12, 17, 18],
            Platform.LINKEDIN: [7, 8, 12, 17],
            Platform.INSTAGRAM: [11, 13, 19, 21],
            Platform.FACEBOOK: [9, 13, 16, 19],
            Platform.YOUTUBE: [14, 15, 16],
            Platform.TIKTOK: [19, 20, 21],
        }
        
        hours = optimal_hours.get(platform, [9, 12, 17])
        
        for day_offset in range(days):
            for hour in hours:
                slot_time = now.replace(
                    hour=hour,
                    minute=0,
                    second=0,
                    microsecond=0
                ) + timedelta(days=day_offset)
                
                slot_key = slot_time.strftime("%Y-%m-%d %H")
                
                if slot_key not in occupied_slots and slot_time > now:
                    suggestions.append({
                        "datetime": slot_time.isoformat(),
                        "hour": hour,
                        "day_of_week": slot_time.strftime("%A"),
                        "available": True
                    })
        
        return suggestions[:10]
    
    def export_calendar(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> str:
        """Export calendar data"""
        
        events = self.get_events_by_range(start_date, end_date)
        
        if format == "json":
            import json
            return json.dumps({
                "events": [e.model_dump() for e in events],
                "exported_at": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }, default=str, indent=2)
        
        return ""


content_calendar = ContentCalendar()
