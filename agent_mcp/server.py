"""
FastMCP 服务端实现。

暴露能力：
- health_check：健康检查
- ask_agent：调用完整 Agent 执行自然语言请求
- calculator/file_read/file_write/data_analysis/web_search：直连工具调用

启动方式（stdio）：
    python -m agent_mcp.server
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# 兼容以脚本方式启动（例如 Client("agent_mcp/server.py")）
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastmcp import FastMCP

from config.settings import settings
from core import Agent
from tools import (
    CalculatorTool,
    DataAnalysisTool,
    FileReadTool,
    FileWriteTool,
    WebSearchTool,
    get_default_tools,
)
from tools.base_tool import ToolResult
from utils.logger import get_logger

from agent_mcp.protocols import MCPToolResponse

logger = get_logger("agent_mcp.server")

mcp = FastMCP("Agent-AI MCP Server")

# 懒加载 Agent，避免在模块导入阶段触发 LLM 初始化
_AGENT: Agent | None = None
_TOOLS = {
    "calculator": CalculatorTool(),
    "file_read": FileReadTool(),
    "file_write": FileWriteTool(),
    "data_analysis": DataAnalysisTool(),
    "web_search": WebSearchTool(),
}


def _to_response(result: ToolResult) -> dict[str, Any]:
    payload = MCPToolResponse(
        success=result.success,
        tool_name=result.tool_name,
        output=str(result.output) if result.output is not None else "",
        error=result.error,
    )
    return payload.model_dump()


def _get_agent() -> Agent:
    global _AGENT
    if _AGENT is None:
        settings.validate()
        settings.ensure_dirs()
        _AGENT = Agent(tools=get_default_tools())
    return _AGENT


@mcp.tool
def health_check() -> dict[str, str]:
    """检查 MCP 服务是否可用。"""
    return {"status": "ok", "service": "agent-ai-mcp"}


@mcp.tool
def ask_agent(question: str) -> dict[str, Any]:
    """
    让 Agent 处理一个自然语言问题。

    Agent 会自行决定是否调用工具。
    返回最终答案、执行步数、工具调用次数、token 与延迟等摘要信息。
    """
    logger.info("MCP ask_agent 收到请求: %s", question[:120])
    try:
        result = _get_agent().run(question)
    except Exception as e:
        return {
            "success": False,
            "answer": "",
            "error": f"ask_agent 调用失败: {e}",
            "steps": 0,
            "total_tool_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_latency": 0.0,
            "trace": [],
        }
    return {
        "success": result.success,
        "answer": result.answer,
        "error": result.error,
        "steps": len(result.steps),
        "total_tool_calls": result.total_tool_calls,
        "total_input_tokens": result.total_input_tokens,
        "total_output_tokens": result.total_output_tokens,
        "total_latency": result.total_latency,
        "trace": [
            {
                "iteration": s.iteration,
                "tool_name": s.tool_name,
                "tool_args": s.tool_args,
                "tool_result": s.tool_result,
                "final_answer": s.final_answer,
            }
            for s in result.steps
        ],
    }


@mcp.tool
def calculator(expression: str) -> dict[str, Any]:
    """安全数学计算。"""
    result = _TOOLS["calculator"].safe_run(expression=expression)
    return _to_response(result)


@mcp.tool
def file_read(path: str) -> dict[str, Any]:
    """读取文件（路径白名单限制）。"""
    result = _TOOLS["file_read"].safe_run(path=path)
    return _to_response(result)


@mcp.tool
def file_write(path: str, content: str) -> dict[str, Any]:
    """写入文件（路径白名单限制）。"""
    result = _TOOLS["file_write"].safe_run(path=path, content=content)
    return _to_response(result)


@mcp.tool
def data_analysis(file_path: str, operation: str = "describe", column: str = "", top_n: int = 5) -> dict[str, Any]:
    """CSV 数据分析（describe/sort/groupby 等）。"""
    kwargs: dict[str, Any] = {
        "file_path": file_path,
        "operation": operation,
        "top_n": top_n,
    }
    if column:
        kwargs["column"] = column
    result = _TOOLS["data_analysis"].safe_run(**kwargs)
    return _to_response(result)


@mcp.tool
def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """联网搜索（Tavily 或 DuckDuckGo）。"""
    result = _TOOLS["web_search"].safe_run(query=query, max_results=max_results)
    return _to_response(result)


@mcp.tool
def list_tools() -> dict[str, Any]:
    """返回当前 MCP server 暴露的工具名称。"""
    return {"tools": sorted(list(_TOOLS.keys()) + ["ask_agent", "health_check", "list_tools"])}


def run_server() -> None:
    """启动 FastMCP 服务（默认 stdio 传输）。"""
    logger.info("启动 FastMCP 服务: Agent-AI MCP Server")
    mcp.run()


if __name__ == "__main__":
    run_server()
