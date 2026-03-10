"""
对话历史管理 - 维护消息列表，自动裁剪超长历史
"""
from dataclasses import dataclass, field
from typing import Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class Message:
    role: Role
    content: str
    tool_name: str = ""
    tool_call_id: str = ""

    def to_dict(self) -> dict:
        d: dict = {"role": self.role, "content": self.content}
        if self.role == "tool":
            d["tool_call_id"] = self.tool_call_id
            d["name"] = self.tool_name
        return d


class ConversationMemory:
    """滑动窗口对话历史，保留最近 max_turns 轮。"""

    def __init__(self, system_prompt: str = "", max_turns: int = 20):
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self._messages: list[Message] = []

    def add(self, role: Role, content: str, **kwargs) -> None:
        self._messages.append(Message(role=role, content=content, **kwargs))
        self._trim()

    def _trim(self) -> None:
        # 保留 system prompt，其余按轮次裁剪
        if len(self._messages) > self.max_turns * 2:
            self._messages = self._messages[-(self.max_turns * 2):]

    def to_openai_messages(self) -> list[dict]:
        """构造 OpenAI messages 列表（包含 system）。"""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(m.to_dict() for m in self._messages)
        return messages

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)
