"""
对话历史管理 - 维护消息列表，自动裁剪超长历史
"""
from dataclasses import dataclass, field
from typing import Literal, Union

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
    """滑动窗口对话历史，保留最近 max_turns 轮。
    
    内部存储支持两种格式：
    - Message dataclass：普通 user/assistant/tool 消息
    - dict：含 tool_calls 的 assistant 消息等需要保留完整结构的消息
    """

    def __init__(self, system_prompt: str = "", max_turns: int = 20):
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self._messages: list[Union[Message, dict]] = []

    def add(self, role: Role, content: str, **kwargs) -> None:
        """添加普通消息（user/assistant/tool）。"""
        self._messages.append(Message(role=role, content=content, **kwargs))
        self._trim()

    def add_raw(self, msg: dict) -> None:
        """直接添加原始 dict 消息，用于含 tool_calls 的 assistant 消息。"""
        self._messages.append(msg)
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
        for m in self._messages:
            if isinstance(m, dict):
                messages.append(m)
            else:
                messages.append(m.to_dict())
        return messages

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)
