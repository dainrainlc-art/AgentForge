"""
Calendar Plugin - 日历和日程管理插件
Provides calendar management and event scheduling
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from loguru import logger

from .plugin_system import Plugin, PluginMetadata


@dataclass
class CalendarEvent:
    """Calendar event data class"""
    id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    attendees: List[str] = None
    reminder_minutes: int = 15
    is_all_day: bool = False
    recurrence: Optional[str] = None  # daily, weekly, monthly
    color: str = "#0ea5e9"
    
    def __post_init__(self):
        if self.attendees is None:
            self.attendees = []


class CalendarPlugin(Plugin):
    """Calendar management plugin with event scheduling"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._events: Dict[str, CalendarEvent] = {}
        self._storage_file = self.get_config("storage_file", ".calendar_events.json")
        self._load_events()
        
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="calendar",
            version="1.0.0",
            description="日历和日程管理插件",
            author="AgentForge",
            tags=["calendar", "schedule", "event", "productivity"],
            permissions=["file_read", "file_write"]
        )
    
    @property
    def config_schema(self) -> Dict[str, Any]:
        return {
            "storage_file": {
                "type": "string",
                "description": "事件存储文件路径",
                "default": ".calendar_events.json"
            },
            "default_reminder": {
                "type": "integer",
                "description": "默认提醒时间（分钟）",
                "default": 15
            },
            "timezone": {
                "type": "string",
                "description": "时区",
                "default": "Asia/Shanghai"
            }
        }
    
    def _load_events(self):
        """Load events from storage"""
        try:
            import os
            if os.path.exists(self._storage_file):
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for event_id, event_data in data.items():
                        event_data['start_time'] = datetime.fromisoformat(event_data['start_time'])
                        event_data['end_time'] = datetime.fromisoformat(event_data['end_time'])
                        self._events[event_id] = CalendarEvent(**event_data)
                logger.info(f"Loaded {len(self._events)} calendar events")
        except Exception as e:
            logger.error(f"Failed to load calendar events: {e}")
    
    def _save_events(self):
        """Save events to storage"""
        try:
            data = {}
            for event_id, event in self._events.items():
                event_dict = asdict(event)
                event_dict['start_time'] = event.start_time.isoformat()
                event_dict['end_time'] = event.end_time.isoformat()
                data[event_id] = event_dict
            
            with open(self._storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save calendar events: {e}")
    
    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: Optional[str] = None,
        attendees: List[str] = None,
        reminder_minutes: int = None,
        is_all_day: bool = False
    ) -> CalendarEvent:
        """Create a new calendar event"""
        import uuid
        
        event_id = str(uuid.uuid4())[:8]
        
        if reminder_minutes is None:
            reminder_minutes = self.get_config("default_reminder", 15)
        
        event = CalendarEvent(
            id=event_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
            attendees=attendees or [],
            reminder_minutes=reminder_minutes,
            is_all_day=is_all_day
        )
        
        self._events[event_id] = event
        self._save_events()
        
        logger.info(f"Created calendar event: {title} ({event_id})")
        return event
    
    async def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """Get event by ID"""
        return self._events.get(event_id)
    
    async def update_event(self, event_id: str, **kwargs) -> Optional[CalendarEvent]:
        """Update an existing event"""
        if event_id not in self._events:
            return None
        
        event = self._events[event_id]
        
        for key, value in kwargs.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        self._save_events()
        logger.info(f"Updated calendar event: {event.title} ({event_id})")
        return event
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        if event_id in self._events:
            event = self._events.pop(event_id)
            self._save_events()
            logger.info(f"Deleted calendar event: {event.title} ({event_id})")
            return True
        return False
    
    async def get_events(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> List[CalendarEvent]:
        """Get events within date range"""
        events = list(self._events.values())
        
        if start_date:
            events = [e for e in events if e.end_time >= start_date]
        
        if end_date:
            events = [e for e in events if e.start_time <= end_date]
        
        # Sort by start time
        events.sort(key=lambda e: e.start_time)
        
        return events[:limit]
    
    async def get_today_events(self) -> List[CalendarEvent]:
        """Get today's events"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return await self.get_events(today, tomorrow)
    
    async def get_upcoming_events(self, days: int = 7) -> List[CalendarEvent]:
        """Get upcoming events for next N days"""
        now = datetime.now()
        future = now + timedelta(days=days)
        return await self.get_events(now, future)
    
    async def check_conflicts(
        self,
        start_time: datetime,
        end_time: datetime,
        exclude_event_id: str = None
    ) -> List[CalendarEvent]:
        """Check for scheduling conflicts"""
        conflicts = []
        
        for event_id, event in self._events.items():
            if exclude_event_id and event_id == exclude_event_id:
                continue
            
            # Check overlap
            if (start_time < event.end_time and end_time > event.start_time):
                conflicts.append(event)
        
        return conflicts
    
    async def get_reminders(self, minutes_ahead: int = 15) -> List[CalendarEvent]:
        """Get events that need reminders"""
        now = datetime.now()
        reminder_time = now + timedelta(minutes=minutes_ahead)
        
        reminders = []
        for event in self._events.values():
            reminder_at = event.start_time - timedelta(minutes=event.reminder_minutes)
            if now <= reminder_at <= reminder_time:
                reminders.append(event)
        
        return reminders
    
    async def export_to_ics(self, events: List[CalendarEvent] = None) -> str:
        """Export events to iCalendar format"""
        if events is None:
            events = list(self._events.values())
        
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//AgentForge//Calendar Plugin//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
        ]
        
        for event in events:
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{event.id}@agentforge",
                f"DTSTART:{event.start_time.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{event.end_time.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{event.title}",
                f"DESCRIPTION:{event.description}",
            ])
            
            if event.location:
                ics_lines.append(f"LOCATION:{event.location}")
            
            if event.attendees:
                for attendee in event.attendees:
                    ics_lines.append(f"ATTENDEE:mailto:{attendee}")
            
            ics_lines.append("END:VEVENT")
        
        ics_lines.append("END:VCALENDAR")
        
        return "\r\n".join(ics_lines)
    
    async def get_free_slots(
        self,
        date: datetime,
        duration_minutes: int = 60,
        working_hours: tuple = (9, 18)
    ) -> List[tuple]:
        """Find free time slots for a given date"""
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get events for the date
        next_day = date + timedelta(days=1)
        events = await self.get_events(date, next_day)
        
        # Generate working hours slots
        slots = []
        start_hour, end_hour = working_hours
        
        current = date.replace(hour=start_hour, minute=0)
        end = date.replace(hour=end_hour, minute=0)
        
        while current + timedelta(minutes=duration_minutes) <= end:
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Check if slot conflicts with any event
            is_free = True
            for event in events:
                if (current < event.end_time and slot_end > event.start_time):
                    is_free = False
                    break
            
            if is_free:
                slots.append((current, slot_end))
            
            current += timedelta(minutes=30)  # 30-minute intervals
        
        return slots
    
    async def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """Execute plugin actions"""
        if action == "create":
            return await self.create_event(
                title=params["title"],
                start_time=datetime.fromisoformat(params["start_time"]),
                end_time=datetime.fromisoformat(params["end_time"]),
                description=params.get("description", ""),
                location=params.get("location"),
                attendees=params.get("attendees"),
                reminder_minutes=params.get("reminder_minutes"),
                is_all_day=params.get("is_all_day", False)
            )
        elif action == "get":
            return await self.get_event(params["event_id"])
        elif action == "list":
            return await self.get_events(
                start_date=datetime.fromisoformat(params["start_date"]) if "start_date" in params else None,
                end_date=datetime.fromisoformat(params["end_date"]) if "end_date" in params else None
            )
        elif action == "today":
            return await self.get_today_events()
        elif action == "upcoming":
            return await self.get_upcoming_events(params.get("days", 7))
        elif action == "update":
            return await self.update_event(params["event_id"], **params.get("updates", {}))
        elif action == "delete":
            return await self.delete_event(params["event_id"])
        elif action == "conflicts":
            return await self.check_conflicts(
                datetime.fromisoformat(params["start_time"]),
                datetime.fromisoformat(params["end_time"]),
                params.get("exclude_event_id")
            )
        elif action == "free_slots":
            return await self.get_free_slots(
                datetime.fromisoformat(params["date"]),
                params.get("duration_minutes", 60)
            )
        elif action == "export":
            events = await self.get_events() if params.get("all") else None
            return await self.export_to_ics(events)
        else:
            raise ValueError(f"Unknown action: {action}")
