# Project

config.py
```python
MODEL_NAME = "ministral-3:14b"
KEEP_ALIVE = "12h"
```

main.py
```python
from core.agent.agent import Agent
from core.agent.registry import ToolRegistry

from core.tools.shell import ShellTool
from core.tools.venv import VenvTool
from core.tools.file_write import FileWriteTool
from core.tools.spawn_agent import SpawnAgentTool


SYSTEM_PROMPT = """
You are a local autonomous agent.
If a task requires shell, file, or sub-agent execution — you MUST use tools.
"""

def build_agent(system_prompt:str=None):
    registry = ToolRegistry()

    shell = ShellTool()
    registry.register(shell)
    registry.register(VenvTool(shell))
    registry.register(FileWriteTool())
    registry.register(SpawnAgentTool(registry))

    return Agent(registry, system_prompt)


if __name__ == "__main__":
    agent = build_agent(SYSTEM_PROMPT)

    while True:
        user_input = input(">>> ")
        result = agent.run(user_input)
        print(result)
```

core/agent/agent.py
```python
import json
from core.llm.mcp_client import MCPClient
from core.llm.conversation import Conversation
from core.utils.logging import logger

class Agent:
    def __init__(self, registry, system_prompt=None):
        self.llm = MCPClient()
        self.registry = registry
        self.conversation = Conversation()
        self.system_prompt = "You are a local autonomous agent, be shortly." if not system_prompt else system_prompt

        self.conversation.messages.append({"role": "system", "content": self.system_prompt})

    def clear(self):
        self.conversation = Conversation()
        self.conversation.messages.append({"role": "system", "content": self.system_prompt})
        logger.info("Memory cleared")

    def normalize(self, text: str):
        return text.replace("\\n", "\n") if text else text

    def run(self, user_input: str):
        if user_input.strip() == "/clear":
            self.clear()
            return "Memory cleared."

        self.conversation.add_user(user_input)

        response = self.llm.chat(
            messages=self.conversation.get(),
            tools=self.registry.schemas()
        )

        message = response["message"]
        usage = response["usage"]

        used = usage["prompt_tokens"] + usage["completion_tokens"]
        remaining = 8192 - used
        logger.info(f"TOKENS | used={used} remaining≈{remaining}")

        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            content = self.normalize(getattr(message, "content", ""))
            self.conversation.add_assistant(content)
            return content

        final_content = ""
        for tool_call in tool_calls:
            func = tool_call.function
            tool_name = func.name
            arguments = func.arguments
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            logger.info(f"Tool call: {tool_name} | args={arguments}")
            tool = self.registry.get(tool_name)
            result = tool.run(**arguments)
            result = self.normalize(str(result))
            logger.info(f"Tool result: {result[:200]}")

            if isinstance(result, dict) and "summary" in result:
                self.conversation.add_assistant(f"[SubAgent] {result['summary']}")
                final_content += f"[SubAgent] {result['summary']}\n"
            else:
                self.conversation.add_tool(tool_name, result)
                final_content += f"[{tool_name}] {result}\n"

        return final_content.strip()
```

core/agent/registry.py
```python
from typing import Dict
from core.tools.base import BaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        return self._tools[name]

    def schemas(self):
        return [tool.schema() for tool in self._tools.values()]
```

core/agent/subagent.py
```python
from core.agent.agent import Agent
from core.agent.task_result import TaskResult
from core.agent.registry import ToolRegistry
from core.utils.logging import logger
import json
import re

TOOL_PATTERN = re.compile(r"(\w+)\[ARGS\](\{.*\})")

class SubAgent(Agent):
    def __init__(self, parent_registry: ToolRegistry, objective: str):
        # Новый реестр без SpawnAgentTool
        sub_registry = ToolRegistry()
        for tool in parent_registry._tools.values():
            if tool.name != "spawn_agent":
                sub_registry.register(tool)

        super().__init__(sub_registry)
        self.objective = objective
        self.logger = logger  # общий логгер

    def run_objective(self) -> TaskResult:
        self.logger.info(f"[SubAgent] Начинаем выполнение задачи: {self.objective}")
        raw_result = self.run(self.objective, depth=0)
        final_result = raw_result
        artifacts = []

        # Парсим tool-вызовы в summary
        matches = TOOL_PATTERN.findall(raw_result)
        for tool_name, args_json in matches:
            try:
                args = json.loads(args_json)
                tool = self.registry.get(tool_name)
                self.logger.info(f"[SubAgent] Выполняем tool: {tool_name} с args={args}")
                tool_result = tool.run(**args)
                self.logger.info(f"[SubAgent] Результат tool {tool_name}: {tool_result}")
                final_result = f"[{tool_name}] {tool_result}"

                # Если tool создал файл, добавляем в артефакты
                if tool_name in ["write_file", "shell"]:
                    if "file" in args:
                        artifacts.append(args["file"])
                    elif "path" in args:
                        artifacts.append(args["path"])

            except Exception as e:
                final_result = f"[{tool_name} ERROR] {str(e)}"
                self.logger.error(f"[SubAgent] Ошибка tool {tool_name}: {e}")

        self.logger.info(f"[SubAgent] Задача завершена: {final_result}")
        return TaskResult(summary=final_result, artifacts=artifacts, metadata={})
```

