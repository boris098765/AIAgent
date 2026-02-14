from __future__ import annotations

import json
from typing import Any, Dict, List

from core.llm.conversation import Conversation
from core.llm.mcp_client import MCPClient
from core.utils.logging import logger


class Agent:
    def __init__(
        self,
        registry,
        system_prompt=None,
        llm_client: MCPClient | None = None,
        max_steps: int = 6,
        max_tool_output_chars: int = 4000,
    ):
        self.llm = llm_client or MCPClient()
        self.registry = registry
        self.conversation = Conversation()
        self.system_prompt = (
            "You are a local autonomous agent, be shortly." if not system_prompt else system_prompt
        )
        self.max_steps = max_steps
        self.max_tool_output_chars = max_tool_output_chars
        self.conversation.add_system(self.system_prompt)

    def clear(self):
        self.conversation = Conversation()
        self.conversation.add_system(self.system_prompt)
        logger.info("Memory cleared")

    @staticmethod
    def normalize(text: str):
        return text.replace("\\n", "\n") if text else text

    @staticmethod
    def _extract_message_content(message: Any) -> str:
        if isinstance(message, dict):
            return message.get("content", "")
        return getattr(message, "content", "")

    @staticmethod
    def _extract_tool_calls(message: Any) -> List[Any]:
        if isinstance(message, dict):
            return message.get("tool_calls") or []
        return getattr(message, "tool_calls", None) or []

    @staticmethod
    def _extract_tool_parts(tool_call: Any):
        if isinstance(tool_call, dict):
            func = tool_call.get("function", {})
            return func.get("name"), func.get("arguments")

        func = tool_call.function
        return func.name, func.arguments

    def _limit_tool_output(self, text: str) -> str:
        if len(text) <= self.max_tool_output_chars:
            return text
        truncated = len(text) - self.max_tool_output_chars
        return f"{text[:self.max_tool_output_chars]}\n...[truncated {truncated} chars]"

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
        logger.info(f"Tool call: {tool_name} | args={arguments}")
        tool = self.registry.get(tool_name)
        result = tool.run(**arguments)
        normalized = self._limit_tool_output(self.normalize(str(result)))
        logger.info(f"Tool result: {normalized[:200]}")
        return result, normalized

    def run(self, user_input: str):
        if user_input.strip() == "/clear":
            self.clear()
            return "Memory cleared."

        self.conversation.add_user(user_input)

        final_chunks: List[str] = []
        for _ in range(self.max_steps):
            try:
                response = self.llm.chat(messages=self.conversation.get(), tools=self.registry.schemas())
            except Exception as exc:
                logger.error("LLM call failed: %s", exc)
                final_chunks.append(f"[error] LLM unavailable: {exc}")
                break

            message = response["message"]
            usage = response["usage"]

            used = usage["prompt_tokens"] + usage["completion_tokens"]
            remaining = 8192 - used
            logger.info(f"TOKENS | used={used} remaining≈{remaining}")

            content = self.normalize(self._extract_message_content(message))
            tool_calls = self._extract_tool_calls(message)

            if content:
                self.conversation.add_assistant(content)
                final_chunks.append(content)

            if not tool_calls:
                break

            for tool_call in tool_calls:
                try:
                    tool_name, arguments = self._extract_tool_parts(tool_call)
                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)
                    arguments = arguments or {}
                    raw_result, normalized_result = self._execute_tool(tool_name, arguments)
                except Exception as exc:
                    logger.exception("Tool execution failed")
                    normalized_result = f"[tool error] {exc}"
                    tool_name = tool_name if 'tool_name' in locals() else "unknown_tool"
                    raw_result = normalized_result

                if isinstance(raw_result, dict) and "summary" in raw_result:
                    summary = f"[SubAgent] {raw_result['summary']}"
                    self.conversation.add_assistant(summary)
                    final_chunks.append(summary)
                    continue

                self.conversation.add_tool(tool_name, normalized_result)
                final_chunks.append(f"[{tool_name}] {normalized_result}")
        else:
            final_chunks.append("[warning] max reasoning steps reached")

        return "\n".join(chunk for chunk in final_chunks if chunk).strip()
