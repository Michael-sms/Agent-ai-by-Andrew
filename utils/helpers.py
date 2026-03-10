"""
通用辅助函数
"""
import json
import time
from typing import Any


def truncate_text(text: str, max_len: int = 500, suffix: str = "...") -> str:
    """截断过长字符串用于日志展示。"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + suffix


def safe_json_loads(text: str, default: Any = None) -> Any:
    """安全 JSON 解析，失败时返回 default。"""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def extract_json_block(text: str) -> str:
    """从 LLM 输出中提取 ```json ... ``` 代码块。"""
    import re
    match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    # 尝试直接找 { ... }
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    return match.group(1) if match else text


def timer(func):
    """装饰器：记录函数执行时间（秒）。"""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        return result, elapsed

    return wrapper
