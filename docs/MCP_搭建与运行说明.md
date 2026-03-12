# Agent-AI MCP 搭建与运行说明（FastMCP）

> 更新时间：2026-03-12  
> 目标：基于 `fastmcp` 为当前 Agent 项目提供标准 MCP Server / Client 能力，支持工具级调用与 Agent 级调用。

---

## 1. 已完成内容

本次已按计划书落地 `agent_mcp/` 模块（避免与官方 `mcp` SDK 包名冲突）：

```
agent_mcp/
├── __init__.py      # MCP 模块导出（默认导出客户端）
├── protocols.py     # MCP 请求/响应协议模型（Pydantic）
├── server.py        # FastMCP 服务端：工具暴露 + ask_agent
└── client.py        # FastMCP 客户端封装（async）
```

并更新依赖：
- `pyproject.toml` 新增：`fastmcp>=2.0.0`

---

## 2. MCP 服务能力（具体功能）

`agent_mcp/server.py` 中通过 `FastMCP("Agent-AI MCP Server")` 暴露如下工具：

### 基础能力

1. `health_check()`
- 功能：检查 MCP 服务是否可用
- 返回：`{"status": "ok", "service": "agent-ai-mcp"}`

2. `list_tools()`
- 功能：列出当前 MCP Server 可用工具
- 返回：工具名数组

### Agent 级能力

3. `ask_agent(question: str)`
- 功能：把自然语言问题交给现有 `core.Agent` 执行
- 特点：Agent 会自动判断是否调用 `calculator/file_read/file_write/data_analysis/web_search`
- 返回：
  - `answer`
  - `steps`
  - `total_tool_calls`
  - `total_input_tokens` / `total_output_tokens`
  - `total_latency`
  - `trace`（每一步工具调用轨迹）

### 工具级能力（直连调用）

4. `calculator(expression: str)`
- 功能：安全数学计算（AST 沙箱）

5. `file_read(path: str)`
- 功能：读取文件（路径白名单限制）

6. `file_write(path: str, content: str)`
- 功能：写文件（路径白名单限制）

7. `data_analysis(file_path: str, operation="describe", column="", top_n=5)`
- 功能：CSV 分析（describe/sort/groupby 等）

8. `web_search(query: str, max_results=5)`
- 功能：联网搜索（优先 Tavily，未配置 Key 时自动降级 DuckDuckGo）

---

## 3. 协议与安全说明

### 协议模型

`agent_mcp/protocols.py` 提供请求模型与统一响应模型：
- `CalculatorRequest`
- `FileReadRequest`
- `FileWriteRequest`
- `DataAnalysisRequest`
- `WebSearchRequest`
- `MCPToolResponse`

其中统一响应结构：

```json
{
  "success": true,
  "tool_name": "calculator",
  "output": "16",
  "error": ""
}
```

### 安全边界

MCP 工具层复用项目已有安全策略：
- 文件访问白名单（拒绝系统目录与路径穿越）
- 输入输出清理与敏感信息过滤
- 工具异常安全兜底（`safe_run`）

`ask_agent` 采用懒加载 Agent：
- 启动 MCP Server 不会立即初始化 LLM
- 首次调用 `ask_agent` 时才检查 `OPENAI_API_KEY`

---

## 4. 如何运行 MCP 服务器（Windows / PowerShell）

### 第一步：安装依赖

```powershell
cd "c:\Users\Lenovo\Desktop\2526source\agent-ai"
uv sync
```

### 第二步：准备环境变量

```powershell
Copy-Item .env.example .env
```

至少配置：

```env
OPENAI_API_KEY=sk-你的Key
OPENAI_BASE_URL=https://api.deepseek.com/v1
DEFAULT_MODEL=deepseek-chat
```

> 说明：仅调用 `calculator/file_read` 等直连工具时，不一定需要 LLM Key；调用 `ask_agent` 必须有有效 Key。

### 第三步：启动 MCP Server

```powershell
cd "c:\Users\Lenovo\Desktop\2526source\agent-ai"
python -m agent_mcp.server
```

启动后即为 `stdio` 模式，可被支持 MCP 的客户端直接拉起与调用。

---

## 5. 客户端调用示例（本项目自带）

`agent_mcp/client.py` 提供 `MCPAgentClient`，可用于本地异步调试：

```python
import asyncio
from agent_mcp.client import MCPAgentClient

async def main():
    async with MCPAgentClient() as client:
        print(await client.health_check())
        print(await client.list_tools())
        print(await client.calculator("sqrt(144) + 6"))
        print(await client.ask_agent("今天北京天气怎么样？"))

asyncio.run(main())
```

默认连接方式：
- `agent_mcp/server.py`（FastMCP 自动识别为本地脚本并以 stdio 方式连接）

你也可以在初始化时传入其他 MCP server 地址：

```python
MCPAgentClient(server="https://your-mcp-server.example.com/mcp")
```

---

## 6. 典型联调流程（建议）

1. 先跑 `health_check` 与 `list_tools`，确认服务可达
2. 再跑直连工具（如 `calculator`）确认工具链正常
3. 最后跑 `ask_agent` 验证 Agent + 工具自动路由
4. 若失败，查看 `logs/agent.log`

---

## 7. 常见问题

### Q1：启动时报 `No module named fastmcp`
请先执行：

```powershell
uv sync
```

### Q2：`ask_agent` 返回 key 未配置错误
请检查 `.env` 中是否存在：
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `DEFAULT_MODEL`

### Q3：`file_read` 读取系统目录失败
这是预期行为，项目有白名单安全策略，禁止访问系统路径。

---

## 8. 后续可扩展方向

- 增加 MCP `resources`（如日志、报告、配置快照）
- 增加 MCP `prompts` 模板下发能力
- 增加 SSE / HTTP Transport 部署模式
- 与 `evaluation/` 联动，暴露 benchmark 运行与报告查询工具
