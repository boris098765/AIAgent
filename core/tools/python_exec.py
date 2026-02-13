from core.tools.base import BaseTool
import subprocess


class PythonExecTool(BaseTool):

    name = "python_exec"
    description = "Execute python code in current environment"

    def run(self, code: str):
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True
        )
        return result.stdout + result.stderr

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string"}
            },
            "required": ["code"]
        }
