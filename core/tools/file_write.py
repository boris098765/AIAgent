from core.tools.base import BaseTool
from core.runtime.workspace import Workspace

class FileWriteTool(BaseTool):
    name = "write_file"
    description = "Create a file with given content in workspace"

    def __init__(self):
        self.workspace = Workspace()

    def run(self, path: str, content: str):
        full_path = self.workspace.resolve(path)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{path}' created in workspace."

    def parameters(self):
        return {
            "type":"object",
            "properties":{
                "path": {
                    "type": "string",
                    "description": "File path relative to workspace"
                },
                "content": {
                    "type": "string",
                    "description": "Text content to write into the file"
                }
            },
            "required":["path","content"]
        }
