# Agent-ai-by-Andrew

基于吴恩达 Agent 系列课程学习后的实践项目，从零搭建一个具备工具调用、安全边界和可评估能力的 AI Agent 原型系统。

---

## 项目进度（2026-03-10）

### 今日完成

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
├── SETUP.md             # 构建与使用详细说明
├── AI_Agent_计划书.md   # 项目规划文档
├── config/              # 配置与安全策略
├── core/                # Agent 核心（LLM 客户端 / ReAct 循环）
├── tools/               # 工具集合
├── security/            # 安全防护
├── memory/              # 对话历史
├── utils/               # 日志与辅助函数
├── tests/               # 单元测试
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

