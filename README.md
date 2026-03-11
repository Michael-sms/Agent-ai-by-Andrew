# Agent-ai-by-Andrew

基于吴恩达 Agent 系列课程学习后的实践项目，从零搭建一个具备工具调用、安全边界和可评估能力的 AI Agent 原型系统。

---

## 项目进度

### 2026-03-11 更新

#### ✨ 新增功能：网络搜索工具（`tools/web_search.py`）
- 新增 `WebSearchTool`，Agent 可根据问题语义**自动判断**是否需要联网搜索，无需用户手动指定
- 典型触发场景：天气查询、最新新闻、实时数据、当前事件等
- 支持**双后端**，按优先级自动切换：
  - **Tavily Search API**（推荐）：专为 LLM 设计，结果质量高，免费额度注册即得
  - **DuckDuckGo Instant Answer API**（降级方案）：无需任何 Key，零配置即可运行
- 新增相关配置项：`TAVILY_API_KEY`、`SEARCH_MAX_RESULTS`（默认 5）、`SEARCH_TIMEOUT`（默认 10s）
- 已集成到 `get_default_tools()`，所有新建 Agent 实例自动具备联网搜索能力

#### 🔧 功能完善：`PromptManager` 结构化重构
- 将原有单一字符串模板拆分为 **5 个独立区段**，结构更清晰、更易维护：
  - `_IDENTITY_SECTION`：定义 Agent 身份
  - `_OBJECTIVE_SECTION`：核心目标与输出要求
  - `_RULES_SECTION`：行为边界与准则
  - `_BUG_SECTION`：异常与错误处理规则
  - `_TOOL_FORMAT_SECTION`：工具调用格式规范
- 新增 `PromptManager.build(identity, objective, extra_rules="")` 工厂类方法，一行代码构建专用 Prompt
- 新增 Prompt 变更日志（`DEBUG` 级别）：初始化、`set_system()`、`append_system()`、`build()` 均会输出完整 Prompt 内容到控制台和日志文件，方便调试与审查

#### 📄 文档完善
- `docs/SETUP.md`：
  - 补充 `PromptManager` 完整使用说明（默认用法 / `build()` / 动态修改 / 日志查看）
  - 新增 DeepSeek 最小可运行示例（可直接复制运行）
  - 新增 `web_search` 工具配置与验证说明
  - 更新模块总览表与文件结构图

---

### 2026-03-10 初版完成

#### 📋 规划阶段
- 编写 `AI_Agent_计划书.md`，明确项目架构、模型选型、工具体系、MCP 策略、安全策略及输出评估机制

#### 🏗️ 核心模块搭建
从零搭建以下模块，Python 版本 3.10.19，包管理工具 uv：

| 模块 | 文件 | 说明 |
|------|------|------|
| **配置层** | `config/settings.py` | 从 `.env` 加载全局配置（模型、路径、Token 上限等）|
| | `config/security.py` | 文件路径白名单、工具访问权限控制 |
| **工具层** | `tools/base_tool.py` | 工具抽象基类，自动导出 OpenAI function schema |
| | `tools/file_operations.py` | 文件读写，强制路径白名单校验 |
| | `tools/calculator.py` | 基于 AST 的安全数学表达式求值（拒绝 `__import__` 等危险语法）|
| | `tools/data_analysis.py` | Pandas CSV 数据分析（describe/sort/groupby 等）|
| **安全层** | `security/secrets_filter.py` | 正则过滤 API Key、JWT、Bearer Token 等敏感信息 |
| | `security/sanitizer.py` | Prompt Injection 检测、超长输入截断 |
| | `security/validator.py` | 参数类型校验、路径穿越（`..`）拦截 |
| **记忆层** | `memory/conversation.py` | 滑动窗口对话历史，支持原始 dict 消息存储 |
| **核心层** | `core/llm_client.py` | OpenAI ChatCompletion 封装，记录 Token 消耗与延迟 |
| | `core/prompt_manager.py` | 系统 Prompt 模板管理 |
| | `core/agent.py` | **ReAct 主循环**（Reasoning + Acting），逐步记录执行轨迹 |
| **工具层** | `utils/logger.py` | 统一日志格式 + 自动脱敏过滤器 |
| | `utils/helpers.py` | 截断、安全 JSON 解析等辅助函数 |
| **测试** | `tests/test_core_modules.py` | 25 个本地单元测试，无需 API Key 即可运行 |
| **入口** | `main.py` | 支持交互模式与单次提问两种运行方式 |

#### 🐛 Bug 修复
- **修复 DeepSeek/OpenAI tool call 消息格式错误**：原代码将含 `tool_calls` 的 assistant 消息错误地序列化为 JSON 字符串存入 content，导致 `tool` 角色消息找不到对应的 `tool_calls` 前置消息，API 报 400 错误。
  - `memory/conversation.py`：新增 `add_raw()` 方法，支持原始 dict 消息直接入队
  - `core/agent.py`：assistant + tool 消息均改用 `add_raw()` 写入，保证协议格式完整

#### 📦 依赖修复
- `pandas` 版本从 `>=2.3.3` 降级为 `>=2.2.0,<2.3.0`（pandas 2.3.x 最低要求 Python 3.11，当前环境为 3.10）

---

## 快速开始

```powershell
# 1. 安装依赖
uv sync

# 2. 配置 API Key
Copy-Item .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY=sk-...

# 3. 运行测试（无需 API Key）
python -m pytest tests/test_core_modules.py -v

# 4. 启动 Agent
python main.py          # 交互模式
python main.py "你的问题"  # 单次提问
```

> 使用 DeepSeek 或其他兼容 OpenAI 格式的 API，在 `.env` 中配置：
> ```
> OPENAI_BASE_URL=https://api.deepseek.com/v1
> DEFAULT_MODEL=deepseek-chat
> ```

---

## 项目结构

```
agent-ai/
├── main.py              # 入口
├── pyproject.toml       # 依赖配置
├── .env.example         # 配置模板
├── AI_Agent_计划书.md   # 项目规划文档
├── config/              # 配置与安全策略
├── core/                # Agent 核心（LLM 客户端 / ReAct 循环 / Prompt 管理）
├── tools/               # 工具集合（文件 / 计算 / 数据分析 / 网络搜索）
├── security/            # 安全防护
├── memory/              # 对话历史
├── utils/               # 日志与辅助函数
├── tests/               # 单元测试
├── docs/                # 构建与使用详细说明
└── benchmarks/          # 测试数据集
```

详细说明见 [SETUP.md](./SETUP.md)。

---

## 提交 Issue

欢迎通过 Issue 反馈问题、建议或讨论！提交前请确认以下事项：

**Bug 报告请包含：**
- Python 版本与操作系统
- 复现步骤（最小可复现代码或操作流程）
- 报错信息完整截图或日志（注意**脱敏处理**，不要粘贴 API Key）
- 期望行为与实际行为的对比

**功能建议请包含：**
- 使用场景描述
- 期望的功能效果
- 是否愿意参与实现（可选）

**提交地址**：[GitHub Issues](https://github.com/Michael-sms/Agent-ai-by-Andrew/issues)

> ⚠️ 请勿在 Issue 中粘贴任何 API Key、密码或其他敏感信息。

---

## 许可证

本项目基于 [Apache License 2.0](./LICENSE) 开源。

```
Copyright 2026 Michael-sms

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```

简而言之：允许自由使用、修改和分发，但需保留原始版权声明，且不可使用项目相关方的商标名称。