core/agent/task_result.py
```python
from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class TaskResult:
    summary: str
    artifacts: Optional[List[str]] = None
    metadata: Optional[Dict] = None
```

core/llm/conversation.py
```python
class Conversation:
    def __init__(self):
        self.messages = []

    def add_user(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def add_tool(self, name: str, content: str):
        self.messages.append({
            "role": "tool",
            "name": name,
            "content": content
        })

    def clear(self):
        self.messages = []

    def get(self):
        return self.messages
```

core/llm/mlp_client.py
```python
import ollama
from config import MODEL_NAME, KEEP_ALIVE


class MCPClient:
    def __init__(self, model: str = MODEL_NAME):
        self.model = model

    def chat(self, messages, tools=None):
        response = ollama.chat(
            model=self.model,
            messages=messages,
            tools=tools
        )

        return {
            "message": response["message"],
            "usage": {
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0)
            }
        }
```

core/runtime/shell_session.py
```python
import subprocess
import threading
import queue
from core.runtime.workspace import Workspace

class ShellSession:
    def __init__(self):
        self.workspace = Workspace()
        self.workspace.chdir()

        self.process = subprocess.Popen(
            ["/bin/bash"],
            cwd=self.workspace.root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        self.output_queue = queue.Queue()

        def reader():
            for line in self.process.stdout:
                self.output_queue.put(line)

        threading.Thread(target=reader, daemon=True).start()

    def execute(self, command: str):
        marker = "__END__"
        self.process.stdin.write(f"{command}\necho {marker}\n")
        self.process.stdin.flush()

        output = []
        while True:
            line = self.output_queue.get()
            if marker in line:
                break
            output.append(line)
        return "".join(output)

    def close(self):
        self.process.terminate()
```

core/runtime/workspace.py
```python
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Workspace:
    def __init__(self):
        self.root = Path(os.getenv("WORKSPACE_DIR", "./workspace")).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, path: str) -> Path:
        full_path = (self.root / path).resolve()
        if not str(full_path).startswith(str(self.root)):
            raise PermissionError("Access outside workspace запрещён")
        return full_path

    def chdir(self):
        os.chdir(self.root)
```

core/tools/base.py
```python
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
```

core/tools/file_write.py
```python
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
```

core/tools/shell.py
```python
from core.tools.base import BaseTool
from core.runtime.shell_session import ShellSession


class ShellTool(BaseTool):
    name = "shell"
    description = "Run shell command in persistent session inside workspace folder"

    def __init__(self):
        self.session = ShellSession()

    def run(self, command: str):
        return self.session.execute(command)

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute in workspace folder"
                }
            },
            "required": ["command"]
        }
```

core/tools/spawn_agent.py
```python
from core.agent.subagent import SubAgent
from core.agent.registry import ToolRegistry
from core.tools.base import BaseTool

class SpawnAgentTool(BaseTool):
    name = "spawn_agent"
    description = "Create temporary sub-agent to perform a subtask in workspace"

    def __init__(self, parent_registry: ToolRegistry):
        self.parent_registry = parent_registry

    def run(self, objective: str):
        """
        Objective: short instruction for SubAgent. The SubAgent executes tools inside workspace.
        """
        sub_agent = SubAgent(self.parent_registry, objective)
        result = sub_agent.run_objective()
        return {
            "summary": result.summary,
            "artifacts": result.artifacts
        }

    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "objective": {
                    "type": "string",
                    "description": "Instruction for sub-agent, describing task to complete in workspace"
                }
            },
            "required": ["objective"]
        }
```

core/tools/venv.py
```python
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
```

core/utils/logging.py
```python
import logging
import sys


def setup_logging(level=logging.INFO):
    logger = logging.getLogger("agent")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


logger = setup_logging()
```

# Task

- Внимательно проанализируй программный код проекта локального ИИ агента
- Выяви его слабые месте, предложи (но не выполняй) план оптимизации и рефакторинга
- Предложи модификации кода, которые повысят функциональность и адаптивность агента в условиях слабого железа (мало токенов контекста, максимум 14b модели)