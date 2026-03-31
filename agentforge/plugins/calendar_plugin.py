"""插件系统 - 日历和提醒插件."""

from datetime import datetime, timedelta
from typing import Any

from loguru import logger

from agentforge.core.plugin_base import ActionPlugin


class CalendarPlugin(ActionPlugin):
    """日历和提醒插件."""

    name = "calendar"
    version = "1.0.0"
    description = "日历查询和提醒管理"
    author = "System"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._reminders: list[dict] = []

    async def initialize(self):
        """初始化插件."""
        self.enable()
        logger.info("日历插件已初始化")

    async def shutdown(self):
        """关闭插件."""
        self.disable()
        self._reminders.clear()
        logger.info("日历插件已关闭")

    def get_capabilities(self) -> list[str]:
        """返回插件能力."""
        return ["action", "calendar", "reminder"]

    async def execute(self, params: dict, context=None) -> dict:
        """执行日历操作."""
        operation = params.get("operation", "get_date")

        if operation == "get_date":
            return self.get_current_date()
        elif operation == "add_reminder":
            return self.add_reminder(params)
        elif operation == "list_reminders":
            return self.list_reminders()
        elif operation == "remove_reminder":
            return self.remove_reminder(params)
        else:
            raise ValueError(f"不支持的操作：{operation}")

    def get_current_date(self) -> dict:
        """获取当前日期."""
        now = datetime.now()

        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.isoformat(),
            "timestamp": now.timestamp(),
            "weekday": now.strftime("%A"),
            "week_number": now.isocalendar()[1],
        }

    def add_reminder(self, params: dict) -> dict:
        """添加提醒."""
        title = params.get("title", "")
        description = params.get("description", "")
        remind_time = params.get("time", "")

        if not title:
            raise ValueError("必须指定提醒标题")

        try:
            if remind_time:
                remind_datetime = datetime.fromisoformat(remind_time)
            else:
                remind_datetime = datetime.now()

            reminder = {
                "id": len(self._reminders) + 1,
                "title": title,
                "description": description,
                "time": remind_datetime.isoformat(),
                "created_at": datetime.now().isoformat(),
                "status": "pending",
            }

            self._reminders.append(reminder)

            logger.info(f"添加提醒：{title} @ {remind_time}")

            return {
                "success": True,
                "reminder": reminder,
                "message": f"提醒已添加：{title}",
            }

        except Exception as e:
            logger.error(f"添加提醒失败：{str(e)}")
            return {"error": str(e)}

    def list_reminders(self, status: str | None = None) -> dict:
        """列出提醒."""
        if status:
            reminders = [r for r in self._reminders if r.get("status") == status]
        else:
            reminders = self._reminders

        return {
            "count": len(reminders),
            "reminders": reminders,
        }

    def remove_reminder(self, params: dict) -> dict:
        """移除提醒."""
        reminder_id = params.get("id")

        if not reminder_id:
            raise ValueError("必须指定提醒 ID")

        for i, reminder in enumerate(self._reminders):
            if reminder["id"] == reminder_id:
                removed = self._reminders.pop(i)
                logger.info(f"移除提醒：{removed['title']}")
                return {
                    "success": True,
                    "message": f"提醒已移除：{removed['title']}",
                }

        return {"error": f"未找到提醒 ID: {reminder_id}"}

    def get_upcoming_events(self, days: int = 7) -> dict:
        """获取即将到来的事件."""
        now = datetime.now()
        future = now + timedelta(days=days)

        upcoming = []
        for reminder in self._reminders:
            try:
                remind_time = datetime.fromisoformat(reminder["time"])
                if now <= remind_time <= future:
                    upcoming.append(reminder)
            except Exception:
                continue

        return {
            "count": len(upcoming),
            "events": upcoming,
        }

    def validate_config(self) -> bool:
        """验证配置."""
        return True
