"""
日志工具 - 统一日志格式，支持日志脱敏
"""
import logging
import re
import sys
from pathlib import Path


# 敏感信息正则：匹配 OpenAI key、Bearer token、通用密码字段
_SENSITIVE_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "sk-***"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer ***"),
    (re.compile(r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*\S+"), r"\1=***"),
]


class SensitiveFilter(logging.Filter):
    """过滤日志中的敏感信息。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact(str(record.msg))
        return True


def _redact(text: str) -> str:
    for pattern, repl in _SENSITIVE_PATTERNS:
        text = pattern.sub(repl, text)
    return text


def get_logger(name: str) -> logging.Logger:
    """获取带脱敏过滤器的 Logger。"""
    from config.settings import settings

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(settings.LOG_LEVEL)
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台（使用 stderr，避免干扰 MCP stdio 协议）
    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(fmt)
    ch.addFilter(SensitiveFilter())
    logger.addHandler(ch)

    # 文件（可选）
    try:
        log_file = settings.LOG_DIR / "agent.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        fh.addFilter(SensitiveFilter())
        logger.addHandler(fh)
    except Exception:
        pass

    return logger
