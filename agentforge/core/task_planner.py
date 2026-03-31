"""
AgentForge Task Planner Module
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SubTask(BaseModel):
    """Sub-task definition"""
    id: str
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Task(BaseModel):
    """Task definition"""
    id: str
    name: str
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    skill_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    subtasks: List[SubTask] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class TaskPlan(BaseModel):
    """Task plan containing multiple tasks"""
    id: str
    name: str
    description: str = ""
    tasks: List[Task] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: TaskStatus = TaskStatus.PENDING


class TaskPlanner:
    """Task planner for breaking down complex goals into executable tasks"""
    
    def __init__(self):
        self._plans: Dict[str, TaskPlan] = {}
        self._task_counter = 0
        self._plan_counter = 0
    
    def _generate_task_id(self) -> str:
        self._task_counter += 1
        return f"task_{self._task_counter:04d}"
    
    def _generate_plan_id(self) -> str:
        self._plan_counter += 1
        return f"plan_{self._plan_counter:04d}"
    
    async def analyze_goal(self, goal: str, context: Optional[Dict[str, Any]] = None) -> TaskPlan:
        """Analyze a goal and create a task plan"""
        logger.info(f"Analyzing goal: {goal}")
        
        plan_id = self._generate_plan_id()
        
        tasks = await self._decompose_goal(goal, context)
        
        plan = TaskPlan(
            id=plan_id,
            name=f"Plan for: {goal[:50]}",
            description=goal,
            tasks=tasks
        )
        
        self._plans[plan_id] = plan
        logger.info(f"Created plan {plan_id} with {len(tasks)} tasks")
        
        return plan
    
    async def _decompose_goal(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Decompose a goal into tasks"""
        tasks = []
        
        goal_lower = goal.lower()
        
        if "fiverr" in goal_lower or "order" in goal_lower:
            tasks.append(Task(
                id=self._generate_task_id(),
                name="Check Fiverr Orders",
                description="Retrieve and analyze Fiverr orders",
                priority=TaskPriority.HIGH,
                skill_name="fiverr_order_manager",
                parameters={"action": "list"}
            ))
        
        if "social" in goal_lower or "post" in goal_lower or "publish" in goal_lower:
            tasks.append(Task(
                id=self._generate_task_id(),
                name="Create Social Media Content",
                description="Generate content for social media",
                priority=TaskPriority.MEDIUM,
                skill_name="content_creator",
                parameters={"type": "social_post", "topic": goal}
            ))
            tasks.append(Task(
                id=self._generate_task_id(),
                name="Publish to Social Media",
                description="Publish content to social platforms",
                priority=TaskPriority.MEDIUM,
                skill_name="social_media_publisher",
                parameters={"platform": "twitter", "content": "Generated content"},
                dependencies=[tasks[-1].id]
            ))
        
        if "knowledge" in goal_lower or "document" in goal_lower:
            tasks.append(Task(
                id=self._generate_task_id(),
                name="Manage Knowledge Base",
                description="Update or search knowledge base",
                priority=TaskPriority.MEDIUM,
                skill_name="knowledge_manager",
                parameters={"action": "sync"}
            ))
        
        if "content" in goal_lower or "write" in goal_lower:
            tasks.append(Task(
                id=self._generate_task_id(),
                name="Create Content",
                description="Generate requested content",
                priority=TaskPriority.MEDIUM,
                skill_name="content_creator",
                parameters={"type": "article", "topic": goal}
            ))
        
        if not tasks:
            tasks.append(Task(
                id=self._generate_task_id(),
                name="Process Request",
                description="General task processing",
                priority=TaskPriority.MEDIUM
            ))
        
        return tasks
    
    def get_plan(self, plan_id: str) -> Optional[TaskPlan]:
        """Get a plan by ID"""
        return self._plans.get(plan_id)
    
    def get_task(self, plan_id: str, task_id: str) -> Optional[Task]:
        """Get a task from a plan"""
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        for task in plan.tasks:
            if task.id == task_id:
                return task
        return None
    
    def update_task_status(
        self,
        plan_id: str,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """Update task status"""
        task = self.get_task(plan_id, task_id)
        if not task:
            return False
        
        task.status = status
        
        if status == TaskStatus.IN_PROGRESS:
            task.started_at = datetime.now().isoformat()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            task.completed_at = datetime.now().isoformat()
        
        if result:
            task.result = result
        if error:
            task.error = error
        
        logger.info(f"Task {task_id} status updated to {status}")
        return True
    
    def get_ready_tasks(self, plan_id: str) -> List[Task]:
        """Get tasks that are ready to execute (dependencies satisfied)"""
        plan = self.get_plan(plan_id)
        if not plan:
            return []
        
        ready_tasks = []
        completed_task_ids = {
            task.id for task in plan.tasks
            if task.status == TaskStatus.COMPLETED
        }
        
        for task in plan.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            
            dependencies_met = all(
                dep_id in completed_task_ids
                for dep_id in task.dependencies
            )
            
            if dependencies_met:
                ready_tasks.append(task)
        
        return ready_tasks
    
    def get_plan_progress(self, plan_id: str) -> Dict[str, Any]:
        """Get plan progress summary"""
        plan = self.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        total = len(plan.tasks)
        completed = sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in plan.tasks if t.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for t in plan.tasks if t.status == TaskStatus.PENDING)
        failed = sum(1 for t in plan.tasks if t.status == TaskStatus.FAILED)
        
        return {
            "plan_id": plan_id,
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "failed": failed,
            "progress_percentage": (completed / total * 100) if total > 0 else 0,
            "status": plan.status
        }
    
    def list_plans(self) -> List[Dict[str, Any]]:
        """List all plans"""
        return [
            {
                "id": plan.id,
                "name": plan.name,
                "task_count": len(plan.tasks),
                "status": plan.status,
                "created_at": plan.created_at
            }
            for plan in self._plans.values()
        ]
