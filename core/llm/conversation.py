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
