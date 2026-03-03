# AI Agent 项目计划书

> 日期：2026年3月3日
> 
> 目标：搭建一个具备工具调用能力、可扩展 MCP 集成、并具备明确安全边界的 AI Agent 原型系统。

## 1. 项目背景与目标

本项目用于学习与实践 AI Agent 技术，重点在于：
- 支持多种大模型接入与切换；
- 支持工具调用、任务分解与执行；
- 提供可扩展的 MCP 工具协议层；
- 强化安全边界，避免敏感信息泄露。

## 2. 总体架构

系统采用模块化分层结构：
- **Agent 核心层**：负责推理、任务规划、调用工具；
- **LLM 接入层**：封装不同模型的调用逻辑；
- **工具层**：统一工具接口与安全校验；
- **MCP 层**：标准化工具协议与扩展通道；
- **安全层**：输入输出清理、权限校验、敏感信息过滤；
- **记忆层（可选）**：对话历史与向量存储；
- **运维层**：日志、配置与监控。

## 3. 主体大模型选型

优先级建议：
1. **OpenAI GPT-4 / GPT-4 Turbo**（函数调用能力最佳）
2. **Claude 3.5 Sonnet**（推理能力强、上下文大）
3. **本地开源模型**（Llama 3.1 / Qwen 2.5，Ollama 部署）

通过统一 `LLM Client` 抽象，支持多模型切换与配置化管理。

## 4. 工具体系（Tools）

**必备工具**：
- 文件读写（目录白名单限制）
- 网络搜索与网页摘要
- 数学计算与表达式求值
- 数据分析（Pandas DataFrame）

**工具共性要求**：
- 参数验证
- 输入输出清理
- 调用权限限制
- 请求频率与超时控制

## 5. MCP 服务策略

**建议实现 MCP 服务**，目的：
- 标准化工具协议
- 支持第三方工具快速接入
- 支持工具热插拔和版本管理

初期可采用轻量 MCP 服务骨架，后续逐步完善工具注册与发现。

## 6. 功能边界与安全策略

**允许的能力**：
- 读取项目指定目录内文件
- 调用白名单内工具
- 访问公开互联网信息

**禁止的能力**：
- 执行系统命令
- 访问系统目录（如 `C:\Windows`）
- 输出密钥、Token、密码等敏感信息

**安全手段**：
- `.env` 存储密钥
- 敏感信息模式检测与过滤
- 日志脱敏
- 文件路径白名单

## 7. 项目文件组织结构（详细版）

```
agent-ai/
├── main.py                        # 项目入口
├── pyproject.toml                 # 依赖与版本
├── README.md                      # 使用说明
│
├── config/                        # 配置相关
│   ├── __init__.py
│   ├── settings.py                # 环境变量与模型配置
│   └── security.py                # 安全策略配置
│
├── core/                          # Agent 核心逻辑
│   ├── __init__.py
│   ├── agent.py                   # Agent 推理与调度
│   ├── llm_client.py              # LLM 客户端封装
│   └── prompt_manager.py          # Prompt 模板管理
│
├── tools/                         # 工具层
│   ├── __init__.py
│   ├── base_tool.py               # 工具基类
│   ├── file_operations.py         # 文件读写工具
│   ├── web_search.py              # 网络搜索工具
│   ├── calculator.py              # 数学计算工具
│   └── data_analysis.py           # 数据分析工具
│
├── mcp/                           # MCP 服务与协议
│   ├── __init__.py
│   ├── server.py                  # MCP Server
│   ├── client.py                  # MCP Client
│   └── protocols.py               # 协议/Schema 定义
│
├── security/                      # 安全防护层
│   ├── __init__.py
│   ├── sanitizer.py               # 输入输出清理
│   ├── validator.py               # 参数校验
│   └── secrets_filter.py          # 敏感信息过滤
│
├── memory/                        # 记忆模块（可选）
│   ├── __init__.py
│   ├── conversation.py            # 对话历史
│   └── vector_store.py            # 向量存储
│
├── utils/                         # 工具与日志
│   ├── __init__.py
│   ├── logger.py                  # 日志工具
│   └── helpers.py                 # 通用辅助函数
│
└── tests/                         # 测试用例
    ├── test_agent.py
    ├── test_tools.py
    └── test_security.py
```

## 8. 实施步骤（里程碑）

1. 搭建项目结构与依赖
2. 封装 LLM 接口与 Prompt 管理
3. 实现工具层与安全校验
4. 编写 Agent 主循环与工具路由
5. 增加 MCP 服务模块
6. 加强安全过滤与日志脱敏
7. 补齐测试与示例

## 9. 交付成果

- 可运行的 AI Agent 原型
- 多模型接入与统一接口
- 可扩展工具体系
- MCP 接入能力
- 完整安全边界方案

