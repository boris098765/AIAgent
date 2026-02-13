from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def parameters(self) -> Dict:
        """Return JSON schema parameters"""
        pass

    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters()
            }
        }
