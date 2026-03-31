"""AI 技能市场 - 触发器系统."""

import asyncio
from datetime import datetime
from typing import Any, Callable

from croniter import croniter
from loguru import logger

from agentforge.core.schemas.skill_schema import SkillDefinition
from agentforge.core.skill_manager import SkillManager


class TimerTrigger:
    """定时器触发器."""

    def __init__(self, skill_manager: SkillManager):
        self._skill_manager = skill_manager
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._scheduled_skills: dict[str, asyncio.Task] = {}

    async def start(self):
        """启动定时器触发器."""
        self._running = True
        logger.info("定时器触发器已启动")

        # 每 60 秒检查一次需要触发的技能
        self._tasks.append(asyncio.create_task(self._check_loop()))

    async def stop(self):
        """停止定时器触发器."""
        self._running = False

        # 取消所有定时任务
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        for task in self._scheduled_skills.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._scheduled_skills.clear()
        logger.info("定时器触发器已停止")

    async def _check_loop(self):
        """检查循环."""
        while self._running:
            try:
                await self._check_and_trigger()
                await asyncio.sleep(60)  # 每分钟检查一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定时器检查失败：{str(e)}")
                await asyncio.sleep(60)

    async def _check_and_trigger(self):
        """检查并触发技能."""
        now = datetime.now()

        for skill in self._skill_manager.list_skills(enabled=True):
            if skill.trigger.type != "timer" or not skill.trigger.cron:
                continue

            try:
                # 检查是否应该触发
                if self._should_trigger(skill.trigger.cron, now):
                    logger.info(f"定时器触发技能：{skill.name}")
                    await self._skill_manager.trigger_event("timer", {"skill": skill.name})
            except Exception as e:
                logger.error(f"检查技能 {skill.name} 失败：{str(e)}")

    def _should_trigger(self, cron_expr: str, now: datetime) -> bool:
        """检查是否应该触发."""
        try:
            cron = croniter(cron_expr, now)
            prev_time = cron.get_prev(datetime)
            diff = (now - prev_time).total_seconds()

            # 如果在 60 秒内，认为应该触发
            return diff <= 60
        except Exception as e:
            logger.error(f"解析 Cron 表达式失败 {cron_expr}: {str(e)}")
            return False


class ManualTrigger:
    """手动触发器."""

    def __init__(self, skill_manager: SkillManager):
        self._skill_manager = skill_manager
        self._callbacks: dict[str, Callable] = {}

    async def trigger_skill(
        self, skill_name: str, variables: dict[str, Any] | None = None
    ) -> dict:
        """手动触发技能."""
        skill = self._skill_manager.get_skill(skill_name)

        if not skill:
            logger.error(f"技能不存在：{skill_name}")
            return {"success": False, "error": f"技能不存在：{skill_name}"}

        if not skill.enabled:
            logger.error(f"技能已禁用：{skill_name}")
            return {"success": False, "error": "技能已禁用"}

        try:
            results = await self._skill_manager.trigger_event("manual", variables or {})
            logger.info(f"手动触发技能：{skill_name}")
            return {"success": True, "results": results}
        except Exception as e:
            logger.error(f"手动触发技能失败 {skill_name}: {str(e)}")
            return {"success": False, "error": str(e)}

    def register_callback(self, skill_name: str, callback: Callable):
        """注册回调函数."""
        self._callbacks[skill_name] = callback
        logger.info(f"注册技能回调：{skill_name}")

    def unregister_callback(self, skill_name: str):
        """注销回调函数."""
        if skill_name in self._callbacks:
            del self._callbacks[skill_name]
            logger.info(f"注销技能回调：{skill_name}")


class TriggerSystem:
    """触发器系统（统一管理）。"""

    def __init__(self, skill_manager: SkillManager):
        self._skill_manager = skill_manager
        self._timer_trigger = TimerTrigger(skill_manager)
        self._manual_trigger = ManualTrigger(skill_manager)

    async def start(self):
        """启动触发器系统."""
        await self._timer_trigger.start()
        logger.info("触发器系统已启动")

    async def stop(self):
        """停止触发器系统."""
        await self._timer_trigger.stop()
        logger.info("触发器系统已停止")

    async def trigger_manual(self, skill_name: str, variables: dict | None = None):
        """手动触发技能."""
        return await self._manual_trigger.trigger_skill(skill_name, variables)

    def get_manual_trigger(self) -> ManualTrigger:
        """获取手动触发器."""
        return self._manual_trigger

    def get_timer_trigger(self) -> TimerTrigger:
        """获取定时器触发器."""
        return self._timer_trigger
