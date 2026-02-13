from core.tools.base import BaseTool


class VenvTool(BaseTool):

    name = "create_venv"
    description = "Create and activate Python virtual environment"

    def __init__(self, shell_tool):
        self.shell = shell_tool

    def run(self, path: str = "venv"):
        self.shell.run(f"python3 -m venv {path}")
        self.shell.run(f"source {path}/bin/activate")
        return f"Virtual environment '{path}' created and activated."

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            }
        }
