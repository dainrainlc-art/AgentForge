"""AI 技能市场 - 技能加载器和管理器."""

import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

from agentforge.core.schemas.skill_schema import SkillDefinition
from agentforge.core.skill_engine import SkillEngine


class SkillLoader:
    """技能加载器."""

    def __init__(self, skills_dir: str | None = None):
        if skills_dir is None:
            skills_dir = Path(__file__).parent.parent / "skills"

        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def load_skill(self, skill_path: Path) -> SkillDefinition:
        """从文件加载技能."""
        with open(skill_path, "r", encoding="utf-8") as f:
            skill_data = json.load(f)

        skill = SkillDefinition(**skill_data)
        logger.info(f"加载技能：{skill.name} v{skill.version}")
        return skill

    def load_all_skills(self) -> list[SkillDefinition]:
        """加载所有技能."""
        skills = []

        if not self.skills_dir.exists():
            logger.warning(f"技能目录不存在：{self.skills_dir}")
            return skills

        for skill_file in self.skills_dir.glob("*.json"):
            try:
                skill = self.load_skill(skill_file)
                skills.append(skill)
            except Exception as e:
                logger.error(f"加载技能失败 {skill_file}: {str(e)}")

        logger.info(f"加载了 {len(skills)} 个技能")
        return skills

    def save_skill(self, skill: SkillDefinition) -> Path:
        """保存技能到文件."""
        skill_file = self.skills_dir / f"{skill.name.replace(' ', '_')}.json"

        with open(skill_file, "w", encoding="utf-8") as f:
            json.dump(skill.model_dump(), f, ensure_ascii=False, indent=2)

        logger.info(f"保存技能：{skill.name} -> {skill_file}")
        return skill_file

    def delete_skill(self, skill_name: str) -> bool:
        """删除技能文件."""
        skill_file = self.skills_dir / f"{skill_name.replace(' ', '_')}.json"

        if skill_file.exists():
            skill_file.unlink()
            logger.info(f"删除技能：{skill_name}")
            return True

        logger.warning(f"技能文件不存在：{skill_file}")
        return False


class SkillManager:
    """技能管理器."""

    def __init__(self, skills_dir: str | None = None):
        self._loader = SkillLoader(skills_dir)
        self._engine = SkillEngine()
        self._skills: dict[str, SkillDefinition] = {}
        self._skills_by_event: dict[str, list[SkillDefinition]] = {}

    async def initialize(self):
        """初始化技能管理器."""
        await self.load_skills()
        self._index_skills()

    async def load_skills(self):
        """加载所有技能."""
        skills = self._loader.load_all_skills()

        for skill in skills:
            self._skills[skill.name] = skill

        logger.info(f"初始化完成，共 {len(self._skills)} 个技能")

    def _index_skills(self):
        """按事件类型索引技能."""
        self._skills_by_event.clear()

        for skill in self._skills.values():
            if skill.trigger.type == "event" and skill.trigger.event_type:
                event_type = skill.trigger.event_type
                if event_type not in self._skills_by_event:
                    self._skills_by_event[event_type] = []
                self._skills_by_event[event_type].append(skill)

        logger.info(f"技能索引完成，共 {len(self._skills_by_event)} 个事件类型")

    async def trigger_event(self, event_type: str, event_data: dict[str, Any]):
        """触发事件，执行相关技能."""
        if event_type not in self._skills_by_event:
            logger.debug(f"没有技能监听事件：{event_type}")
            return []

        results = []

        for skill in self._skills_by_event[event_type]:
            if not skill.enabled:
                logger.debug(f"技能已禁用：{skill.name}")
                continue

            try:
                result = await self._engine.execute_skill(skill, event_data)
                results.append({"skill": skill.name, "result": result})

                if result.status == "success":
                    logger.info(f"技能执行成功：{skill.name}")
                elif result.status == "failed":
                    logger.error(f"技能执行失败：{skill.name}, 错误：{result.error}")

            except Exception as e:
                logger.error(f"触发技能失败 {skill.name}: {str(e)}")
                results.append({"skill": skill.name, "error": str(e)})

        return results

    def register_skill(self, skill: SkillDefinition, save: bool = True):
        """注册技能."""
        self._skills[skill.name] = skill

        if save:
            self._loader.save_skill(skill)

        self._index_skills()
        logger.info(f"注册技能：{skill.name}")

    def unregister_skill(self, skill_name: str, delete: bool = False):
        """注销技能."""
        if skill_name in self._skills:
            skill = self._skills[skill_name]
            del self._skills[skill_name]

            if delete:
                self._loader.delete_skill(skill_name)

            self._index_skills()
            logger.info(f"注销技能：{skill_name}")
            return True

        return False

    def get_skill(self, skill_name: str) -> SkillDefinition | None:
        """获取技能定义."""
        return self._skills.get(skill_name)

    def list_skills(
        self,
        tag: str | None = None,
        enabled: bool | None = None,
    ) -> list[SkillDefinition]:
        """获取技能列表."""
        skills = list(self._skills.values())

        if tag is not None:
            skills = [s for s in skills if tag in s.tags]

        if enabled is not None:
            skills = [s for s in skills if s.enabled == enabled]

        return skills

    def get_skills_by_event(self, event_type: str) -> list[SkillDefinition]:
        """获取监听指定事件的技能列表."""
        return self._skills_by_event.get(event_type, [])

    def get_event_types(self) -> list[str]:
        """获取所有事件类型."""
        return list(self._skills_by_event.keys())

    def register_action_handler(self, action_type: str, handler):
        """注册动作处理器."""
        self._engine.register_action_handler(action_type, handler)
        logger.info(f"注册动作处理器：{action_type}")
