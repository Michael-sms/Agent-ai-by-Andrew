"""
输入输出清理 - 防止 Prompt Injection
"""
import re


_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+.*?instructions",
    r"你现在是(?!.*助手)",         # 角色扮演注入
    r"forget\s+your\s+instructions",
    r"act\s+as\s+(?!an?\s+assistant)",
    r"jailbreak",
    r"DAN\s+mode",
]

_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# 最大输入长度（防止超长输入消耗 Token）
MAX_INPUT_LENGTH = 4000


def sanitize_input(text: str) -> tuple[str, list[str]]:
    """
    清理用户输入。
    返回 (清理后文本, 检测到的风险列表)
    """
    warnings: list[str] = []

    # 截断
    if len(text) > MAX_INPUT_LENGTH:
        text = text[:MAX_INPUT_LENGTH]
        warnings.append(f"输入过长，已截断至 {MAX_INPUT_LENGTH} 字符。")

    # Prompt Injection 检测
    if _INJECTION_RE.search(text):
        warnings.append("检测到可能的 Prompt Injection 模式，已标记。")

    return text, warnings


def sanitize_output(text: str) -> str:
    """清理模型输出中的敏感信息。"""
    from security.secrets_filter import filter_sensitive
    return filter_sensitive(text)
