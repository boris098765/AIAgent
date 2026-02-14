from __future__ import annotations

from typing import Dict, Iterable, List

from core.tools.base import BaseTool


class ToolRegistry:
    """Central tool container with helper methods for extensibility."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def register_many(self, tools: Iterable[BaseTool]) -> None:
        for tool in tools:
            self.register(tool)

    def has(self, name: str) -> bool:
        return name in self._tools

    def remove(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            available = ", ".join(sorted(self._tools))
            raise KeyError(f"Tool '{name}' is not registered. Available: {available}")
        return self._tools[name]

    def list_names(self) -> List[str]:
        return sorted(self._tools.keys())

    def schemas(self):
        return [tool.schema() for tool in self._tools.values()]

    def clone(self, *, exclude: Iterable[str] | None = None) -> "ToolRegistry":
        excluded = set(exclude or [])
        cloned = ToolRegistry()
        for name, tool in self._tools.items():
            if name not in excluded:
                cloned.register(tool)
        return cloned
