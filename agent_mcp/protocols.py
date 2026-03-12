"""
MCP 协议数据结构定义。
用于统一工具入参与出参结构，便于客户端和服务端复用。
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class CalculatorRequest(BaseModel):
    expression: str = Field(..., description="数学表达式，例如 'sqrt(256) + 3'")


class FileReadRequest(BaseModel):
    path: str = Field(..., description="要读取的文件路径（受白名单限制）")


class FileWriteRequest(BaseModel):
    path: str = Field(..., description="要写入的文件路径（受白名单限制）")
    content: str = Field(..., description="文件写入内容")


class DataAnalysisRequest(BaseModel):
    file_path: str = Field(..., description="CSV 文件路径")
    operation: str = Field(default="describe", description="分析操作，如 describe/sort/groupby")
    column: str = Field(default="", description="相关列名（按需）")
    top_n: int = Field(default=5, ge=1, le=50, description="返回条数")


class WebSearchRequest(BaseModel):
    query: str = Field(..., description="搜索关键词或自然语言问题")
    max_results: int = Field(default=5, ge=1, le=10, description="返回结果条数")


class MCPToolResponse(BaseModel):
    success: bool
    tool_name: str
    output: str
    error: str = ""
