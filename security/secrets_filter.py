"""
敏感信息过滤 - 检测并屏蔽输出中的 API Key、Token 等
"""
import re

_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "[REDACTED-OPENAI-KEY]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED-AWS-KEY]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer [REDACTED-TOKEN]"),
    (re.compile(r"(?i)(password|passwd|secret|api[_-]?key)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"), "[REDACTED-JWT]"),  # JWT
]


def filter_sensitive(text: str) -> str:
    """将字符串中的敏感信息替换为占位符。"""
    for pattern, repl in _PATTERNS:
        text = pattern.sub(repl, text)
    return text


def contains_sensitive(text: str) -> bool:
    """判断字符串是否包含敏感信息。"""
    for pattern, _ in _PATTERNS:
        if pattern.search(text):
            return True
    return False
