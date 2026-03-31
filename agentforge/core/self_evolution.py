"""
Self-Evolution Engine - Memory consolidation, self-check, and task review
"""
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from loguru import logger
import asyncio
import json
import re
import aiofiles
from pathlib import Path

from agentforge.memory import MemoryStore
from agentforge.llm import QianfanClient
from agentforge.config import settings


class MemoryConsolidator:
    """Consolidate memories during off-peak hours"""
    
    CONSOLIDATION_HOUR = 3
    MAX_SHORT_TERM_MEMORIES = 100
    SIMILARITY_THRESHOLD = 0.85
    
    def __init__(self, memory_store: MemoryStore, llm_client: QianfanClient):
        self.memory_store = memory_store
        self.llm_client = llm_client
        self._last_consolidation: Optional[datetime] = None
        self._consolidation_in_progress: bool = False
        self._memory_file_path = Path(settings.memory_file_path)
        if not self._memory_file_path.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            self._memory_file_path = project_root / self._memory_file_path
    
    async def read_memory_file(self) -> Dict[str, Any]:
        """Read and parse MEMORY.md file content.
        
        Returns:
            Dictionary containing sections and their content from MEMORY.md
        """
        try:
            if not self._memory_file_path.exists():
                logger.warning(f"Memory file not found: {self._memory_file_path}")
                return {
                    "last_update": None,
                    "business_insights": [],
                    "technical_insights": [],
                    "user_insights": [],
                    "success_cases": [],
                    "failure_lessons": [],
                    "workflow_patterns": [],
                    "problem_patterns": [],
                    "mastered_skills": [],
                    "skills_to_optimize": []
                }
            
            async with aiofiles.open(self._memory_file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            sections = {
                "last_update": self._extract_last_update(content),
                "business_insights": self._extract_section_content(content, "业务洞察"),
                "technical_insights": self._extract_section_content(content, "技术洞察"),
                "user_insights": self._extract_section_content(content, "用户洞察"),
                "success_cases": self._extract_section_content(content, "成功案例"),
                "failure_lessons": self._extract_section_content(content, "失败教训"),
                "workflow_patterns": self._extract_section_content(content, "工作流模式"),
                "problem_patterns": self._extract_section_content(content, "问题模式"),
                "mastered_skills": self._extract_section_content(content, "已掌握技能"),
                "skills_to_optimize": self._extract_section_content(content, "待优化技能")
            }
            
            logger.debug(f"Successfully read memory file: {self._memory_file_path}")
            return sections
            
        except Exception as e:
            logger.error(f"Failed to read memory file: {e}")
            return {
                "last_update": None,
                "business_insights": [],
                "technical_insights": [],
                "user_insights": [],
                "success_cases": [],
                "failure_lessons": [],
                "workflow_patterns": [],
                "problem_patterns": [],
                "mastered_skills": [],
                "skills_to_optimize": []
            }
    
    def _extract_last_update(self, content: str) -> Optional[str]:
        """Extract last update date from content."""
        match = re.search(r'\*\*最后更新\*\*:\s*(\d{4}-\d{2}-\d{2})', content)
        if match:
            return match.group(1)
        return None
    
    def _extract_section_content(self, content: str, section_title: str) -> List[str]:
        """Extract items from a specific section in MEMORY.md.
        
        Args:
            content: Full content of MEMORY.md
            section_title: Section title to extract
            
        Returns:
            List of items in that section
        """
        items = []
        pattern = rf"### {re.escape(section_title)}\n\n<!--(.*?)-->\n\n(.*?)(?=\n### |\n---|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            section_content = match.group(2)
            for line in section_content.split('\n'):
                line = line.strip()
                if line.startswith('- ') and len(line) > 2:
                    items.append(line[2:])
        
        return items
    
    async def write_memory_file(self, sections: Dict[str, Any]) -> bool:
        """Write updated content to MEMORY.md file.
        
        Args:
            sections: Dictionary containing sections and their content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            content = self._generate_memory_file_content(sections)
            
            async with aiofiles.open(self._memory_file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            logger.info(f"Successfully wrote memory file: {self._memory_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write memory file: {e}")
            return False
    
    def _generate_memory_file_content(self, sections: Dict[str, Any]) -> str:
        """Generate MEMORY.md file content from sections.
        
        Args:
            sections: Dictionary containing sections and their content
            
        Returns:
            Formatted markdown content
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        content = f"""# AgentForge 记忆库

> 自动记忆系统 - 记录重要洞察、经验教训和模式

---

## 最后更新时间

- **最后更新**: {today}
- **版本**: 1.0

---

## 核心洞察

### 业务洞察

<!-- AI 将在这里记录从业务运营中提取的关键洞察 -->

"""
        for item in sections.get("business_insights", []):
            content += f"- {item}\n"
        
        content += """
### 技术洞察

<!-- AI 将在这里记录技术实现和优化相关的洞察 -->

"""
        for item in sections.get("technical_insights", []):
            content += f"- {item}\n"
        
        content += """
### 用户洞察

<!-- AI 将在这里记录用户行为和偏好相关的洞察 -->

"""
        for item in sections.get("user_insights", []):
            content += f"- {item}\n"
        
        content += """
## 经验教训

### 成功案例

<!-- 记录成功的案例和可复制的经验 -->

"""
        for item in sections.get("success_cases", []):
            content += f"- {item}\n"
        
        content += """
### 失败教训

<!-- 记录失败案例和需要避免的问题 -->

"""
        for item in sections.get("failure_lessons", []):
            content += f"- {item}\n"
        
        content += """
## 模式识别

### 工作流模式

<!-- 识别出的高效工作流模式 -->

"""
        for item in sections.get("workflow_patterns", []):
            content += f"- {item}\n"
        
        content += """
### 问题模式

<!-- 常见问题及其解决方案模式 -->

"""
        for item in sections.get("problem_patterns", []):
            content += f"- {item}\n"
        
        content += """
## 技能库

### 已掌握技能

<!-- 系统已掌握并可重用的技能 -->

"""
        for item in sections.get("mastered_skills", []):
            content += f"- {item}\n"
        
        content += """
### 待优化技能

<!-- 需要改进的技能 -->

"""
        for item in sections.get("skills_to_optimize", []):
            content += f"- {item}\n"
        
        content += """
## 历史版本

### v1.0 - 2026-03-28

- 初始版本
- 建立记忆库基础结构

---

## 使用说明

本文件由系统自动维护，主要来源：

1. **每日记忆巩固** - 每天凌晨 3 点自动执行
2. **任务复盘** - 重要任务完成后自动更新
3. **自我检查** - 每天凌晨 4 点分析问题后更新

**注意**: 请勿手动修改此文件，所有更新由 AI 自动完成。
"""
        
        return content
        
        self._is_consolidating = False
    
    async def read_memory_file(self) -> Dict[str, Any]:
        """Read and parse MEMORY.md file content.
        
        Returns:
            Dictionary containing memory sections and metadata
        """
        try:
            if not self._memory_file_path.exists():
                logger.warning(f"Memory file not found: {self._memory_file_path}")
                return {
                    "last_update": None,
                    "version": "1.0",
                    "business_insights": [],
                    "technical_insights": [],
                    "user_insights": [],
                    "success_cases": [],
                    "failure_lessons": [],
                    "workflow_patterns": [],
                    "problem_patterns": [],
                    "mastered_skills": [],
                    "skills_to_optimize": []
                }
            
            async with aiofiles.open(self._memory_file_path, "r", encoding="utf-8") as f:
                content = await f.read()
            
            return self._parse_memory_content(content)
            
        except Exception as e:
            logger.error(f"Failed to read memory file: {e}")
            return {
                "last_update": None,
                "version": "1.0",
                "business_insights": [],
                "technical_insights": [],
                "user_insights": [],
                "success_cases": [],
                "failure_lessons": [],
                "workflow_patterns": [],
                "problem_patterns": [],
                "mastered_skills": [],
                "skills_to_optimize": []
            }
    
    def _parse_memory_content(self, content: str) -> Dict[str, Any]:
        """Parse MEMORY.md content into structured data.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Structured dictionary with memory sections
        """
        sections = {
            "last_update": self._extract_last_update(content),
            "version": self._extract_version(content),
            "business_insights": self._extract_section_items(content, "业务洞察"),
            "technical_insights": self._extract_section_items(content, "技术洞察"),
            "user_insights": self._extract_section_items(content, "用户洞察"),
            "success_cases": self._extract_section_items(content, "成功案例"),
            "failure_lessons": self._extract_section_items(content, "失败教训"),
            "workflow_patterns": self._extract_section_items(content, "工作流模式"),
            "problem_patterns": self._extract_section_items(content, "问题模式"),
            "mastered_skills": self._extract_section_items(content, "已掌握技能"),
            "skills_to_optimize": self._extract_section_items(content, "待优化技能")
        }
        return sections
    
    def _extract_last_update(self, content: str) -> Optional[str]:
        """Extract last update timestamp."""
        match = re.search(r"\*\*最后更新\*\*:\s*(\d{4}-\d{2}-\d{2})", content)
        return match.group(1) if match else None
    
    def _extract_version(self, content: str) -> str:
        """Extract version number."""
        match = re.search(r"\*\*版本\*\*:\s*v?([\d.]+)", content)
        return match.group(1) if match else "1.0"
    
    def _extract_section_items(self, content: str, section_name: str) -> List[str]:
        """Extract items from a specific section."""
        pattern = rf"### {re.escape(section_name)}\s*\n\s*<!--.*?-->\s*\n(.*?)(?=\n###|\n---|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []
        
        items = []
        for line in match.group(1).strip().split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                items.append(line[2:].strip())
            elif line and not line.startswith("<!"):
                items.append(line)
        
        return [item for item in items if item]
    
    async def write_memory_file(self, memory_data: Dict[str, Any]) -> bool:
        """Write updated memory data to MEMORY.md file.
        
        Args:
            memory_data: Structured memory data to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            content = self._generate_memory_content(memory_data)
            
            self._memory_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(self._memory_file_path, "w", encoding="utf-8") as f:
                await f.write(content)
            
            logger.info(f"Memory file updated: {self._memory_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write memory file: {e}")
            return False
    
    def _generate_memory_content(self, memory_data: Dict[str, Any]) -> str:
        """Generate MEMORY.md content from structured data.
        
        Args:
            memory_data: Structured memory data
            
        Returns:
            Formatted markdown content
        """
        last_update = datetime.now().strftime("%Y-%m-%d")
        version = memory_data.get("version", "1.0")
        
        content = f"""# AgentForge 记忆库

> 自动记忆系统 - 记录重要洞察、经验教训和模式

---

## 最后更新时间

- **最后更新**: {last_update}
- **版本**: v{version}

---

## 核心洞察

### 业务洞察

<!-- AI 将在这里记录从业务运营中提取的关键洞察 -->
"""
        
        for item in memory_data.get("business_insights", []):
            content += f"- {item}\n"
        
        content += "\n### 技术洞察\n\n<!-- AI 将在这里记录技术实现和优化相关的洞察 -->\n"
        for item in memory_data.get("technical_insights", []):
            content += f"- {item}\n"
        
        content += "\n### 用户洞察\n\n<!-- AI 将在这里记录用户行为和偏好相关的洞察 -->\n"
        for item in memory_data.get("user_insights", []):
            content += f"- {item}\n"
        
        content += "\n---\n\n## 经验教训\n\n### 成功案例\n\n<!-- 记录成功的案例和可复制的经验 -->\n"
        for item in memory_data.get("success_cases", []):
            content += f"- {item}\n"
        
        content += "\n### 失败教训\n\n<!-- 记录失败案例和需要避免的问题 -->\n"
        for item in memory_data.get("failure_lessons", []):
            content += f"- {item}\n"
        
        content += "\n---\n\n## 模式识别\n\n### 工作流模式\n\n<!-- 识别出的高效工作流模式 -->\n"
        for item in memory_data.get("workflow_patterns", []):
            content += f"- {item}\n"
        
        content += "\n### 问题模式\n\n<!-- 常见问题及其解决方案模式 -->\n"
        for item in memory_data.get("problem_patterns", []):
            content += f"- {item}\n"
        
        content += "\n---\n\n## 技能库\n\n### 已掌握技能\n\n<!-- 系统已掌握并可重用的技能 -->\n"
        for item in memory_data.get("mastered_skills", []):
            content += f"- {item}\n"
        
        content += "\n### 待优化技能\n\n<!-- 需要改进的技能 -->\n"
        for item in memory_data.get("skills_to_optimize", []):
            content += f"- {item}\n"
        
        content += f"""
---

## 历史版本

### v{version} - {last_update}

- 最新记忆巩固更新

---

## 使用说明

本文件由系统自动维护，主要来源：

1. **每日记忆巩固** - 每天凌晨 3 点自动执行
2. **任务复盘** - 重要任务完成后自动更新
3. **自我检查** - 每天凌晨 4 点分析问题后更新

**注意**: 请勿手动修改此文件，所有更新由 AI 自动完成。
"""
        
        return content
    
    async def consolidate(self, force: bool = False) -> Dict[str, Any]:
        """Run memory consolidation process
        
        Args:
            force: If True, run consolidation even if already in progress
        
        Returns:
            Statistics about the consolidation process
        """
        if self._consolidation_in_progress and not force:
            logger.warning("Consolidation already in progress")
            return {
                "status": "already_in_progress",
                "message": "Consolidation is already running"
            }
        
        logger.info("Starting memory consolidation...")
        
        start_time = time.time()
        stats = {
            "processed": 0,
            "consolidated": 0,
            "duplicates_removed": 0,
            "errors": 0,
            "insights_extracted": 0,
            "memory_file_updated": False
        }
        
        try:
            self._consolidation_in_progress = True
            
            short_term_memories = await self.memory_store.get_short_term_memories(
                limit=self.MAX_SHORT_TERM_MEMORIES
            )
            
            stats["processed"] = len(short_term_memories)
            
            if not short_term_memories:
                logger.info("No short-term memories to consolidate")
                return stats
            
            existing_memories = await self.read_memory_file()
            logger.info(f"Loaded {len(existing_memories)} existing memories from MEMORY.md")
            
            consolidated_memories = []
            
            for i, memory in enumerate(short_term_memories):
                try:
                    is_duplicate = await self._check_duplicate(
                        memory, 
                        consolidated_memories + existing_memories
                    )
                    
                    if is_duplicate:
                        stats["duplicates_removed"] += 1
                        logger.debug(f"Duplicate memory removed: {memory.get('content', '')[:50]}")
                        continue
                    
                    importance = await self._evaluate_importance(memory)
                    logger.debug(f"Memory importance score: {importance:.2f}")
                    
                    if importance >= 0.5:
                        await self.memory_store.store_long_term_memory(
                            content=memory.get("content", ""),
                            metadata={
                                "importance": importance,
                                "consolidated_at": datetime.now().isoformat(),
                                "original_timestamp": memory.get("timestamp")
                            }
                        )
                        consolidated_memories.append(memory)
                        stats["consolidated"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing memory {i}: {e}")
                    stats["errors"] += 1
            
            await self.memory_store.clear_short_term_memories()
            
            if consolidated_memories:
                updated_memories = await self._consolidate(
                    existing_memories, 
                    consolidated_memories
                )
                
                if updated_memories:
                    await self.write_memory_file(updated_memories)
                    stats["memory_file_updated"] = True
                    stats["insights_extracted"] = len(updated_memories.get("insights", []))
                    logger.info(f"MEMORY.md updated with {len(updated_memories.get('insights', []))} insights")
            
            self._last_consolidation = datetime.now()
            
            duration = time.time() - start_time
            logger.info(
                f"Memory consolidation completed in {duration:.2f}s. "
                f"Processed: {stats['processed']}, Consolidated: {stats['consolidated']}, "
                f"Duplicates removed: {stats['duplicates_removed']}, "
                f"Insights extracted: {stats['insights_extracted']}"
            )
            
        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")
            stats["errors"] += 1
        finally:
            self._consolidation_in_progress = False
        
        return stats
    
    async def trigger_consolidation(self) -> Dict[str, Any]:
        """Manually trigger memory consolidation (API interface)
        
        Returns:
            Statistics about the consolidation process
        """
        logger.info("Manual memory consolidation triggered")
        return await self.consolidate(force=True)
    
    def get_last_consolidation_time(self) -> Optional[datetime]:
        """Get the last consolidation time
        
        Returns:
            Last consolidation datetime or None if never consolidated
        """
        return self._last_consolidation
    
    def get_status(self) -> Dict[str, Any]:
        """Get consolidation status
        
        Returns:
            Status information including last consolidation time and whether in progress
        """
        return {
            "last_consolidation": self._last_consolidation.isoformat() if self._last_consolidation else None,
            "in_progress": self._consolidation_in_progress,
            "memory_file_path": str(self._memory_file_path)
        }
    
    async def read_memory_file(self) -> Dict[str, Any]:
        """Read and parse MEMORY.md file"""
        try:
            if not self._memory_file_path.exists():
                logger.warning(f"MEMORY.md not found at {self._memory_file_path}")
                return {
                    "insights": [],
                    "lessons": [],
                    "patterns": [],
                    "last_updated": None
                }
            
            async with aiofiles.open(self._memory_file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            memories = {
                "insights": [],
                "lessons": [],
                "patterns": [],
                "last_updated": None
            }
            
            insight_section = re.search(r'## 核心洞察\n\n(.*?)## 经验教训', content, re.DOTALL)
            if insight_section:
                business = re.findall(r'### 业务洞察\n\n(.*?)(?:###|$)', insight_section.group(1), re.DOTALL)
                technical = re.findall(r'### 技术洞察\n\n(.*?)(?:###|$)', insight_section.group(1), re.DOTALL)
                user = re.findall(r'### 用户洞察\n\n(.*?)(?:###|$)', insight_section.group(1), re.DOTALL)
                
                for item in business + technical + user:
                    items = [i.strip() for i in item.strip().split('\n') if i.strip() and not i.strip().startswith('<!--')]
                    memories["insights"].extend(items)
            
            lesson_section = re.search(r'## 经验教训\n\n(.*?)## 模式识别', content, re.DOTALL)
            if lesson_section:
                success = re.findall(r'### 成功案例\n\n(.*?)(?:###|$)', lesson_section.group(1), re.DOTALL)
                failure = re.findall(r'### 失败教训\n\n(.*?)(?:###|$)', lesson_section.group(1), re.DOTALL)
                
                for item in success + failure:
                    items = [i.strip() for i in item.strip().split('\n') if i.strip() and not i.strip().startswith('<!--')]
                    memories["lessons"].extend(items)
            
            pattern_section = re.search(r'## 模式识别\n\n(.*?)## 技能库', content, re.DOTALL)
            if pattern_section:
                workflow = re.findall(r'### 工作流模式\n\n(.*?)(?:###|$)', pattern_section.group(1), re.DOTALL)
                problem = re.findall(r'### 问题模式\n\n(.*?)(?:###|$)', pattern_section.group(1), re.DOTALL)
                
                for item in workflow + problem:
                    items = [i.strip() for i in item.strip().split('\n') if i.strip() and not i.strip().startswith('<!--')]
                    memories["patterns"].extend(items)
            
            last_updated = re.search(r'\*\*最后更新\*\*: (\d{4}-\d{2}-\d{2})', content)
            if last_updated:
                memories["last_updated"] = last_updated.group(1)
            
            logger.debug(f"Parsed MEMORY.md: {len(memories['insights'])} insights, "
                        f"{len(memories['lessons'])} lessons, {len(memories['patterns'])} patterns")
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to read MEMORY.md: {e}")
            return {
                "insights": [],
                "lessons": [],
                "patterns": [],
                "last_updated": None
            }
    
    async def write_memory_file(self, memories: Dict[str, Any]) -> None:
        """Write updated memories to MEMORY.md file"""
        try:
            current_time = datetime.now()
            today_str = current_time.strftime("%Y-%m-%d")
            
            content = f"""# AgentForge 记忆库

> 自动记忆系统 - 记录重要洞察、经验教训和模式

---

## 最后更新时间

- **最后更新**: {today_str}
- **版本**: 1.0

---

## 核心洞察

### 业务洞察

"""
            if memories.get("insights"):
                for insight in memories["insights"][:10]:
                    content += f"- {insight}\n"
            else:
                content += "<!-- AI 将在这里记录从业务运营中提取的关键洞察 -->\n"
            
            content += "\n### 技术洞察\n\n"
            if memories.get("insights"):
                for insight in memories["insights"][10:20]:
                    content += f"- {insight}\n"
            else:
                content += "<!-- AI 将在这里记录技术实现和优化相关的洞察 -->\n"
            
            content += "\n### 用户洞察\n\n"
            if memories.get("insights"):
                for insight in memories["insights"][20:]:
                    content += f"- {insight}\n"
            else:
                content += "<!-- AI 将在这里记录用户行为和偏好相关的洞察 -->\n"
            
            content += "\n## 经验教训\n\n### 成功案例\n\n"
            if memories.get("lessons"):
                for lesson in memories["lessons"][:10]:
                    content += f"- {lesson}\n"
            else:
                content += "<!-- 记录成功的案例和可复制的经验 -->\n"
            
            content += "\n### 失败教训\n\n"
            if memories.get("lessons"):
                for lesson in memories["lessons"][10:]:
                    content += f"- {lesson}\n"
            else:
                content += "<!-- 记录失败案例和需要避免的问题 -->\n"
            
            content += "\n## 模式识别\n\n### 工作流模式\n\n"
            if memories.get("patterns"):
                for pattern in memories["patterns"][:10]:
                    content += f"- {pattern}\n"
            else:
                content += "<!-- 识别出的高效工作流模式 -->\n"
            
            content += "\n### 问题模式\n\n"
            if memories.get("patterns"):
                for pattern in memories["patterns"][10:]:
                    content += f"- {pattern}\n"
            else:
                content += "<!-- 常见问题及其解决方案模式 -->\n"
            
            content += """
## 技能库

### 已掌握技能

<!-- 系统已掌握并可重用的技能 -->

### 待优化技能

<!-- 需要改进的技能 -->

---

## 历史版本

"""
            content += f"### v1.0 - {today_str}\n\n"
            content += f"- 更新洞察：{len(memories.get('insights', []))} 条\n"
            content += f"- 更新经验：{len(memories.get('lessons', []))} 条\n"
            content += f"- 更新模式：{len(memories.get('patterns', []))} 条\n"
            content += """
---

## 使用说明

本文件由系统自动维护，主要来源：

1. **每日记忆巩固** - 每天凌晨 3 点自动执行
2. **任务复盘** - 重要任务完成后自动更新
3. **自我检查** - 每天凌晨 4 点分析问题后更新

**注意**: 请勿手动修改此文件，所有更新由 AI 自动完成。
"""
            
            async with aiofiles.open(self._memory_file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            logger.info(f"MEMORY.md written successfully to {self._memory_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to write MEMORY.md: {e}")
            raise
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    async def _check_duplicate(
        self, 
        memory: Dict[str, Any], 
        existing: List[Dict[str, Any]]
    ) -> bool:
        """Check if memory is duplicate of existing ones"""
        if not existing:
            return False
        
        memory_content = memory.get("content", "").lower()
        
        for existing_memory in existing:
            existing_content = existing_memory.get("content", "").lower() if isinstance(existing_memory, dict) else existing_memory.lower()
            
            if self._calculate_similarity(memory_content, existing_content) >= self.SIMILARITY_THRESHOLD:
                return True
        
        return False
    
    async def _consolidate(
        self, 
        existing_memories: Dict[str, Any], 
        new_memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Consolidate new memories with existing ones using LLM"""
        logger.info("Starting LLM-powered memory consolidation...")
        
        try:
            new_contents = [m.get("content", "") for m in new_memories]
            
            all_insights = existing_memories.get("insights", []) + new_contents
            all_lessons = existing_memories.get("lessons", [])
            all_patterns = existing_memories.get("patterns", [])
            
            prompt = f"""分析以下记忆内容，提取深入的洞察、经验教训和模式：

新记忆：
{chr(10).join(f'- {c}' for c in new_contents[:20])}

现有洞察：
{chr(10).join(f'- {i}' for i in existing_memories.get('insights', [])[:10])}

请执行以下任务：
1. 去重：移除重复或相似的内容
2. 提取洞察：从记忆中提取关键的业务、技术、用户洞察
3. 总结经验：识别成功经验和失败教训
4. 发现模式：识别重复出现的工作流模式和问题模式

请以 JSON 格式返回：
{{
    "insights": ["洞察 1", "洞察 2", ...],
    "lessons": ["经验 1", "经验 2", ...],
    "patterns": ["模式 1", "模式 2", ...]
}}

要求：
- 每个类别最多保留 20 条
- 内容简洁明了
- 避免重复
- 优先保留高质量、高价值的记忆"""
            
            response = await self.llm_client.chat(message=prompt)
            
            try:
                consolidated = json.loads(response)
                
                all_insights = consolidated.get("insights", all_insights)
                all_lessons = consolidated.get("lessons", all_lessons)
                all_patterns = consolidated.get("patterns", all_patterns)
                
                logger.info(f"LLM extracted {len(all_insights)} insights, "
                           f"{len(all_lessons)} lessons, {len(all_patterns)} patterns")
                
            except json.JSONDecodeError:
                logger.warning("LLM response is not valid JSON, using fallback consolidation")
                all_insights = list(set(all_insights))[:20]
                all_lessons = list(set(all_lessons))[:20]
                all_patterns = list(set(all_patterns))[:20]
            
            return {
                "insights": all_insights,
                "lessons": all_lessons,
                "patterns": all_patterns,
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            logger.error(f"LLM consolidation failed: {e}")
            
            all_insights = list(set(existing_memories.get("insights", []) + new_contents))[:20]
            all_lessons = list(set(existing_memories.get("lessons", [])))[:20]
            all_patterns = list(set(existing_memories.get("patterns", [])))[:20]
            
            return {
                "insights": all_insights,
                "lessons": all_lessons,
                "patterns": all_patterns,
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
    
    async def _evaluate_importance(self, memory: Dict[str, Any]) -> float:
        """Evaluate importance of a memory using LLM"""
        content = memory.get("content", "")
        memory_type = memory.get("type", "general")
        timestamp = memory.get("timestamp", "")
        
        try:
            prompt = f"""分析以下记忆的重要性，评分 0-1（保留 2 位小数）：

记忆内容：{content}
记忆类型：{memory_type}
时间戳：{timestamp}

评分标准：
- 0.0-0.3: 日常信息，无需长期保留
- 0.3-0.5: 一般信息，可能有参考价值
- 0.5-0.7: 重要信息，值得长期保留
- 0.7-1.0: 关键信息，对业务/技术有重大影响

考虑因素：
1. 是否包含关键业务洞察
2. 是否包含技术经验教训
3. 是否反映用户行为模式
4. 是否具有长期参考价值
5. 是否涉及错误/成功的关键信息

请只返回一个 0-1 之间的数字，保留 2 位小数。"""
            
            response = await self.llm_client.chat(message=prompt)
            
            try:
                importance = float(response.strip())
                importance = max(0.0, min(1.0, importance))
                logger.debug(f"LLM evaluated importance: {importance:.2f} for memory: {content[:50]}")
                return importance
            except ValueError:
                logger.warning("LLM response is not a valid number, using fallback evaluation")
                
        except Exception as e:
            logger.warning(f"LLM importance evaluation failed: {e}, using fallback")
        
        importance_keywords = [
            "important", "critical", "essential", "key", "must",
            "remember", "note", "warning", "error", "success",
            "完成", "重要", "关键", "错误", "成功", "失败", "经验", "洞察"
        ]
        
        score = 0.3
        
        content_lower = content.lower()
        for keyword in importance_keywords:
            if keyword in content_lower:
                score += 0.08
        
        if len(content) > 200:
            score += 0.1
        if len(content) > 500:
            score += 0.1
        
        if memory_type in ["error", "success", "learning", "insight"]:
            score += 0.2
        
        return min(score, 1.0)


class SelfChecker:
    """Self-check system for error analysis and auto-repair"""
    
    CHECK_HOUR = 4
    MAX_ERRORS_TO_ANALYZE = 50
    
    def __init__(
        self, 
        llm_client: QianfanClient, 
        memory_store: MemoryStore,
        log_dir: Optional[str] = None,
        report_dir: Optional[str] = None
    ):
        self.llm_client = llm_client
        self.memory_store = memory_store
        self._last_check: Optional[datetime] = None
        self._error_log: List[Dict[str, Any]] = []
        self._is_running: bool = False
        
        project_root = Path(__file__).parent.parent.parent
        self._log_dir = Path(log_dir) if log_dir else project_root / "logs"
        self._report_dir = Path(report_dir) if report_dir else project_root / "reports"
        
        self._error_log_file = self._log_dir / "self_check_errors.jsonl"
        
        self._report_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SelfChecker initialized - Log dir: {self._log_dir}, Report dir: {self._report_dir}")
    
    async def _log_error_async(self, error_data: Dict[str, Any]) -> None:
        """Asynchronously log error to file"""
        try:
            async with aiofiles.open(self._error_log_file, 'a', encoding='utf-8') as f:
                await f.write(json.dumps(error_data, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to write error to log file: {e}")
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log an error for later analysis"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "traceback": str(error.__traceback__)
        }
        
        self._error_log.append(error_data)
        
        if len(self._error_log) > 100:
            self._error_log = self._error_log[-50:]
        
        asyncio.create_task(self._log_error_async(error_data))
        
        logger.debug(f"Error logged: {error_data['error_type']} - {error_data['error_message'][:100]}")
    
    async def read_error_logs(self) -> List[Dict[str, Any]]:
        """Read error logs from log files"""
        errors = []
        
        try:
            if not self._log_dir.exists():
                logger.warning(f"Log directory does not exist: {self._log_dir}")
                return errors
            
            log_files = list(self._log_dir.glob("*.log")) + list(self._log_dir.glob("*.jsonl"))
            
            for log_file in log_files:
                try:
                    if log_file.suffix == '.jsonl':
                        async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                            async for line in f:
                                line = line.strip()
                                if line:
                                    try:
                                        error_data = json.loads(line)
                                        errors.append(error_data)
                                    except json.JSONDecodeError:
                                        logger.warning(f"Invalid JSON in log file {log_file}: {line[:100]}")
                    elif log_file.suffix == '.log':
                        parsed_errors = await self._parse_log_file(log_file)
                        errors.extend(parsed_errors)
                except Exception as e:
                    logger.error(f"Failed to read log file {log_file}: {e}")
            
            errors.sort(key=lambda x: x.get("timestamp", ""))
            
            logger.info(f"Read {len(errors)} errors from log files")
            
        except Exception as e:
            logger.error(f"Failed to read error logs: {e}")
        
        return errors
    
    async def _parse_log_file(self, log_file: Path) -> List[Dict[str, Any]]:
        """Parse a log file and extract error entries"""
        errors = []
        
        try:
            async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                async for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if 'ERROR' in line or 'FATAL' in line or 'CRITICAL' in line:
                        parsed = self._parse_log_line(line)
                        if parsed:
                            errors.append(parsed)
                            
        except Exception as e:
            logger.error(f"Failed to parse log file {log_file}: {e}")
        
        return errors
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line"""
        patterns = [
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\|\s+(?P<level>\w+)\s+\|\s+(?P<logger>[^:]+):(?P<function>[^:]+):\d+\s+-\s+(?P<message>.+)',
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+(?P<level>\w+)\s+(?P<message>.+)',
            r'\[(?P<timestamp>[^\]]+)\]\s+(?P<level>\w+)\s+(?P<message>.+)',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groupdict()
                return {
                    "timestamp": groups.get("timestamp", datetime.now().isoformat()),
                    "error_type": groups.get("level", "Unknown"),
                    "error_message": groups.get("message", line),
                    "logger": groups.get("logger", ""),
                    "function": groups.get("function", ""),
                    "raw_line": line
                }
        
        return None
    
    async def run_self_check(self, force: bool = False) -> Dict[str, Any]:
        """Run self-check process"""
        if self._is_running and not force:
            logger.warning("Self-check already running")
            return {
                "status": "already_running",
                "message": "Self-check is already in progress"
            }
        
        logger.info("Starting self-check...")
        
        start_time = time.time()
        stats = {
            "errors_analyzed": 0,
            "file_errors_read": 0,
            "memory_errors_read": 0,
            "issues_found": 0,
            "patterns_identified": 0,
            "suggestions_generated": 0,
            "report_generated": False,
            "errors": []
        }
        
        try:
            self._is_running = True
            
            file_errors = await self.read_error_logs()
            stats["file_errors_read"] = len(file_errors)
            
            memory_errors = self._error_log[-self.MAX_ERRORS_TO_ANALYZE:]
            stats["memory_errors_read"] = len(memory_errors)
            
            all_errors = file_errors + memory_errors
            all_errors = all_errors[-self.MAX_ERRORS_TO_ANALYZE:]
            stats["errors_analyzed"] = len(all_errors)
            
            if not all_errors:
                logger.info("No errors to analyze")
                await self._generate_empty_report()
                stats["report_generated"] = True
                return stats
            
            error_summary = self._summarize_errors(all_errors)
            
            analysis = await self._analyze_errors_with_llm(all_errors)
            
            if analysis.get("issues"):
                stats["issues_found"] = len(analysis["issues"])
            
            if analysis.get("patterns"):
                stats["patterns_identified"] = len(analysis["patterns"])
            
            if analysis.get("suggestions"):
                stats["suggestions_generated"] = len(analysis["suggestions"])
            
            report_path = await self._generate_diagnostic_report(analysis, stats)
            if report_path:
                stats["report_generated"] = True
                stats["report_path"] = str(report_path)
            
            for suggestion in analysis.get("suggestions", [])[:3]:
                try:
                    await self._apply_suggestion(suggestion)
                    stats["applied_fixes"] = stats.get("applied_fixes", 0) + 1
                except Exception as e:
                    logger.error(f"Failed to apply suggestion: {e}")
                    stats["errors"].append(str(e))
            
            await self.memory_store.store_memory(
                content=f"Self-check completed: {stats}",
                memory_type="self_check"
            )
            
            self._last_check = datetime.now()
            
            duration = time.time() - start_time
            logger.info(
                f"Self-check completed in {duration:.2f}s. "
                f"Errors analyzed: {stats['errors_analyzed']}, "
                f"Issues found: {stats['issues_found']}, "
                f"Report generated: {stats['report_generated']}"
            )
            
        except Exception as e:
            logger.error(f"Self-check failed: {e}")
            stats["errors"].append(str(e))
        finally:
            self._is_running = False
        
        return stats
    
    def _summarize_errors(self, errors: List[Dict[str, Any]]) -> str:
        """Summarize errors for analysis"""
        error_types = {}
        error_sources = {}
        
        for error in errors:
            error_type = error.get("error_type", "Unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            source = error.get("logger", error.get("function", "Unknown"))
            if source != "Unknown":
                error_sources[source] = error_sources.get(source, 0) + 1
        
        summary_lines = ["=== Error Type Summary ==="]
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            summary_lines.append(f"{error_type}: {count} occurrences")
        
        if error_sources:
            summary_lines.append("\n=== Error Source Summary ===")
            for source, count in sorted(error_sources.items(), key=lambda x: x[1], reverse=True):
                summary_lines.append(f"{source}: {count} occurrences")
        
        summary_lines.append("\n=== Recent Error Samples ===")
        for error in errors[-5:]:
            summary_lines.append(f"[{error.get('timestamp', 'N/A')}] {error.get('error_type', 'Unknown')}: {error.get('error_message', 'N/A')[:200]}")
        
        return "\n".join(summary_lines)
    
    async def _analyze_errors_with_llm(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze errors using LLM to identify patterns and generate suggestions"""
        error_details = []
        for error in errors[-20:]:
            error_details.append(
                f"- [{error.get('timestamp', 'N/A')}] {error.get('error_type', 'Unknown')}: "
                f"{error.get('error_message', 'N/A')[:300]}"
            )
        
        errors_text = "\n".join(error_details)
        
        prompt = f"""你是一个专业的系统诊断专家。请分析以下错误日志，并提供详细的诊断报告。

错误日志:
{errors_text}

请执行以下分析任务:

1. **问题识别**: 识别系统中的主要问题和潜在风险
2. **根本原因分析**: 分析每个问题可能的根本原因
3. **影响范围评估**: 评估这些问题对系统的影响
4. **错误模式识别**: 识别重复出现的错误模式
5. **修复建议**: 提供具体的、可操作的修复建议 (包括代码或配置修改)

请严格按照以下 JSON 格式返回:
{{
    "issues": [
        {{
            "title": "问题标题",
            "description": "问题详细描述",
            "root_cause": "根本原因",
            "impact": "影响范围",
            "severity": "high|medium|low"
        }}
    ],
    "patterns": [
        {{
            "pattern_name": "模式名称",
            "description": "模式描述",
            "frequency": "出现频率",
            "suggestion": "应对建议"
        }}
    ],
    "suggestions": [
        {{
            "title": "建议标题",
            "description": "建议详细描述",
            "priority": "high|medium|low",
            "code_changes": "需要的代码修改 (可选)",
            "config_changes": "需要的配置修改 (可选)",
            "estimated_effort": "预估工作量 (如：1h, 1d)"
        }}
    ]
}}

要求:
- 问题描述清晰具体
- 根本原因分析深入
- 修复建议可操作
- 优先处理高严重性问题"""
        
        try:
            response = await self.llm_client.chat(message=prompt)
            
            try:
                result = json.loads(response)
                logger.info(f"LLM analysis completed: {len(result.get('issues', []))} issues, "
                           f"{len(result.get('patterns', []))} patterns, "
                           f"{len(result.get('suggestions', []))} suggestions")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response: {e}")
                logger.debug(f"Raw response: {response[:500]}")
                return {
                    "issues": [],
                    "patterns": [],
                    "suggestions": []
                }
                
        except Exception as e:
            logger.error(f"Error analysis with LLM failed: {e}")
            return {
                "issues": [],
                "patterns": [],
                "suggestions": []
            }
    
    async def _generate_diagnostic_report(
        self, 
        analysis: Dict[str, Any], 
        stats: Dict[str, Any]
    ) -> Optional[Path]:
        """Generate a detailed diagnostic report"""
        try:
            report_date = datetime.now()
            report_filename = f"self_check_{report_date.strftime('%Y-%m-%d')}.md"
            report_path = self._report_dir / report_filename
            
            timestamp = report_date.strftime("%Y-%m-%d %H:%M:%S")
            
            content = f"""# AgentForge 自我诊断报告

**生成时间**: {timestamp}
**报告版本**: 1.0

---

## 执行摘要

本次自我检查共分析了 **{stats['errors_analyzed']}** 条错误日志（其中文件日志 {stats['file_errors_read']} 条，内存日志 {stats['memory_errors_read']} 条），识别出 **{stats['issues_found']}** 个主要问题，发现 **{stats['patterns_identified']}** 个错误模式，生成 **{stats['suggestions_generated']}** 条修复建议。

---

## 问题诊断

"""
            
            for i, issue in enumerate(analysis.get("issues", []), 1):
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.get("severity", "medium"), "⚪")
                content += f"""### {i}. {issue.get('title', '未知问题')} {severity_emoji}

**问题描述**: {issue.get('description', '无详细描述')}

**根本原因**: {issue.get('root_cause', '未确定')}

**影响范围**: {issue.get('impact', '未评估')}

"""
            
            content += """## 错误模式识别

"""
            
            for i, pattern in enumerate(analysis.get("patterns", []), 1):
                content += f"""### {i}. {pattern.get('pattern_name', '未知模式')}

**模式描述**: {pattern.get('description', '无详细描述')}

**出现频率**: {pattern.get('frequency', '未知')}

**应对建议**: {pattern.get('suggestion', '无')}

"""
            
            content += """## 修复建议

"""
            
            for i, suggestion in enumerate(analysis.get("suggestions", []), 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(suggestion.get("priority", "medium"), "⚪")
                content += f"""### {i}. {suggestion.get('title', '未知建议')} {priority_emoji}

**建议描述**: {suggestion.get('description', '无详细描述')}

**优先级**: {suggestion.get('priority', 'medium')}

**预估工作量**: {suggestion.get('estimated_effort', '未评估')}

"""
                if suggestion.get("code_changes"):
                    content += f"""**代码修改**:
```
{suggestion.get('code_changes')}
```

"""
                
                if suggestion.get("config_changes"):
                    content += f"""**配置修改**:
```
{suggestion.get('config_changes')}
```

"""
            
            content += f"""---

## 附录：错误统计

### 错误类型分布

"""
            
            error_types = {}
            for error in self._error_log[-50:] + analysis.get("raw_errors", []):
                error_type = error.get("error_type", "Unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                content += f"- **{error_type}**: {count} 次\n"
            
            content += f"""
---

## 后续行动

- [ ] 审查高优先级问题
- [ ] 实施关键修复建议
- [ ] 更新监控告警规则
- [ ] 安排技术债务偿还

---

*本报告由 AgentForge 自我检查系统自动生成*
"""
            
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            logger.info(f"Diagnostic report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to generate diagnostic report: {e}")
            return None
    
    async def _generate_empty_report(self) -> Optional[Path]:
        """Generate an empty report when no errors found"""
        try:
            report_date = datetime.now()
            report_filename = f"self_check_{report_date.strftime('%Y-%m-%d')}.md"
            report_path = self._report_dir / report_filename
            
            content = f"""# AgentForge 自我诊断报告

**生成时间**: {report_date.strftime('%Y-%m-%d %H:%M:%S')}
**报告版本**: 1.0

---

## 执行摘要

本次自我检查未发现任何错误日志，系统运行正常。

---

## 检查详情

- **检查时间**: {report_date.strftime('%Y-%m-%d %H:%M:%S')}
- **检查范围**: 日志文件、内存错误记录
- **检查结果**: ✅ 无异常

---

## 建议

虽然本次检查未发现错误，但建议继续保持良好的监控和日志记录习惯。

---

*本报告由 AgentForge 自我检查系统自动生成*
"""
            
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            logger.info(f"Empty diagnostic report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to generate empty report: {e}")
            return None
    
    async def _apply_suggestion(self, suggestion: Dict[str, Any]) -> None:
        """Apply a suggested fix"""
        suggestion_title = suggestion.get("title", "Unknown suggestion")
        logger.info(f"Applying suggestion: {suggestion_title}")
        
        await self.memory_store.store_memory(
            content=f"Applied fix: {suggestion_title} - {suggestion.get('description', '')[:200]}",
            memory_type="self_evolution"
        )
    
    async def trigger_self_check(self) -> Dict[str, Any]:
        """Manually trigger self-check process (API interface)"""
        logger.info("Manual self-check triggered")
        return await self.run_self_check(force=True)
    
    def get_self_check_status(self) -> Dict[str, Any]:
        """Get self-check status"""
        return {
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "is_running": self._is_running,
            "error_log_count": len(self._error_log),
            "log_dir": str(self._log_dir),
            "report_dir": str(self._report_dir),
            "error_log_file": str(self._error_log_file),
            "error_log_file_exists": self._error_log_file.exists() if self._error_log_file else False
        }
    
    def get_last_self_check_time(self) -> Optional[datetime]:
        """Get the last self-check time"""
        return self._last_check


class TaskReviewer:
    """Review completed tasks and extract learnings"""
    
    REVIEW_THRESHOLD = 10
    
    def __init__(
        self, 
        llm_client: QianfanClient, 
        memory_store: MemoryStore,
        report_dir: Optional[str] = None,
        data_dir: Optional[str] = None
    ):
        self.llm_client = llm_client
        self.memory_store = memory_store
        self._completed_tasks: List[Dict[str, Any]] = []
        self._last_review_time: Optional[datetime] = None
        self._is_reviewing: bool = False
        
        project_root = Path(__file__).parent.parent.parent
        self._report_dir = Path(report_dir) if report_dir else project_root / "reports"
        self._data_dir = Path(data_dir) if data_dir else project_root / "data" / "task_history"
        
        self._report_dir.mkdir(parents=True, exist_ok=True)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TaskReviewer initialized - Report dir: {self._report_dir}, Data dir: {self._data_dir}")
    
    def record_task_completion(
        self,
        task_id: str,
        task_type: str,
        description: str,
        result: str,
        success: bool,
        input_params: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
        resource_usage: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a completed task for review.
        
        Args:
            task_id: Unique task identifier
            task_type: Type of task (e.g., 'fiverr_order', 'social_media_post')
            description: Task description
            result: Task result description
            success: Whether task was successful
            input_params: Input parameters used for the task
            output_data: Output data generated by the task
            execution_time: Execution time in seconds
            resource_usage: Resource usage metrics (e.g., tokens, API calls)
            metadata: Additional metadata
        """
        completed_at = datetime.now()
        
        task_record = {
            "task_id": task_id,
            "task_type": task_type,
            "description": description,
            "result": result,
            "success": success,
            "completed_at": completed_at.isoformat(),
            "input_params": input_params or {},
            "output_data": output_data or {},
            "execution_time_seconds": execution_time,
            "resource_usage": resource_usage or {},
            "metadata": metadata or {}
        }
        
        self._completed_tasks.append(task_record)
        
        asyncio.create_task(self._save_task_to_jsonl(task_record, completed_at))
        
        logger.info(
            f"Task recorded: {task_id} ({task_type}) - Success: {success}, "
            f"Execution time: {execution_time:.2f}s" if execution_time else ""
        )
        
        if len(self._completed_tasks) >= self.REVIEW_THRESHOLD:
            logger.info(f"Task count ({len(self._completed_tasks)}) reached threshold, auto-triggering review")
            asyncio.create_task(self.review_tasks())
    
    async def _save_task_to_jsonl(self, task_record: Dict[str, Any], completed_at: datetime) -> bool:
        """Save task record to JSONL file.
        
        Args:
            task_record: Task record dictionary
            completed_at: Task completion datetime
            
        Returns:
            True if successful, False otherwise
        """
        try:
            date_str = completed_at.strftime("%Y-%m-%d")
            jsonl_file = self._data_dir / f"{date_str}.jsonl"
            
            jsonl_line = json.dumps(task_record, ensure_ascii=False) + "\n"
            
            async with aiofiles.open(jsonl_file, 'a', encoding='utf-8') as f:
                await f.write(jsonl_line)
            
            logger.debug(f"Task {task_record['task_id']} saved to {jsonl_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save task to JSONL: {e}")
            return False
    
    async def _load_tasks_from_jsonl(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load task records from JSONL files.
        
        Args:
            date_str: Specific date to load (YYYY-MM-DD format), or None for all dates
            
        Returns:
            List of task records
        """
        tasks = []
        
        try:
            if not self._data_dir.exists():
                logger.warning(f"Data directory does not exist: {self._data_dir}")
                return tasks
            
            if date_str:
                jsonl_file = self._data_dir / f"{date_str}.jsonl"
                if jsonl_file.exists():
                    async with aiofiles.open(jsonl_file, 'r', encoding='utf-8') as f:
                        async for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    task = json.loads(line)
                                    tasks.append(task)
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Invalid JSON in {jsonl_file}: {e}")
            else:
                for file in self._data_dir.glob("*.jsonl"):
                    async with aiofiles.open(file, 'r', encoding='utf-8') as f:
                        async for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    task = json.loads(line)
                                    tasks.append(task)
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Invalid JSON in {file}: {e}")
            
            tasks.sort(key=lambda x: x.get("completed_at", ""))
            logger.info(f"Loaded {len(tasks)} tasks from JSONL files")
            
        except Exception as e:
            logger.error(f"Failed to load tasks from JSONL: {e}")
        
        return tasks
    
    async def review_tasks(self, force: bool = False) -> Dict[str, Any]:
        """Review completed tasks and extract learnings.
        
        Args:
            force: If True, force review even if no tasks in memory (will load from files)
            
        Returns:
            Statistics about the review process
        """
        if self._is_reviewing and not force:
            logger.warning("Task review already in progress")
            return {
                "status": "already_in_progress",
                "message": "Task review is already running"
            }
        
        logger.info("Starting task review...")
        
        start_time = time.time()
        stats = {
            "tasks_reviewed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "learnings_extracted": 0,
            "patterns_found": 0,
            "skills_updated": 0,
            "report_generated": False,
            "errors": []
        }
        
        try:
            self._is_reviewing = True
            
            if not self._completed_tasks and not force:
                logger.info("No tasks in memory to review")
                loaded_tasks = await self._load_tasks_from_jsonl()
                if loaded_tasks:
                    self._completed_tasks = loaded_tasks[-self.REVIEW_THRESHOLD * 2:]
                    logger.info(f"Loaded {len(self._completed_tasks)} tasks from files for review")
            
            if not self._completed_tasks:
                logger.info("No tasks to review")
                await self._generate_empty_review_report()
                stats["report_generated"] = True
                return stats
            
            stats["tasks_reviewed"] = len(self._completed_tasks)
            
            successful_tasks = [t for t in self._completed_tasks if t.get("success", False)]
            failed_tasks = [t for t in self._completed_tasks if not t.get("success", False)]
            
            stats["successful_tasks"] = len(successful_tasks)
            stats["failed_tasks"] = len(failed_tasks)
            
            logger.info(
                f"Analyzing {stats['tasks_reviewed']} tasks: "
                f"{stats['successful_tasks']} successful, {stats['failed_tasks']} failed"
            )
            
            success_patterns = []
            if successful_tasks:
                success_patterns = await self._analyze_success_patterns(successful_tasks)
                stats["patterns_found"] = len(success_patterns)
                logger.info(f"Extracted {len(success_patterns)} success patterns")
            
            failure_lessons = []
            if failed_tasks:
                failure_lessons = await self._analyze_failure_lessons(failed_tasks)
                stats["learnings_extracted"] += len(failure_lessons)
                logger.info(f"Extracted {len(failure_lessons)} failure lessons")
            
            all_learnings = success_patterns + failure_lessons
            if all_learnings:
                await self._update_memory_with_learnings(all_learnings)
                stats["learnings_extracted"] = len(all_learnings)
            
            skills_updated = await self._update_skill_library(successful_tasks, failed_tasks)
            stats["skills_updated"] = skills_updated
            
            report_path = await self._generate_review_report(stats, success_patterns, failure_lessons)
            if report_path:
                stats["report_generated"] = True
                stats["report_path"] = str(report_path)
            
            self._completed_tasks = []
            
            self._last_review_time = datetime.now()
            
            duration = time.time() - start_time
            logger.info(
                f"Task review completed in {duration:.2f}s. "
                f"Reviewed: {stats['tasks_reviewed']}, "
                f"Patterns: {stats['patterns_found']}, "
                f"Learnings: {stats['learnings_extracted']}, "
                f"Skills updated: {stats['skills_updated']}"
            )
            
        except Exception as e:
            logger.error(f"Task review failed: {e}")
            stats["errors"].append(str(e))
        finally:
            self._is_reviewing = False
        
        return stats
    
    async def _analyze_success_patterns(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze successful tasks to extract patterns.
        
        Args:
            tasks: List of successful task records
            
        Returns:
            List of pattern dictionaries
        """
        if not tasks:
            return []
        
        task_details = []
        for task in tasks[:15]:
            detail = {
                "task_id": task.get("task_id"),
                "task_type": task.get("task_type"),
                "description": task.get("description"),
                "input_params": task.get("input_params"),
                "output_data": task.get("output_data"),
                "execution_time": task.get("execution_time_seconds"),
                "resource_usage": task.get("resource_usage")
            }
            task_details.append(detail)
        
        prompt = f"""分析以下成功任务，提取可复用的成功模式：

任务列表：
{json.dumps(task_details, ensure_ascii=False, indent=2)}

请执行以下分析：
1. 识别共同的成功因素
2. 提取高效的工作流程模式
3. 总结最佳实践
4. 识别关键成功指标

请以 JSON 格式返回：
{{
    "patterns": [
        {{
            "pattern_name": "模式名称",
            "description": "模式详细描述",
            "applicable_scenarios": ["适用场景 1", "适用场景 2"],
            "key_success_factors": ["关键因素 1", "关键因素 2"],
            "recommended_actions": ["推荐行动 1", "推荐行动 2"],
            "confidence_score": 0.95
        }}
    ]
}}

要求：
- 模式具有可复用性
- 描述具体明确
- 提供可操作的建议
- 置信度评分 0-1"""
        
        try:
            response = await self.llm_client.chat(message=prompt)
            
            try:
                result = json.loads(response)
                patterns = result.get("patterns", [])
                logger.info(f"LLM extracted {len(patterns)} success patterns")
                return patterns
            except json.JSONDecodeError:
                logger.warning("LLM response is not valid JSON, using fallback")
                return [{
                    "pattern_name": "成功模式",
                    "description": response[:500],
                    "applicable_scenarios": ["通用场景"],
                    "key_success_factors": ["高质量执行"],
                    "recommended_actions": ["继续保持"],
                    "confidence_score": 0.7
                }]
                
        except Exception as e:
            logger.error(f"Success pattern analysis failed: {e}")
            return []
    
    async def _analyze_failure_lessons(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze failed tasks to extract lessons.
        
        Args:
            tasks: List of failed task records
            
        Returns:
            List of lesson dictionaries
        """
        if not tasks:
            return []
        
        task_details = []
        for task in tasks[:15]:
            detail = {
                "task_id": task.get("task_id"),
                "task_type": task.get("task_type"),
                "description": task.get("description"),
                "result": task.get("result"),
                "input_params": task.get("input_params"),
                "execution_time": task.get("execution_time_seconds"),
                "resource_usage": task.get("resource_usage"),
                "metadata": task.get("metadata")
            }
            task_details.append(detail)
        
        prompt = f"""分析以下失败任务，提取经验教训和改进建议：

任务列表：
{json.dumps(task_details, ensure_ascii=False, indent=2)}

请执行以下分析：
1. 识别失败的根本原因
2. 总结常见问题模式
3. 提供具体的改进建议
4. 制定预防措施

请以 JSON 格式返回：
{{
    "lessons": [
        {{
            "lesson_title": "教训标题",
            "root_cause": "根本原因分析",
            "problem_description": "问题详细描述",
            "impact": "影响范围",
            "improvement_suggestions": ["改进建议 1", "改进建议 2"],
            "prevention_measures": ["预防措施 1", "预防措施 2"],
            "priority": "high|medium|low"
        }}
    ]
}}

要求：
- 根本原因分析深入
- 改进建议具体可操作
- 预防措施切实可行
- 优先级评估合理"""
        
        try:
            response = await self.llm_client.chat(message=prompt)
            
            try:
                result = json.loads(response)
                lessons = result.get("lessons", [])
                logger.info(f"LLM extracted {len(lessons)} failure lessons")
                return lessons
            except json.JSONDecodeError:
                logger.warning("LLM response is not valid JSON, using fallback")
                return [{
                    "lesson_title": "失败教训",
                    "root_cause": "未知",
                    "problem_description": response[:500],
                    "impact": "需要进一步分析",
                    "improvement_suggestions": ["改进执行流程"],
                    "prevention_measures": ["加强监控"],
                    "priority": "medium"
                }]
                
        except Exception as e:
            logger.error(f"Failure lesson analysis failed: {e}")
            return []
    
    async def _update_memory_with_learnings(self, learnings: List[Dict[str, Any]]) -> bool:
        """Store learnings to memory.
        
        Args:
            learnings: List of learning dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            for learning in learnings:
                if "pattern_name" in learning:
                    content = f"成功模式：{learning['pattern_name']} - {learning['description']}"
                    memory_type = "success_pattern"
                else:
                    content = f"失败教训：{learning['lesson_title']} - {learning['root_cause']}"
                    memory_type = "failure_lesson"
                
                await self.memory_store.store_memory(
                    content=content,
                    memory_type=memory_type,
                    metadata={
                        "source": "task_review",
                        "learning": learning,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            logger.info(f"Stored {len(learnings)} learnings to memory")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store learnings to memory: {e}")
            return False
    
    async def _update_skill_library(
        self, 
        successful_tasks: List[Dict[str, Any]], 
        failed_tasks: List[Dict[str, Any]]
    ) -> int:
        """Update skill library based on task review.
        
        Args:
            successful_tasks: List of successful tasks
            failed_tasks: List of failed tasks
            
        Returns:
            Number of skills updated
        """
        from agentforge.skills.skill_registry import SkillRegistry
        
        skills_updated = 0
        
        try:
            task_types = set()
            for task in successful_tasks + failed_tasks:
                task_type = task.get("task_type")
                if task_type:
                    task_types.add(task_type)
            
            for task_type in task_types:
                type_success_tasks = [t for t in successful_tasks if t.get("task_type") == task_type]
                type_failed_tasks = [t for t in failed_tasks if t.get("task_type") == task_type]
                
                if type_success_tasks or type_failed_tasks:
                    skill_name = f"task_{task_type}"
                    skill_description = f"Skill for handling {task_type} tasks"
                    
                    success_strategies = []
                    for task in type_success_tasks[:5]:
                        if task.get("input_params"):
                            success_strategies.append({
                                "input": task.get("input_params"),
                                "output": task.get("output_data"),
                                "execution_time": task.get("execution_time_seconds")
                            })
                    
                    failure_avoidance = []
                    for task in type_failed_tasks[:5]:
                        failure_avoidance.append({
                            "issue": task.get("result"),
                            "context": task.get("input_params")
                        })
                    
                    skill_metadata = {
                        "task_type": task_type,
                        "success_count": len(type_success_tasks),
                        "failure_count": len(type_failed_tasks),
                        "success_strategies": success_strategies,
                        "failure_avoidance": failure_avoidance,
                        "last_updated": datetime.now().isoformat()
                    }
                    
                    await self.memory_store.store_memory(
                        content=f"技能优化：{skill_name} - {skill_description}",
                        memory_type="skill_update",
                        metadata=skill_metadata
                    )
                    
                    skills_updated += 1
                    logger.info(f"Updated skill library for task type: {task_type}")
            
            logger.info(f"Total skills updated: {skills_updated}")
            
        except Exception as e:
            logger.error(f"Failed to update skill library: {e}")
        
        return skills_updated
    
    async def _generate_review_report(
        self, 
        stats: Dict[str, Any], 
        success_patterns: List[Dict[str, Any]], 
        failure_lessons: List[Dict[str, Any]]
    ) -> Optional[Path]:
        """Generate a detailed review report.
        
        Args:
            stats: Review statistics
            success_patterns: List of success patterns
            failure_lessons: List of failure lessons
            
        Returns:
            Path to the generated report, or None if failed
        """
        try:
            report_date = datetime.now()
            report_filename = f"task_review_{report_date.strftime('%Y-%m-%d')}.md"
            report_path = self._report_dir / report_filename
            
            timestamp = report_date.strftime("%Y-%m-%d %H:%M:%S")
            
            content = f"""# AgentForge 任务复盘报告

**生成时间**: {timestamp}
**报告版本**: 1.0

---

## 执行摘要

本次任务复盘共分析了 **{stats['tasks_reviewed']}** 个任务，其中成功 **{stats['successful_tasks']}** 个，失败 **{stats['failed_tasks']}** 个。识别出 **{len(success_patterns)}** 个成功模式，提取 **{len(failure_lessons)}** 个经验教训，更新 **{stats['skills_updated']}** 个技能。

---

## 任务统计

### 总体统计

- **任务总数**: {stats['tasks_reviewed']}
- **成功任务**: {stats['successful_tasks']} ({stats['successful_tasks'] / max(stats['tasks_reviewed'], 1) * 100:.1f}%)
- **失败任务**: {stats['failed_tasks']} ({stats['failed_tasks'] / max(stats['tasks_reviewed'], 1) * 100:.1f}%)

### 任务类型分布

"""
            
            task_type_stats = {}
            for task in self._completed_tasks:
                task_type = task.get("task_type", "unknown")
                task_type_stats[task_type] = task_type_stats.get(task_type, 0) + 1
            
            for task_type, count in sorted(task_type_stats.items(), key=lambda x: x[1], reverse=True):
                content += f"- **{task_type}**: {count} 个任务\n"
            
            content += """
---

## 成功模式

"""
            
            for i, pattern in enumerate(success_patterns, 1):
                content += f"""### {i}. {pattern.get('pattern_name', '未知模式')}

**模式描述**: {pattern.get('description', '无详细描述')}

**适用场景**: {', '.join(pattern.get('applicable_scenarios', []))}

**关键成功因素**: {', '.join(pattern.get('key_success_factors', []))}

**推荐行动**: {', '.join(pattern.get('recommended_actions', []))}

**置信度**: {pattern.get('confidence_score', 0) * 100:.0f}%

"""
            
            content += """## 失败教训

"""
            
            for i, lesson in enumerate(failure_lessons, 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(lesson.get("priority", "medium"), "⚪")
                content += f"""### {i}. {lesson.get('lesson_title', '未知教训')} {priority_emoji}

**根本原因**: {lesson.get('root_cause', '未确定')}

**问题描述**: {lesson.get('problem_description', '无详细描述')}

**影响范围**: {lesson.get('impact', '未评估')}

**改进建议**: {', '.join(lesson.get('improvement_suggestions', []))}

**预防措施**: {', '.join(lesson.get('prevention_measures', []))}

"""
            
            content += f"""---

## 技能库更新

本次复盘更新了 **{stats['skills_updated']}** 个技能，主要包括：

"""
            
            if stats['skills_updated'] > 0:
                content += "- 优化了任务执行策略\n"
                content += "- 添加了新的成功模式\n"
                content += "- 记录了失败教训和避免方法\n"
            else:
                content += "- 暂无技能更新\n"
            
            content += f"""
---

## 改进行动计划

基于本次复盘，建议采取以下行动：

- [ ] 审查高优先级失败教训
- [ ] 实施成功模式推广计划
- [ ] 更新相关工作流程
- [ ] 安排技能培训和分享
- [ ] 跟踪改进措施执行情况

---

## 附录：详细数据

### 任务执行时间统计

"""
            
            execution_times = [t.get("execution_time_seconds") for t in self._completed_tasks if t.get("execution_time_seconds")]
            if execution_times:
                avg_time = sum(execution_times) / len(execution_times)
                min_time = min(execution_times)
                max_time = max(execution_times)
                content += f"- **平均执行时间**: {avg_time:.2f}秒\n"
                content += f"- **最短执行时间**: {min_time:.2f}秒\n"
                content += f"- **最长执行时间**: {max_time:.2f}秒\n"
            else:
                content += "- 无执行时间数据\n"
            
            content += """
---

*本报告由 AgentForge 任务复盘系统自动生成*
"""
            
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            logger.info(f"Task review report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to generate review report: {e}")
            return None
    
    async def _generate_empty_review_report(self) -> Optional[Path]:
        """Generate an empty report when no tasks found."""
        try:
            report_date = datetime.now()
            report_filename = f"task_review_{report_date.strftime('%Y-%m-%d')}.md"
            report_path = self._report_dir / report_filename
            
            content = f"""# AgentForge 任务复盘报告

**生成时间**: {report_date.strftime('%Y-%m-%d %H:%M:%S')}
**报告版本**: 1.0

---

## 执行摘要

本次任务复盘未发现任何任务记录，系统暂无可分析数据。

---

## 建议

- 确保任务完成后调用 `record_task_completion()` 方法
- 检查任务历史记录目录是否存在数据
- 等待任务积累到一定数量后再进行复盘

---

*本报告由 AgentForge 任务复盘系统自动生成*
"""
            
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            logger.info(f"Empty task review report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to generate empty report: {e}")
            return None
    
    async def trigger_task_review(self) -> Dict[str, Any]:
        """Manually trigger task review (API interface).
        
        Returns:
            Statistics about the review process
        """
        logger.info("Manual task review triggered")
        return await self.review_tasks(force=True)
    
    def get_task_review_status(self) -> Dict[str, Any]:
        """Get task review status.
        
        Returns:
            Status information including last review time and whether in progress
        """
        return {
            "last_review_time": self._last_review_time.isoformat() if self._last_review_time else None,
            "is_reviewing": self._is_reviewing,
            "pending_tasks": len(self._completed_tasks),
            "review_threshold": self.REVIEW_THRESHOLD,
            "report_dir": str(self._report_dir),
            "data_dir": str(self._data_dir)
        }
    
    def get_last_task_review_time(self) -> Optional[datetime]:
        """Get the last task review time.
        
        Returns:
            Last review datetime or None if never reviewed
        """
        return self._last_review_time
    
    async def get_task_history(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        task_type: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query task history with filters.
        
        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            task_type: Filter by task type
            success: Filter by success status
            limit: Maximum number of tasks to return
            
        Returns:
            List of task records matching the filters
        """
        tasks = await self._load_tasks_from_jsonl()
        
        filtered_tasks = []
        for task in tasks:
            if start_date:
                task_date = task.get("completed_at", "")[:10]
                if task_date < start_date:
                    continue
            
            if end_date:
                task_date = task.get("completed_at", "")[:10]
                if task_date > end_date:
                    continue
            
            if task_type and task.get("task_type") != task_type:
                continue
            
            if success is not None and task.get("success") != success:
                continue
            
            filtered_tasks.append(task)
        
        filtered_tasks.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
        
        return filtered_tasks[:limit]


class SelfEvolutionEngine:
    """Main self-evolution engine coordinating all components"""
    
    def __init__(
        self,
        memory_store: MemoryStore,
        llm_client: QianfanClient,
        report_dir: Optional[str] = None,
        data_dir: Optional[str] = None
    ):
        self.memory_store = memory_store
        self.llm_client = llm_client
        
        self.consolidator = MemoryConsolidator(memory_store, llm_client)
        self.self_checker = SelfChecker(llm_client, memory_store)
        self.task_reviewer = TaskReviewer(
            llm_client, 
            memory_store,
            report_dir=report_dir,
            data_dir=data_dir
        )
        
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the self-evolution engine"""
        if self._running:
            logger.warning("Self-evolution engine already running")
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        
        logger.info("Self-evolution engine started")
    
    async def stop(self) -> None:
        """Stop the self-evolution engine"""
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Self-evolution engine stopped")
    
    async def _run_scheduler(self) -> None:
        """Run scheduled tasks"""
        while self._running:
            try:
                now = datetime.now()
                
                if now.hour == self.consolidator.CONSOLIDATION_HOUR:
                    await self.consolidator.consolidate()
                
                if now.hour == self.self_checker.CHECK_HOUR:
                    await self.self_checker.run_self_check()
                
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(300)
    
    async def run_all(self) -> Dict[str, Any]:
        """Run all self-evolution processes manually"""
        results = {}
        
        results["consolidation"] = await self.consolidator.consolidate()
        results["self_check"] = await self.self_checker.run_self_check()
        results["task_review"] = await self.task_reviewer.review_tasks()
        
        return results
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error for self-check analysis"""
        self.self_checker.log_error(error, context)
    
    def record_task(
        self,
        task_id: str,
        task_type: str,
        description: str,
        result: str,
        success: bool
    ) -> None:
        """Record a task for review"""
        self.task_reviewer.record_task_completion(
            task_id=task_id,
            task_type=task_type,
            description=description,
            result=result,
            success=success
        )
