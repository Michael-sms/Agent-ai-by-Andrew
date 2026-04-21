# Agent-ai-by-Andrew

基于吴恩达 Agent 系列课程学习后的实践项目，从零搭建一个具备工具调用、安全边界和可评估能力的 AI Agent 原型系统。

---

## 项目简介

`Agent-ai-by-Andrew` 是一个面向学习与工程实践的 AI Agent 项目，支持 ReAct 推理、工具调用、安全边界控制、评测体系、MCP 接入，以及可直接使用的 Web 聊天界面。

项目核心目标：构建一个“可运行、可扩展、可评估”的 Agent 原型系统。

---

## 项目结构

```text
agent-ai/
├── main.py                    # CLI 入口（交互模式 / 单次提问）
├── pyproject.toml             # 依赖与项目配置
├── .env.example               # 环境变量模板
├── agent_mcp/                 # FastMCP 模块（server/client/protocols）
├── webapp/                    # Web UI（FastAPI + 静态前端）
│   ├── server.py
│   ├── session_store.py
│   └── static/
├── core/                      # Agent 核心（ReAct、LLM 客户端、Prompt 管理）
├── tools/                     # 工具层（文件、计算、数据分析、联网搜索）
├── security/                  # 输入输出安全、敏感信息过滤、参数校验
├── memory/                    # 对话记忆
├── config/                    # 全局配置与安全配置
├── benchmarks/                # 测试数据集
├── evaluation/                # 评估器、指标、报告
├── tests/                     # 单元测试
├── docs/                      # 详细文档
├── data/                      # 本地数据（含 Web 会话存储）
├── logs/                      # 运行日志
└── outputs/                   # 输出目录
```

---

## 项目实现功能

### 1) Agent 核心能力
- ReAct 循环（Reasoning + Acting）
- OpenAI 兼容模型调用（支持 DeepSeek 等 OpenAI 格式接口）
- 多轮对话记忆管理
- 工具自动选择与调用

### 2) 工具能力
- 文件读写（路径白名单限制）
- 安全计算器（AST 安全求值）
- CSV 数据分析（`describe` / `sort` / `groupby`）
- 网络搜索（Tavily 优先，Serper 备选）

### 3) MCP 能力（FastMCP）
- `health_check`、`list_tools`
- `ask_agent`
- `calculator`、`file_read`、`file_write`、`data_analysis`、`web_search`

### 4) Web 前端能力
- ChatGPT/Gemini 风格聊天页面
- DeepSeek 风格会话历史侧边栏
- 会话新建/切换/重命名/删除
- LLM Markdown 输出渲染（标题、列表、粗斜体、代码、链接）
- 主题三态切换：`日间` / `夜间` / `跟随系统`

### 5) 评测能力
- 基准数据集（功能、边界、回归）
- 评估器与指标聚合
- 报告输出

---

## 安装依赖

### 环境要求
- Python `>=3.10`
- 推荐使用 `uv`

### 方式一（推荐：uv）

```powershell
cd "c:\your projects catalog\agent-ai"
uv sync
```

### 方式二（pip）

```powershell
cd "c:\your projects catalog\agent-ai"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

---

## 技术栈

- **语言**：Python 3.10+
- **后端框架**：FastAPI、Uvicorn
- **MCP**：FastMCP
- **LLM SDK**：OpenAI Python SDK（兼容 OpenAI 格式服务）
- **数据处理**：Pandas、NumPy
- **配置管理**：python-dotenv、Pydantic
- **网络请求**：httpx
- **评测与测试**：PyYAML、pytest、pytest-asyncio
- **前端**：原生 HTML/CSS/JavaScript（无前端框架）

---

## 快速开始

### 1) 配置环境变量

```powershell
Copy-Item .env.example .env
```

在 `.env` 中至少配置：

```env
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
DEFAULT_MODEL=deepseek-chat
```

如需联网搜索，额外配置：

```env
TAVILY_API_KEY=tvly-xxxx
# 或者
SERPER_API_KEY=xxxx
```

### 2) CLI 模式

```powershell
python main.py
python main.py "帮我总结这个项目的能力"
```

### 3) 启动 Web 前端

```powershell
python -m webapp.server
```

浏览器访问：`http://127.0.0.1:8000`

### 4) MCP 连通性验证

```powershell
python demo_mcp_client.py
```

---

## 常见问题

### Q1：Web 页面切主题没有变化
- 先强制刷新：`Ctrl + F5`
- 确认页面使用最新静态资源（已附带版本参数）
- 若仍异常，检查浏览器是否禁用了 `localStorage`

### Q2：`ask_agent` 调用失败，提示 API Key 错误
- 检查 `.env` 中 `OPENAI_API_KEY` 是否正确
- 检查 `OPENAI_BASE_URL` 与 `DEFAULT_MODEL` 是否匹配目标服务

### Q3：搜索工具不可用
- 配置 `TAVILY_API_KEY` 或 `SERPER_API_KEY`
- 未配置时工具会返回明确错误，不会静默成功

### Q4：MCP 连接失败
- 先确保依赖已安装：`uv sync`
- 再运行：`python -m agent_mcp.server`
- 检查日志输出是否有导入错误或路径错误

### Q5：会话历史不显示或重命名无效
- 使用最新代码并刷新页面
- 检查 `data/web_sessions/sessions.json` 是否可读写

---

## 更新日志

### 2026-04-09
- 修复主题切换无视觉变化问题（强化 `html/body` 主题标记与浅色背景兜底）
- 修复会话重命名偶发无效与会话列表刷新异常
- 增加静态资源版本参数，规避浏览器缓存导致的旧代码问题

### 2026-04-08
- 新增主题三态切换：日间 / 夜间 / 跟随系统
- 前端主题偏好持久化与系统主题联动

### 2026-03-21
- 上线 Web 聊天前端（FastAPI + 原生前端）
- 新增 DeepSeek 风格会话历史侧边栏与会话持久化
- 修复 LLM Markdown 渲染问题

### 2026-03-13
- 补全 Benchmark 数据集与评估模块
- 完成 FastMCP 接入与联调
- 搜索后端切换为 Tavily + Serper

---

## 提交 Issue

欢迎提交问题与建议：

- **仓库地址**：`https://github.com/Michael-sms/Agent-ai-by-Andrew`
- **Issue 地址**：`https://github.com/Michael-sms/Agent-ai-by-Andrew/issues`

建议模板：
- 运行环境（OS、Python 版本）
- 复现步骤（尽量最小化）
- 实际行为与期望行为
- 错误日志（请脱敏，勿包含密钥）

---

## 致谢

感谢以下项目/生态提供支持：
- OpenAI Python SDK 与 OpenAI 兼容生态
- FastAPI / Uvicorn
- FastMCP 与 MCP 社区
- Pandas / NumPy / Pytest 开源社区

也感谢所有提交 Issue、反馈体验与参与改进的同学。

---

## 许可证

本项目采用 [Apache License 2.0](./LICENSE)。

