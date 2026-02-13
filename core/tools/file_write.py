from core.tools.base import BaseTool
from core.runtime.workspace import Workspace


class FileWriteTool(BaseTool):

    name = "write_file"
    description = "Write content to file inside workspace"

    def __init__(self):
        self.workspace = Workspace()

    def run(self, path: str, content: str):
        full_path = self.workspace.resolve(path)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"File '{path}' written."

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
