from core.tools.base import BaseTool
from core.runtime.shell_session import ShellSession


class ShellTool(BaseTool):
    name = "shell"
    description = "Run shell command in persistent session inside workspace folder"

    def __init__(self):
        self.session = ShellSession()

    def run(self, command: str):
        return self.session.execute(command)

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute in workspace folder"
                }
            },
            "required": ["command"]
        }
