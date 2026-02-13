from core.tools.base import BaseTool


class FileWriteTool(BaseTool):

    name = "write_file"
    description = "Write content to file"

    def run(self, path: str, content: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{path}' written successfully."

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
