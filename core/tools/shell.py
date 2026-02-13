from core.tools.base import BaseTool
from core.runtime.shell_session import ShellSession


class ShellTool(BaseTool):
    name = "shell"
    description = "Execute command in persistent shell session"

    def __init__(self):
        self.session = ShellSession()

    def run(self, command: str):
        return self.session.execute(command)

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string"}
            },
            "required": ["command"]
        }
