from core.agent.subagent import SubAgent
from core.agent.registry import ToolRegistry
from core.tools.base import BaseTool

class SpawnAgentTool(BaseTool):
    name = "spawn_agent"
    description = "Create temporary sub-agent to perform a subtask in workspace"

    def __init__(self, parent_registry: ToolRegistry):
        self.parent_registry = parent_registry

    def run(self, objective: str):
        """
        Objective: short instruction for SubAgent. The SubAgent executes tools inside workspace.
        """
        sub_agent = SubAgent(self.parent_registry, objective)
        result = sub_agent.run_objective()
        return {
            "summary": result.summary,
            "artifacts": result.artifacts
        }

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "objective": {
                    "type": "string",
                    "description": "Instruction for sub-agent, describing task to complete in workspace"
                }
            },
            "required": ["objective"]
        }
