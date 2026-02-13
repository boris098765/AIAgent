from core.agent.agent import Agent
from core.agent.registry import ToolRegistry

from core.tools.shell import ShellTool
from core.tools.venv import VenvTool
from core.tools.file_write import FileWriteTool
from core.tools.python_exec import PythonExecTool
from core.tools.spawn_agent import SpawnAgentTool


def build_agent():
    registry = ToolRegistry()

    shell = ShellTool()

    registry.register(shell)
    registry.register(VenvTool(shell))
    registry.register(FileWriteTool())
    registry.register(PythonExecTool())
    registry.register(SpawnAgentTool(registry))

    return Agent(registry)



if __name__ == "__main__":
    agent = build_agent()

    while True:
        user_input = input(">>> ")
        result = agent.run(user_input)
        print(result)
