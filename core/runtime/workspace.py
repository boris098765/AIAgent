import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Workspace:
    def __init__(self):
        self.root = Path(os.getenv("WORKSPACE_DIR")).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, path: str) -> Path:
        full_path = (self.root / path).resolve()

        if not str(full_path).startswith(str(self.root)):
            raise PermissionError("Access outside workspace запрещён.")

        return full_path

    def chdir(self):
        os.chdir(self.root)
