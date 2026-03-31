"""
自进化定时调度器

实现每日自动记忆巩固、自我检查和任务复盘
"""
import asyncio
from datetime import datetime, time
from typing import Optional, Callable
from loguru import logger
import aiofiles
from pathlib import Path
import json

from agentforge.config import settings


class SelfEvolutionScheduler:
    """自进化定时调度器"""
    
    def __init__(self):
        self._running = False
        self._tasks: list = []
        self._consolidation_time = time(3, 0)  # 凌晨 3 点
        self._self_check_time = time(4, 0)     # 凌晨 4 点
        self._review_time = time(23, 0)        # 晚上 11 点
        self._consolidation_task: Optional[asyncio.Task] = None
        self._self_check_task: Optional[asyncio.Task] = None
        self._review_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """启动调度器"""
        if self._running:
            logger.warning("调度器已在运行中")
            return
        
        logger.info("启动自进化调度器...")
        self._running = True
        
        # 启动定时任务
        self._consolidation_task = asyncio.create_task(
            self._run_scheduled_task(
                self._consolidation_time,
                self._memory_consolidation,
                "记忆巩固"
            )
        )
        
        self._self_check_task = asyncio.create_task(
            self._run_scheduled_task(
                self._self_check_time,
                self._self_check,
                "自我检查"
            )
        )
        
        self._review_task = asyncio.create_task(
            self._run_scheduled_task(
                self._review_time,
                self._task_review,
                "任务复盘"
            )
        )
        
        logger.info(f"调度器已启动 - 记忆巩固：{self._consolidation_time}, "
                   f"自我检查：{self._self_check_time}, 任务复盘：{self._review_time}")
    
    async def stop(self):
        """停止调度器"""
        if not self._running:
            return
        
        logger.info("停止自进化调度器...")
        self._running = False
        
        # 取消所有任务
        for task in [self._consolidation_task, self._self_check_task, self._review_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("调度器已停止")
    
    async def _run_scheduled_task(
        self,
        scheduled_time: time,
        callback: Callable,
        task_name: str
    ):
        """运行定时任务"""
        while self._running:
            try:
                now = datetime.now()
                scheduled_datetime = datetime.combine(now.date(), scheduled_time)
                
                # 如果已经过了今天的定时时间，则安排在明天
                if now.time() >= scheduled_time:
                    scheduled_datetime = scheduled_datetime.replace(
                        day=scheduled_datetime.day + 1
                    )
                
                # 计算等待时间
                wait_seconds = (scheduled_datetime - now).total_seconds()
                
                logger.debug(f"下一次{task_name}时间：{scheduled_datetime}, "
                           f"等待：{wait_seconds:.0f}秒")
                
                # 等待到定时时间
                await asyncio.sleep(wait_seconds)
                
                if not self._running:
                    break
                
                # 执行任务
                logger.info(f"开始执行{task_name}...")
                await callback()
                logger.info(f"{task_name}执行完成")
                
            except asyncio.CancelledError:
                logger.info(f"{task_name}任务被取消")
                break
            except Exception as e:
                logger.error(f"{task_name}执行失败：{e}")
                # 等待 1 分钟后重试，避免无限错误循环
                await asyncio.sleep(60)
    
    async def _memory_consolidation(self):
        """执行记忆巩固"""
        try:
            from agentforge.core.self_evolution import MemoryConsolidator
            from agentforge.memory import MemoryStore
            from agentforge.llm import QianfanClient
            
            memory_store = MemoryStore()
            llm_client = QianfanClient()
            consolidator = MemoryConsolidator(memory_store, llm_client)
            
            # 执行记忆巩固
            await consolidator.consolidate()
            
            logger.info("✅ 记忆巩固完成")
            
        except Exception as e:
            logger.error(f"❌ 记忆巩固失败：{e}")
            raise
    
    async def _self_check(self):
        """执行自我检查"""
        try:
            from agentforge.core.self_evolution import SelfChecker
            from agentforge.memory import MemoryStore
            from agentforge.llm import QianfanClient
            
            memory_store = MemoryStore()
            llm_client = QianfanClient()
            checker = SelfChecker(llm_client, memory_store)
            await checker.run_self_check()
            
            logger.info("✅ 自我检查完成")
            
        except Exception as e:
            logger.error(f"❌ 自我检查失败：{e}")
            raise
    
    async def _task_review(self):
        """执行任务复盘"""
        try:
            from agentforge.core.self_evolution import TaskReviewer
            from agentforge.memory import MemoryStore
            from agentforge.llm import QianfanClient
            
            memory_store = MemoryStore()
            llm_client = QianfanClient()
            reviewer = TaskReviewer(llm_client, memory_store)
            await reviewer.review_tasks()
            
            logger.info("✅ 任务复盘完成")
            
        except Exception as e:
            logger.error(f"❌ 任务复盘失败：{e}")
            raise
    
    def is_running(self) -> bool:
        """检查调度器是否运行中"""
        return self._running


class SelfEvolutionManager:
    """自进化管理器 - 统一管理所有自进化功能"""
    
    def __init__(self):
        self.scheduler = SelfEvolutionScheduler()
        self._initialized = False
    
    async def initialize(self):
        """初始化自进化系统"""
        if self._initialized:
            return
        
        logger.info("初始化自进化系统...")
        
        # 检查 MEMORY.md 文件
        memory_file = Path(settings.memory_file_path)
        if not memory_file.is_absolute():
            memory_file = Path(__file__).parent.parent.parent / memory_file
        
        if not memory_file.exists():
            logger.warning(f"MEMORY.md 文件不存在，创建默认文件：{memory_file}")
            await self._create_default_memory_file(memory_file)
        
        # 检查自我检查错误日志文件
        error_log = Path("logs/self_check_errors.jsonl")
        if not error_log.is_absolute():
            error_log = Path(__file__).parent.parent.parent / error_log
        
        if not error_log.parent.exists():
            error_log.parent.mkdir(parents=True, exist_ok=True)
        
        if not error_log.exists():
            async with aiofiles.open(error_log, 'w', encoding='utf-8') as f:
                await f.write("")
        
        self._initialized = True
        logger.info("自进化系统初始化完成")
    
    async def _create_default_memory_file(self, path: Path):
        """创建默认 MEMORY.md 文件"""
        content = """# AgentForge 记忆文件

**最后更新**: {date}

## 业务洞察


## 技术洞察


## 用户洞察


## 成功案例


## 失败教训


## 工作流模式


## 问题模式


## 已掌握技能


## 待优化技能

"""
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(content.format(date=datetime.now().strftime("%Y-%m-%d")))
        
        logger.info(f"已创建默认 MEMORY.md: {path}")
    
    async def start(self):
        """启动自进化系统"""
        await self.initialize()
        await self.scheduler.start()
    
    async def stop(self):
        """停止自进化系统"""
        await self.scheduler.stop()
    
    async def run_now(self, task_type: str = "all"):
        """立即运行指定任务
        
        Args:
            task_type: 任务类型 (consolidation, self_check, review, all)
        """
        if not self._initialized:
            await self.initialize()
        
        if task_type in ["consolidation", "all"]:
            logger.info("手动触发记忆巩固...")
            await self.scheduler._memory_consolidation()
        
        if task_type in ["self_check", "all"]:
            logger.info("手动触发自我检查...")
            await self.scheduler._self_check()
        
        if task_type in ["review", "all"]:
            logger.info("手动触发任务复盘...")
            await self.scheduler._task_review()
    
    def get_status(self) -> dict:
        """获取自进化系统状态"""
        return {
            "initialized": self._initialized,
            "running": self.scheduler.is_running(),
            "next_consolidation": "03:00",
            "next_self_check": "04:00",
            "next_review": "23:00"
        }


# 全局单例
_manager: Optional[SelfEvolutionManager] = None


def get_evolution_manager() -> SelfEvolutionManager:
    """获取自进化管理器单例"""
    global _manager
    if _manager is None:
        _manager = SelfEvolutionManager()
    return _manager


async def start_self_evolution():
    """启动自进化系统"""
    manager = get_evolution_manager()
    await manager.start()


async def stop_self_evolution():
    """停止自进化系统"""
    manager = get_evolution_manager()
    await manager.stop()


async def run_self_evolution_now(task_type: str = "all"):
    """立即运行自进化任务"""
    manager = get_evolution_manager()
    await manager.run_now(task_type)
