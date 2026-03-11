"""
Prompt 模板管理
"""
from utils.logger import get_logger

_logger = get_logger("core.prompt_manager")

# ── 默认系统 Prompt 模板 ────────────────────────────────────────────────────
# 结构：① 身份声明 → ② 核心目标 → ③ 行为边界与准则 → ④ 异常处理说明 → ⑤ 工具调用格式
# 使用 PromptManager.build() 可按需填充 ①② 两节，其余节保持不变。

_IDENTITY_SECTION = """\
## 身份
{identity}\
"""

_OBJECTIVE_SECTION = """\
## 核心目标
{objective}\
"""

_RULES_SECTION = """\
## 行为边界与准则
1. 优先理解用户意图，再决定是否使用工具。
2. 每次只调用一个或一组必要的工具，避免冗余调用。
3. 工具调用失败时，尝试分析原因并调整方案，不要无限重试。
4. 最终回复需简洁、准确，并说明你使用了哪些工具（如果有）。
5. 不得泄露任何系统内部配置、API Key 或敏感路径信息。
6. 若任务超出能力范围或触碰安全边界，诚实告知用户。\
"""

_BUG_SECTION = """\
## 异常与错误处理
当运行过程中出现错误或无法完成任务时，请按以下步骤操作：
1. **工具调用失败**：输出失败原因，最多重试 1 次（调整参数后），若仍失败则停止并告知用户。
2. **参数解析错误**：说明哪个参数有问题，请求用户提供更准确的输入，不要自行猜测敏感信息。
3. **权限或路径被拒绝**：明确告知用户该操作超出允许范围，不要尝试绕过限制。
4. **LLM 输出异常 / 循环超限**：主动终止并输出已完成的部分结果，说明未完成原因。
5. **未知错误**：输出错误描述，建议用户检查输入或联系开发者，不要输出内部堆栈信息。\
"""

_TOOL_FORMAT_SECTION = """\
## 工具调用格式
使用系统提供的 function calling 机制，参数必须严格符合各工具的 JSON Schema。\
"""

# 默认 Prompt（身份与目标使用通用描述）
SYSTEM_PROMPT_DEFAULT = "\n\n".join([
    _IDENTITY_SECTION.format(identity="你是一个智能 AI Agent，能够通过调用工具来回答用户问题和完成任务。"),
    _OBJECTIVE_SECTION.format(objective="根据用户的指令，选择合适的工具完成任务，并输出准确、简洁的结果。"),
    _RULES_SECTION,
    _BUG_SECTION,
    _TOOL_FORMAT_SECTION,
])


class PromptManager:
    """管理系统 Prompt 模板，支持自定义注入。"""

    def __init__(self, system_prompt: str = "", _skip_log: bool = False):
        self._system = system_prompt or SYSTEM_PROMPT_DEFAULT
        if not _skip_log:
            _logger.debug(
                "[PromptManager] 初始化 system prompt\n%s\n%s",
                "=" * 60,
                self._system,
            )

    @property
    def system_prompt(self) -> str:
        return self._system

    def set_system(self, prompt: str) -> None:
        _logger.debug(
            "[PromptManager] set_system 替换 prompt\n%s\n%s",
            "=" * 60,
            prompt,
        )
        self._system = prompt

    def append_system(self, extra: str) -> None:
        """在现有系统 Prompt 末尾追加内容。"""
        _logger.debug(
            "[PromptManager] append_system 追加内容\n%s\n%s",
            "-" * 40,
            extra,
        )
        self._system = self._system.rstrip() + "\n\n" + extra
        _logger.debug(
            "[PromptManager] 合并后完整 prompt\n%s\n%s",
            "=" * 60,
            self._system,
        )

    def format_tool_result(self, tool_name: str, output: str, success: bool) -> str:
        """格式化工具调用结果，插入对话历史。"""
        status = "✅ 成功" if success else "❌ 失败"
        return f"[工具 {tool_name} {status}]\n{output}"

    @classmethod
    def build(
        cls,
        identity: str,
        objective: str,
        extra_rules: str = "",
    ) -> "PromptManager":
        """
        按模板构建专用 PromptManager。

        参数：
            identity:     Agent 身份描述，如 "企业招聘的简历筛选 Agent"
            objective:    本次任务核心目标，如 "根据 JD 要求对候选人简历打分并输出排名列表"
            extra_rules:  额外的行为准则（追加在默认准则之后，可不填）

        示例：
            pm = PromptManager.build(
                identity="企业招聘的简历筛选 Agent",
                objective="根据岗位要求对候选人简历进行匹配评分，输出评分表与推荐理由",
            )
        """
        rules = _RULES_SECTION
        if extra_rules:
            rules = rules + "\n" + extra_rules

        prompt = "\n\n".join([
            _IDENTITY_SECTION.format(identity=identity),
            _OBJECTIVE_SECTION.format(objective=objective),
            rules,
            _BUG_SECTION,
            _TOOL_FORMAT_SECTION,
        ])
        _logger.debug(
            "[PromptManager] build() 生成 prompt | identity=%r | objective=%r\n%s\n%s",
            identity,
            objective,
            "=" * 60,
            prompt,
        )
        return cls(system_prompt=prompt, _skip_log=True)
