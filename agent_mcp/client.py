"""
FastMCP 客户端封装（用于本地调试/集成测试）。
"""
from __future__ import annotations

from typing import Any

from fastmcp import Client


class MCPAgentClient:
    """Agent-AI MCP 客户端。"""

    def __init__(self, server: str = "agent_mcp/server.py") -> None:
        self.server = server
        self._client: Client | None = None

    async def __aenter__(self) -> "MCPAgentClient":
        self._client = Client(self.server)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.__aexit__(exc_type, exc, tb)
            self._client = None

    async def _call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        if self._client is None:
            raise RuntimeError("MCP 客户端未连接，请使用 'async with MCPAgentClient()'。")
        result = await self._client.call_tool(name=name, arguments=arguments or {})
        if hasattr(result, "data"):
            return result.data
        return result

    async def health_check(self) -> Any:
        return await self._call("health_check")

    async def list_tools(self) -> Any:
        return await self._call("list_tools")

    async def ask_agent(self, question: str) -> Any:
        return await self._call("ask_agent", {"question": question})

    async def calculator(self, expression: str) -> Any:
        return await self._call("calculator", {"expression": expression})

    async def file_read(self, path: str) -> Any:
        return await self._call("file_read", {"path": path})

    async def file_write(self, path: str, content: str) -> Any:
        return await self._call("file_write", {"path": path, "content": content})

    async def data_analysis(
        self,
        file_path: str,
        operation: str = "describe",
        column: str = "",
        top_n: int = 5,
    ) -> Any:
        payload = {
            "file_path": file_path,
            "operation": operation,
            "top_n": top_n,
        }
        if column:
            payload["column"] = column
        return await self._call("data_analysis", payload)

    async def web_search(self, query: str, max_results: int = 5) -> Any:
        return await self._call("web_search", {"query": query, "max_results": max_results})
