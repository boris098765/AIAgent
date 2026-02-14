from __future__ import annotations

from typing import Iterable, Optional

from core.agent.agent import Agent
from core.agent.registry import ToolRegistry
from core.tools.base import BaseTool
from core.tools.file_write import FileWriteTool
from core.tools.shell import ShellTool
from core.tools.spawn_agent import SpawnAgentTool
from core.tools.venv import VenvTool


DEFAULT_SYSTEM_PROMPT = """
You are a local autonomous agent.
If a task requires shell, file, or sub-agent execution — you MUST use tools.
""".strip()


def default_tools() -> Iterable[BaseTool]:
    shell = ShellTool()
    return [shell, VenvTool(shell), FileWriteTool()]


def build_registry(extra_tools: Optional[Iterable[BaseTool]] = None) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register_many(default_tools())
    if extra_tools:
        registry.register_many(extra_tools)
    registry.register(SpawnAgentTool(registry))
    return registry


def build_agent(system_prompt: str | None = None, extra_tools: Optional[Iterable[BaseTool]] = None) -> Agent:
    registry = build_registry(extra_tools=extra_tools)
    return Agent(registry=registry, system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT)
