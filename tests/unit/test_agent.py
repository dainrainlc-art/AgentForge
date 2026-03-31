"""
Agent 模块单元测试

测试 AgentForge 核心 Agent 相关功能，包括：
- AgentCore: 基础 Agent 功能
- EnhancedAgentCore: 增强型 Agent
- TaskPlanner: 任务规划器
- SelfEvolution: 自进化引擎
"""
import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from agentforge.core.agent import AgentCore
from agentforge.core.enhanced_agent import EnhancedAgentCore
from agentforge.core.task_planner import TaskPlanner, TaskStatus, TaskPriority
from agentforge.core.self_evolution import (
    SelfEvolutionEngine,
    MemoryConsolidator,
    SelfChecker,
    TaskReviewer
)
from agentforge.memory.memory_store import MemoryStore
from agentforge.llm.qianfan_client import QianfanClient


@pytest.fixture
def mock_memory_store():
    """创建 Mock MemoryStore"""
    store = MagicMock(spec=MemoryStore)
    store.search_memories = AsyncMock(return_value=[
        {"content": "Test memory 1", "type": "conversation"},
        {"content": "Test memory 2", "type": "learning"}
    ])
    store.store_memory = AsyncMock(return_value="memory_id_123")
    store.initialize = AsyncMock()
    return store


@pytest.fixture
def mock_llm_client():
    """创建 Mock QianfanClient"""
    client = MagicMock(spec=QianfanClient)
    client.chat = AsyncMock(return_value="This is a test response from LLM")
    client.chat_stream = AsyncMock()
    client.route_to_model = MagicMock(return_value="glm-5")
    client.health_check = AsyncMock(return_value=True)
    return client


@pytest.fixture
def agent_config():
    """Agent 测试配置"""
    return {
        "agent_id": "test_agent_001",
        "name": "TestAgent",
    }


