from core.agent.agent import Agent
from core.agent.registry import ToolRegistry

from core.tools.shell import ShellTool
from core.tools.venv import VenvTool
from core.tools.file_write import FileWriteTool
from core.tools.spawn_agent import SpawnAgentTool


SYSTEM_PROMPT = """
You are a local autonomous agent.
If a task requires shell, file, or sub-agent execution — you MUST use tools.
"""

def build_agent(system_prompt:str=None):
    registry = ToolRegistry()

    shell = ShellTool()
    registry.register(shell)
    registry.register(VenvTool(shell))
    registry.register(FileWriteTool())
    registry.register(SpawnAgentTool(registry))

    return Agent(registry, system_prompt)


if __name__ == "__main__":
    agent = build_agent(SYSTEM_PROMPT)

    while True:
        user_input = input(">>> ")
        result = agent.run(user_input)
        print(result)
