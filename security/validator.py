"""
参数校验工具
"""
from pathlib import Path
from typing import Any


def validate_string(value: Any, name: str, max_len: int = 2000) -> str:
    if not isinstance(value, str):
        raise TypeError(f"参数 '{name}' 必须是字符串，收到 {type(value).__name__}")
    if len(value) > max_len:
        raise ValueError(f"参数 '{name}' 超过最大长度 {max_len}")
    return value.strip()


def validate_path(value: Any, name: str = "path") -> str:
    value = validate_string(value, name)
    # 防止路径穿越
    if ".." in Path(value).parts:
        raise ValueError(f"参数 '{name}' 包含非法路径片段 '..'")
    return value


def validate_enum(value: Any, name: str, choices: list) -> Any:
    if value not in choices:
        raise ValueError(f"参数 '{name}' 必须是 {choices} 之一，收到 '{value}'")
    return value