class TestAgentCore:
    """AgentCore 基础功能测试"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试 Agent 初始化"""
        agent = AgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        assert agent.agent_id == "test_agent_001"
        assert agent.name == "TestAgent"
        assert agent.memory_store == mock_memory_store
        assert agent.llm_client == mock_llm_client
        assert agent.conversation_history == []
        assert isinstance(agent.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_agent_default_initialization(self, agent_config):
        """测试 Agent 默认初始化（自动创建依赖）"""
        agent = AgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"]
        )
        
        assert agent.agent_id == "test_agent_001"
        assert agent.name == "TestAgent"
        assert isinstance(agent.memory_store, MemoryStore)
        assert isinstance(agent.llm_client, QianfanClient)
    
    @pytest.mark.asyncio
    async def test_process_message_success(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试消息处理成功流程"""
        agent = AgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        response = await agent.process_message(
            message="Hello, how are you?",
            context={"user_id": "user_123"}
        )
        
        assert response == "This is a test response from LLM"
        assert len(agent.conversation_history) == 2
        assert agent.conversation_history[0]["role"] == "user"
        assert agent.conversation_history[0]["content"] == "Hello, how are you?"
        assert agent.conversation_history[1]["role"] == "assistant"
        
        mock_memory_store.search_memories.assert_called_once()
        mock_llm_client.chat.assert_called_once()
        mock_memory_store.store_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_with_empty_context(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试消息处理（空上下文）"""
        agent = AgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        response = await agent.process_message(
            message="Test message",
            context=None
        )
        
        assert response == "This is a test response from LLM"
        mock_llm_client.chat.assert_called_once()
        call_kwargs = mock_llm_client.chat.call_args[1]
        assert call_kwargs["context"] is None
    
    @pytest.mark.asyncio
    async def test_process_message_with_history_limit(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试消息处理（历史消息限制）"""
        agent = AgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        for i in range(15):
            await agent.process_message(f"Message {i}")
        
        assert len(agent.conversation_history) == 30
        mock_llm_client.chat.assert_called()
        last_call = mock_llm_client.chat.call_args[1]
        assert len(last_call["history"]) <= 10
    
    @pytest.mark.asyncio
    async def test_execute_skill_success(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试技能执行成功"""
        agent = AgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        result = await agent.execute_skill(
            skill_name="test_skill",
            parameters={"param1": "value1", "param2": 123}
        )
        
        assert result["skill"] == "test_skill"
        assert result["status"] == "executed"
        assert result["parameters"] == {"param1": "value1", "param2": 123}
        assert result["result"] == "Skill execution placeholder"
    
    @pytest.mark.asyncio
    async def test_execute_skill_with_empty_parameters(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试技能执行（空参数）"""
        agent = AgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        result = await agent.execute_skill(
            skill_name="empty_param_skill",
            parameters={}
        )
        
        assert result["parameters"] == {}
        assert result["status"] == "executed"
    
    @pytest.mark.asyncio
    async def test_learn_with_feedback(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试学习功能（带反馈）"""
        agent = AgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        await agent.learn(
            experience="Learned how to handle edge cases",
            feedback="This was very helpful"
        )
        
        mock_memory_store.store_memory.assert_called_once()
        call_kwargs = mock_memory_store.store_memory.call_args[1]
        assert call_kwargs["content"] == "Learned how to handle edge cases"
        assert call_kwargs["memory_type"] == "learning"
        assert call_kwargs["metadata"]["feedback"] == "This was very helpful"
    
    @pytest.mark.asyncio
    async def test_learn_without_feedback(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试学习功能（无反馈）"""
        agent = AgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        await agent.learn(experience="Simple learning")
        
        mock_memory_store.store_memory.assert_called_once()
        call_kwargs = mock_memory_store.store_memory.call_args[1]
        assert call_kwargs["metadata"] is None
    
    @pytest.mark.asyncio
    async def test_get_status(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试获取 Agent 状态"""
        agent = AgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        for i in range(3):
            await agent.process_message(f"Message {i}")
        
        status = agent.get_status()
        
        assert status["agent_id"] == "test_agent_001"
        assert status["name"] == "TestAgent"
        assert status["status"] == "active"
        assert status["conversation_count"] == 6
        assert "created_at" in status
        assert isinstance(status["created_at"], str)


class TestEnhancedAgentCore:
    """EnhancedAgentCore 增强功能测试"""
    
    @pytest.mark.asyncio
    async def test_enhanced_agent_initialization(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试增强型 Agent 初始化"""
        agent = EnhancedAgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client,
            skills=["skill1", "skill2"]
        )
        
        assert agent.agent_id == "test_agent_001"
        assert agent.name == "TestAgent"
        assert agent.skills == ["skill1", "skill2"]
        assert agent._model_preference is None
        assert isinstance(agent._evolution_engine, SelfEvolutionEngine)
    
    @pytest.mark.asyncio
    async def test_enhanced_agent_default_skills(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试增强型 Agent 默认技能列表"""
        agent = EnhancedAgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        assert agent.skills == []
    
    @pytest.mark.asyncio
    async def test_process_message_with_model_routing(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试增强型 Agent 消息处理（带模型路由）"""
        agent = EnhancedAgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        with patch("agentforge.core.enhanced_agent.model_router") as mock_router:
            mock_router.chat_with_failover = AsyncMock(
                return_value="Routed response"
            )
            
            response = await agent.process_message(
                message="Test message",
                task_type="creative"
            )
            
            assert response == "Routed response"
            mock_router.chat_with_failover.assert_called_once()
            call_kwargs = mock_router.chat_with_failover.call_args[1]
            assert call_kwargs["task_type"] == "creative"
    
    @pytest.mark.asyncio
    async def test_process_message_with_error(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试增强型 Agent 消息处理（出错情况）"""
        agent = EnhancedAgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        with patch("agentforge.core.enhanced_agent.model_router") as mock_router:
            mock_router.chat_with_failover = AsyncMock(
                side_effect=Exception("API Error")
            )
            
            with pytest.raises(Exception, match="API Error"):
                await agent.process_message(message="Test message")
    
    @pytest.mark.asyncio
    async def test_set_model_preference(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试设置模型偏好"""
        agent = EnhancedAgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        agent.set_model_preference("kimi-k2.5")
        
        assert agent._model_preference == "kimi-k2.5"
    
    @pytest.mark.asyncio
    async def test_clear_history(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试清除历史消息"""
        agent = EnhancedAgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        
        await agent.process_message("Message 1")
        await agent.process_message("Message 2")
        
        assert len(agent.conversation_history) == 4
        
        agent.clear_history()
        
        assert len(agent.conversation_history) == 0
    
    @pytest.mark.asyncio
    async def test_get_enhanced_status(
        self,
        agent_config,
        mock_memory_store,
        mock_llm_client
    ):
        """测试获取增强型 Agent 状态"""
        agent = EnhancedAgentCore(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            memory_store=mock_memory_store,
            llm_client=mock_llm_client,
            skills=["skill1"]
        )
        
        agent.set_model_preference("glm-5")
        
        status = agent.get_status()
        
        assert status["agent_id"] == "test_agent_001"
        assert status["skills"] == ["skill1"]
        assert status["model_preference"] == "glm-5"
        assert "evolution_running" in status
        assert status["status"] == "active"


class TestTaskPlanner:
    """TaskPlanner 任务规划器测试"""
    
    @pytest.fixture
    def planner(self):
        """创建 TaskPlanner 实例"""
        return TaskPlanner()
    
    @pytest.mark.asyncio
    async def test_analyze_goal_fiverr(self, planner):
        """测试分析 Fiverr 相关目标"""
        goal = "Manage Fiverr orders"
        
        plan = await planner.analyze_goal(goal)
        
        assert plan.id is not None
        assert len(plan.tasks) > 0
        assert any("Fiverr" in t.name for t in plan.tasks)
    
    @pytest.mark.asyncio
    async def test_analyze_goal_social_media(self, planner):
        """测试分析社交媒体相关目标"""
        goal = "Post to social media"
        
        plan = await planner.analyze_goal(goal)
        
        assert len(plan.tasks) >= 2
        task_names = [t.name for t in plan.tasks]
        assert any("Create Social Media Content" in name for name in task_names)
        assert any("Publish to Social Media" in name for name in task_names)
    
    @pytest.mark.asyncio
    async def test_analyze_goal_knowledge(self, planner):
        """测试分析知识库相关目标"""
        goal = "Update knowledge base documents"
        
        plan = await planner.analyze_goal(goal)
        
        assert any("Knowledge" in t.name for t in plan.tasks)
    
    @pytest.mark.asyncio
    async def test_analyze_goal_general(self, planner):
        """测试分析通用目标"""
        goal = "Do something random"
        
        plan = await planner.analyze_goal(goal)
        
        assert len(plan.tasks) > 0
        assert any("Process Request" in t.name for t in plan.tasks)
    
    @pytest.mark.asyncio
    async def test_get_plan(self, planner):
        """测试获取计划"""
        goal = "Test goal"
        plan = await planner.analyze_goal(goal)
        
        retrieved_plan = planner.get_plan(plan.id)
        
        assert retrieved_plan == plan
        assert retrieved_plan.name == plan.name
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_plan(self, planner):
        """测试获取不存在的计划"""
        plan = planner.get_plan("nonexistent_plan")
        
        assert plan is None
    
    @pytest.mark.asyncio
    async def test_get_task(self, planner):
        """测试获取任务"""
        goal = "Test goal"
        plan = await planner.analyze_goal(goal)
        
        if plan.tasks:
            task_id = plan.tasks[0].id
            task = planner.get_task(plan.id, task_id)
            
            assert task == plan.tasks[0]
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, planner):
        """测试更新任务状态"""
        goal = "Test goal"
        plan = await planner.analyze_goal(goal)
        
        task_id = plan.tasks[0].id
        
        success = planner.update_task_status(
            plan_id=plan.id,
            task_id=task_id,
            status=TaskStatus.IN_PROGRESS
        )
        
        assert success is True
        assert plan.tasks[0].status == TaskStatus.IN_PROGRESS
        assert plan.tasks[0].started_at is not None
    
    @pytest.mark.asyncio
    async def test_update_task_status_with_result(self, planner):
        """测试更新任务状态（带结果）"""
        goal = "Test goal"
        plan = await planner.analyze_goal(goal)
        
        task_id = plan.tasks[0].id
        
        planner.update_task_status(
            plan_id=plan.id,
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            result={"output": "test result"},
            error=None
        )
        
        assert plan.tasks[0].status == TaskStatus.COMPLETED
        assert plan.tasks[0].result == {"output": "test result"}
        assert plan.tasks[0].completed_at is not None
    
    @pytest.mark.asyncio
    async def test_update_task_status_with_error(self, planner):
        """测试更新任务状态（带错误）"""
        goal = "Test goal"
        plan = await planner.analyze_goal(goal)
        
        task_id = plan.tasks[0].id
        
        planner.update_task_status(
            plan_id=plan.id,
            task_id=task_id,
            status=TaskStatus.FAILED,
            error="Test error message"
        )
        
        assert plan.tasks[0].status == TaskStatus.FAILED
        assert plan.tasks[0].error == "Test error message"
    
    @pytest.mark.asyncio
    async def test_get_ready_tasks(self, planner):
        """测试获取就绪任务"""
        goal = "Test goal"
        plan = await planner.analyze_goal(goal)
        
        if len(plan.tasks) > 1:
            plan.tasks[0].status = TaskStatus.COMPLETED
            
            ready_tasks = planner.get_ready_tasks(plan.id)
            
            for task in ready_tasks:
                assert task.status == TaskStatus.PENDING
                assert all(
                    dep_id == plan.tasks[0].id
                    for dep_id in task.dependencies
                ) or len(task.dependencies) == 0
    
    @pytest.mark.asyncio
    async def test_get_plan_progress(self, planner):
        """测试获取计划进度"""
        goal = "Test goal"
        plan = await planner.analyze_goal(goal)
        
        if len(plan.tasks) >= 2:
            plan.tasks[0].status = TaskStatus.COMPLETED
            plan.tasks[1].status = TaskStatus.IN_PROGRESS
            
            progress = planner.get_plan_progress(plan.id)
            
            assert progress["plan_id"] == plan.id
            assert progress["total_tasks"] == len(plan.tasks)
            assert progress["completed"] >= 1
            assert progress["in_progress"] >= 1
            assert "progress_percentage" in progress
    
    @pytest.mark.asyncio
    async def test_list_plans(self, planner):
        """测试列出所有计划"""
        await planner.analyze_goal("Goal 1")
        await planner.analyze_goal("Goal 2")
        
        plans = planner.list_plans()
        
        assert len(plans) == 2
        for plan in plans:
            assert "id" in plan
            assert "name" in plan
            assert "task_count" in plan
            assert "status" in plan


class TestSelfEvolution:
    """自进化引擎测试"""
    
    @pytest.fixture
    def evolution_engine(self, mock_memory_store, mock_llm_client):
        """创建自进化引擎"""
        return SelfEvolutionEngine(
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
    
    @pytest.mark.asyncio
    async def test_evolution_engine_initialization(
        self,
        evolution_engine
    ):
        """测试自进化引擎初始化"""
        assert evolution_engine._running is False
        assert isinstance(evolution_engine.consolidator, MemoryConsolidator)
        assert isinstance(evolution_engine.self_checker, SelfChecker)
        assert isinstance(evolution_engine.task_reviewer, TaskReviewer)
    
    @pytest.mark.asyncio
    async def test_start_evolution(
        self,
        evolution_engine
    ):
        """测试启动自进化"""
        await evolution_engine.start()
        
        assert evolution_engine._running is True
        assert evolution_engine._scheduler_task is not None
        
        await evolution_engine.stop()
    
    @pytest.mark.asyncio
    async def test_stop_evolution(
        self,
        evolution_engine
    ):
        """测试停止自进化"""
        await evolution_engine.start()
        await evolution_engine.stop()
        
        assert evolution_engine._running is False
    
    @pytest.mark.asyncio
    async def test_log_error(
        self,
        evolution_engine
    ):
        """测试记录错误"""
        error = ValueError("Test error")
        context = {"test_key": "test_value"}
        
        evolution_engine.log_error(error, context)
        
        assert len(evolution_engine.self_checker._error_log) > 0
    
    @pytest.mark.asyncio
    async def test_record_task(
        self,
        evolution_engine
    ):
        """测试记录任务"""
        evolution_engine.record_task(
            task_id="task_001",
            task_type="test",
            description="Test task",
            result="Success",
            success=True
        )
        
        assert len(evolution_engine.task_reviewer._completed_tasks) > 0


class TestMemoryConsolidator:
    """记忆巩固器测试"""
    
    @pytest.fixture
    def consolidator(self, mock_memory_store, mock_llm_client):
        """创建记忆巩固器"""
        consolidator = MemoryConsolidator(
            memory_store=mock_memory_store,
            llm_client=mock_llm_client
        )
        consolidator._consolidation_in_progress = False
        return consolidator
    
    @pytest.mark.asyncio
    async def test_get_status(
        self,
        consolidator
    ):
        """测试获取巩固状态"""
        status = consolidator.get_status()
        
        assert "last_consolidation" in status or "in_progress" in status
        assert "memory_file_path" in status
    
    @pytest.mark.asyncio
    async def test_get_last_consolidation_time(
        self,
        consolidator
    ):
        """测试获取最后巩固时间"""
        last_time = consolidator.get_last_consolidation_time()
        
        assert last_time is None


class TestSelfChecker:
    """自检器测试"""
    
    @pytest.fixture
    def self_checker(self, mock_memory_store, mock_llm_client):
        """创建自检器"""
        return SelfChecker(
            llm_client=mock_llm_client,
            memory_store=mock_memory_store
        )
    
    @pytest.mark.asyncio
    async def test_log_error(
        self,
        self_checker
    ):
        """测试记录错误"""
        error = RuntimeError("Test runtime error")
        context = {"module": "test", "function": "test_func"}
        
        self_checker.log_error(error, context)
        
        await asyncio.sleep(0.1)
        
        assert len(self_checker._error_log) > 0
        error_data = self_checker._error_log[-1]
        assert error_data["error_type"] == "RuntimeError"
        assert "Test runtime error" in error_data["error_message"]
        assert error_data["context"] == context
    
    @pytest.mark.asyncio
    async def test_get_self_check_status(
        self,
        self_checker
    ):
        """测试获取自检状态"""
        status = self_checker.get_self_check_status()
        
        assert "last_check" in status
        assert "is_running" in status
        assert "error_log_count" in status
        assert "log_dir" in status
        assert "report_dir" in status


class TestTaskReviewer:
    """任务复盘器测试"""
    
    @pytest.fixture
    def task_reviewer(self, mock_memory_store, mock_llm_client):
        """创建任务复盘器"""
        return TaskReviewer(
            llm_client=mock_llm_client,
            memory_store=mock_memory_store
        )
    
    @pytest.mark.asyncio
    async def test_record_task_completion(
        self,
        task_reviewer
    ):
        """测试记录任务完成"""
        task_reviewer.record_task_completion(
            task_id="task_001",
            task_type="fiverr_order",
            description="Process order",
            result="Order processed successfully",
            success=True,
            input_params={"order_id": "123"},
            output_data={"status": "completed"},
            execution_time=2.5,
            resource_usage={"tokens": 100}
        )
        
        await asyncio.sleep(0.1)
        
        assert len(task_reviewer._completed_tasks) > 0
        task = task_reviewer._completed_tasks[-1]
        assert task["task_id"] == "task_001"
        assert task["task_type"] == "fiverr_order"
        assert task["success"] is True
        assert task["execution_time_seconds"] == 2.5
    
    @pytest.mark.asyncio
    async def test_get_task_review_status(
        self,
        task_reviewer
    ):
        """测试获取任务复盘状态"""
        status = task_reviewer.get_task_review_status()
        
        assert "last_review_time" in status
        assert "is_reviewing" in status
        assert "pending_tasks" in status
        assert "review_threshold" in status
        assert status["review_threshold"] == TaskReviewer.REVIEW_THRESHOLD
