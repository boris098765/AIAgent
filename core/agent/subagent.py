from core.agent.agent import Agent
from core.agent.task_result import TaskResult
from core.agent.registry import ToolRegistry
from core.utils.logging import logger


class SubAgent(Agent):
    def __init__(self, parent_registry: ToolRegistry, objective: str):
        sub_registry = parent_registry.clone(exclude=["spawn_agent"])
        super().__init__(sub_registry)
        self.objective = objective
        self.logger = logger

    def run_objective(self) -> TaskResult:
        self.logger.info(f"[SubAgent] Start objective: {self.objective}")
        final_result = self.run(self.objective)
        self.logger.info(f"[SubAgent] Finished objective: {final_result}")
        return TaskResult(summary=final_result, artifacts=[], metadata={"objective": self.objective})
