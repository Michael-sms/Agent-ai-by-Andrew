"""
工具基类 - 所有工具继承此类并实现 run()
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """工具调用结果的统一封装。"""
    success: bool
    output: Any
    error: str = ""
    tool_name: str = ""

    def to_str(self) -> str:
        if self.success:
            return str(self.output)
        return f"[工具错误] {self.error}"


class BaseTool(ABC):
    """所有工具的抽象基类。"""

    name: str = ""
    description: str = ""
    parameters: dict = field(default_factory=dict)  # JSON Schema 风格

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """执行工具逻辑，返回 ToolResult。"""
        ...

    def safe_run(self, **kwargs) -> ToolResult:
        """带异常捕获的安全执行入口。"""
        from utils.logger import get_logger
        logger = get_logger(f"tool.{self.name}")
        try:
            result = self.run(**kwargs)
            logger.info("工具 [%s] 调用成功", self.name)
            return result
        except Exception as e:
            logger.error("工具 [%s] 异常: %s", self.name, e)
            return ToolResult(success=False, output=None, error=str(e), tool_name=self.name)

    def to_openai_schema(self) -> dict:
        """导出为 OpenAI function calling 格式。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
