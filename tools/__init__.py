from tools.base_tool import BaseTool, ToolResult
from tools.file_operations import FileReadTool, FileWriteTool
from tools.calculator import CalculatorTool
from tools.data_analysis import DataAnalysisTool

__all__ = ["BaseTool", "ToolResult", "FileReadTool", "FileWriteTool", "CalculatorTool", "DataAnalysisTool"]


def get_default_tools() -> list[BaseTool]:
    """返回默认工具集合。"""
    return [
        FileReadTool(),
        FileWriteTool(),
        CalculatorTool(),
        DataAnalysisTool(),
    ]
