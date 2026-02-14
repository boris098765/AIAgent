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
