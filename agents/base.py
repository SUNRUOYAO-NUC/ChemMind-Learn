from utils.llm_client import chat


class BaseAgent:
    def __init__(self, system_prompt: str):
        self._system_prompt = system_prompt
        self.conversation: list[dict] = []

    def reset(self):
        self.conversation = []

    def _call_llm(self, user_message: str, temperature: float = 0.7) -> str:
        messages = [{"role": "system", "content": self._system_prompt}] + self.conversation
        messages.append({"role": "user", "content": user_message})
        response = chat(messages, temperature=temperature)
        self.conversation.append({"role": "user", "content": user_message})
        self.conversation.append({"role": "assistant", "content": response})
        return response