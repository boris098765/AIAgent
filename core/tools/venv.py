from core.tools.base import BaseTool

class VenvTool(BaseTool):
    name = "create_venv"
    description = "Create Python virtual environment in workspace"

    def __init__(self, shell_tool):
        self.shell = shell_tool

    def run(self, path="venv"):
        self.shell.run(f"python3 -m venv {path}")
        return f"Virtual environment '{path}' created in workspace."

    def parameters(self):
        return {
            "type":"object",
            "properties":{
                "path": {
                    "type": "string",
                    "description": "Path to create the virtual environment relative to workspace"
                }
            },
            "required":["path"]
        }
