from core.tools.base import BaseTool
from core.agent.subagent import SubAgent
from core.agent.registry import ToolRegistry


class SpawnAgentTool(BaseTool):

    name = "spawn_agent"
    description = "Create temporary sub-agent to solve subtask"

    def __init__(self, parent_registry: ToolRegistry):
        self.parent_registry = parent_registry

    def run(self, objective: str):

        sub_registry = ToolRegistry()

        for tool in self.parent_registry._tools.values():
            sub_registry.register(tool)

        sub_agent = SubAgent(sub_registry, objective)
        result = sub_agent.run_objective()

        return f"SubAgent result:\n{result}"

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "objective": {"type": "string"}
            },
            "required": ["objective"]
        }
