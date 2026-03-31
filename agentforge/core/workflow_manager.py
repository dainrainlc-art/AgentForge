"""工作流模板市场 - 工作流加载器和管理器."""

import yaml
from pathlib import Path
from typing import Any

from loguru import logger

from agentforge.core.schemas.workflow_schema import WorkflowDefinition
from agentforge.core.workflow_engine import WorkflowEngine


class WorkflowLoader:
    """工作流加载器."""

    def __init__(self, workflows_dir: str | None = None):
        if workflows_dir is None:
            workflows_dir = Path(__file__).parent.parent / "workflows"

        self.workflows_dir = Path(workflows_dir)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def load_workflow(self, workflow_path: Path) -> WorkflowDefinition:
        """从文件加载工作流."""
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow_data = yaml.safe_load(f)

        workflow = WorkflowDefinition(**workflow_data)
        logger.info(f"加载工作流：{workflow.name} v{workflow.version}")
        return workflow

    def load_all_workflows(self) -> list[WorkflowDefinition]:
        """加载所有工作流."""
        workflows = []

        if not self.workflows_dir.exists():
            logger.warning(f"工作流目录不存在：{self.workflows_dir}")
            return workflows

        for workflow_file in self.workflows_dir.glob("*.yaml"):
            try:
                workflow = self.load_workflow(workflow_file)
                workflows.append(workflow)
            except Exception as e:
                logger.error(f"加载工作流失败 {workflow_file}: {str(e)}")

        logger.info(f"加载了 {len(workflows)} 个工作流")
        return workflows

    def save_workflow(self, workflow: WorkflowDefinition) -> Path:
        """保存工作流到文件."""
        workflow_file = self.workflows_dir / f"{workflow.name.replace(' ', '_')}.yaml"

        with open(workflow_file, "w", encoding="utf-8") as f:
            yaml.dump(
                workflow.model_dump(),
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

        logger.info(f"保存工作流：{workflow.name} -> {workflow_file}")
        return workflow_file

    def delete_workflow(self, workflow_name: str) -> bool:
        """删除工作流文件."""
        workflow_file = self.workflows_dir / f"{workflow_name.replace(' ', '_')}.yaml"

        if workflow_file.exists():
            workflow_file.unlink()
            logger.info(f"删除工作流：{workflow_name}")
            return True

        logger.warning(f"工作流文件不存在：{workflow_file}")
        return False


class WorkflowManager:
    """工作流管理器."""

    def __init__(self, workflows_dir: str | None = None):
        self._loader = WorkflowLoader(workflows_dir)
        self._engine = WorkflowEngine()
        self._workflows: dict[str, WorkflowDefinition] = {}

    async def initialize(self):
        """初始化管理器."""
        await self.load_workflows()

    async def load_workflows(self):
        """加载所有工作流."""
        workflows = self._loader.load_all_workflows()

        for workflow in workflows:
            self._workflows[workflow.name] = workflow

        logger.info(f"初始化完成，共 {len(self._workflows)} 个工作流")

    async def execute_workflow(
        self, workflow_name: str, variables: dict[str, Any] | None = None
    ):
        """执行工作流."""
        workflow = self._workflows.get(workflow_name)

        if not workflow:
            logger.error(f"工作流不存在：{workflow_name}")
            return None

        if not workflow.enabled:
            logger.error(f"工作流已禁用：{workflow_name}")
            return None

        result = await self._engine.execute_workflow(workflow, variables)
        return result

    def register_workflow(self, workflow: WorkflowDefinition, save: bool = True):
        """注册工作流."""
        self._workflows[workflow.name] = workflow

        if save:
            self._loader.save_workflow(workflow)

        logger.info(f"注册工作流：{workflow.name}")

    def unregister_workflow(self, workflow_name: str, delete: bool = False):
        """注销工作流."""
        if workflow_name in self._workflows:
            workflow = self._workflows[workflow_name]
            del self._workflows[workflow_name]

            if delete:
                self._loader.delete_workflow(workflow_name)

            logger.info(f"注销工作流：{workflow_name}")
            return True

        return False

    def get_workflow(self, workflow_name: str) -> WorkflowDefinition | None:
        """获取工作流定义."""
        return self._workflows.get(workflow_name)

    def list_workflows(
        self,
        tag: str | None = None,
        enabled: bool | None = None,
    ) -> list[WorkflowDefinition]:
        """获取工作流列表."""
        workflows = list(self._workflows.values())

        if tag is not None:
            workflows = [w for w in workflows if tag in w.tags]

        if enabled is not None:
            workflows = [w for w in workflows if w.enabled == enabled]

        return workflows

    def register_action_handler(self, action_type: str, handler):
        """注册动作处理器."""
        self._engine.register_action_handler(action_type, handler)
        logger.info(f"注册工作流动作处理器：{action_type}")
