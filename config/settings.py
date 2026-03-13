"""
配置管理 - 环境变量与模型参数
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 自动加载项目根目录下的 .env
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=False)


class Settings:
    """全局配置，从环境变量读取，提供安全的默认值。"""

    # ── LLM 配置 ──────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    # ── Agent 行为 ─────────────────────────────────────────
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))  # ReAct 最大循环次数
    MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "20"))        # 保留的对话轮次

    # ── 项目路径 ───────────────────────────────────────────
    ROOT_DIR: Path = _ROOT
    DATA_DIR: Path = _ROOT / "data"
    OUTPUT_DIR: Path = _ROOT / "outputs"
    LOG_DIR: Path = _ROOT / "logs"

    # ── 日志 ───────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── 网络搜索 ───────────────────────────────────────────
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    SEARCH_MAX_RESULTS: int = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
    SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "10"))

    def validate(self) -> None:
        """启动时检查必要配置。"""
        if not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY 未设置，请在项目根目录创建 .env 文件并填写。\n"
                "示例：OPENAI_API_KEY=sk-..."
            )

    def ensure_dirs(self) -> None:
        """确保数据/输出/日志目录存在。"""
        for d in (self.DATA_DIR, self.OUTPUT_DIR, self.LOG_DIR):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
