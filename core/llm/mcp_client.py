import time

import ollama
from config import MODEL_NAME
from core.utils.logging import logger


class MCPClient:
    def __init__(self, model: str = MODEL_NAME, retries: int = 2, retry_delay_s: float = 1.0):
        self.model = model
        self.retries = retries
        self.retry_delay_s = retry_delay_s

    def chat(self, messages, tools=None):
        last_error = None
        for attempt in range(1, self.retries + 2):
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                )
                return {
                    "message": response["message"],
                    "usage": {
                        "prompt_tokens": response.get("prompt_eval_count", 0),
                        "completion_tokens": response.get("eval_count", 0),
                    },
                }
            except Exception as exc:
                last_error = exc
                logger.warning("LLM chat failed (attempt %s/%s): %s", attempt, self.retries + 1, exc)
                if attempt <= self.retries:
                    time.sleep(self.retry_delay_s * attempt)

        raise RuntimeError(f"LLM request failed after retries: {last_error}")
