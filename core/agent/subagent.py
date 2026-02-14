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
