import json
from core.llm.mcp_client import MCPClient
from core.llm.conversation import Conversation
from core.utils.logging import logger


SYSTEM_PROMPT = """
You are a local autonomous agent.
If a task requires shell, file, or sub-agent execution — you MUST use tools.
"""


class Agent:

    def __init__(self, registry):
        self.llm = MCPClient()
        self.registry = registry
        self.conversation = Conversation()
        self.conversation.messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })

    def clear(self):
        self.conversation = Conversation()
        self.conversation.messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })
        logger.info("Memory cleared")

    def normalize(self, text: str):
        if not text:
            return text
        return text.replace("\\n", "\n")

    def run(self, user_input: str, depth: int = 0):

        if user_input.strip() == "/clear":
            self.clear()
            return "Memory cleared."

        if depth > 5:
            return "Tool recursion limit reached."

        self.conversation.add_user(user_input)

        tools = self.registry.schemas()
        # logger.info(f"TOOLS AVAILABLE: {[t['function']['name'] for t in tools]}")

        response = self.llm.chat(
            messages=self.conversation.get(),
            tools=tools
        )

        message = response["message"]

        # logger.info(f"RAW RESPONSE: {message}")

        if "tool_calls" in message and message["tool_calls"]:
            for tool_call in message["tool_calls"]:
                function = tool_call.function if hasattr(tool_call, "function") else tool_call["function"]
                tool_name = function.name if hasattr(function, "name") else function["name"]
                arguments = function.arguments if hasattr(function, "arguments") else function["arguments"]
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)

                logger.info(f"Tool call: {tool_name} | args={arguments}")

                tool = self.registry.get(tool_name)
                result = tool.run(**arguments)
                result = self.normalize(str(result))

                logger.info(f"Tool result: {result[:200]}")

                self.conversation.add_tool(tool_name, result)

            return self.run("continue", depth + 1)

        content = self.normalize(message.get("content", ""))

        self.conversation.add_assistant(content)
        return content
