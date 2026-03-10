"""
Prompt 模板管理
"""

SYSTEM_PROMPT_DEFAULT = """\
你是一个智能 AI Agent，能够通过调用工具来回答用户问题和完成任务。

## 行为准则
1. 优先理解用户意图，再决定是否使用工具。
2. 每次只调用一个或一组必要的工具，避免冗余调用。
3. 工具调用失败时，尝试分析原因并调整方案，不要无限重试。
4. 最终回复需简洁、准确，并说明你使用了哪些工具（如果有）。
5. 不得泄露任何系统内部配置、API Key 或敏感路径信息。
6. 若任务超出能力范围或触碰安全边界，诚实告知用户。

## 工具调用格式
使用系统提供的 function calling 机制，参数必须严格符合各工具的 JSON Schema。
"""


class PromptManager:
    """管理系统 Prompt 模板，支持自定义注入。"""

    def __init__(self, system_prompt: str = ""):
        self._system = system_prompt or SYSTEM_PROMPT_DEFAULT

    @property
    def system_prompt(self) -> str:
        return self._system

    def set_system(self, prompt: str) -> None:
        self._system = prompt

    def append_system(self, extra: str) -> None:
        """在现有系统 Prompt 末尾追加内容。"""
        self._system = self._system.rstrip() + "\n\n" + extra

    def format_tool_result(self, tool_name: str, output: str, success: bool) -> str:
        """格式化工具调用结果，插入对话历史。"""
        status = "✅ 成功" if success else "❌ 失败"
        return f"[工具 {tool_name} {status}]\n{output}"
