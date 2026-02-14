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
