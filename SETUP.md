# Agent-AI 构建说明

## 已创建模块总览

| 层级 | 文件 | 职责 |
|------|------|------|
| **config/** | `settings.py` | 从 `.env` 加载全局配置（模型、路径等）|
| | `security.py` | 文件路径白名单、工具权限控制 |
| **utils/** | `logger.py` | 统一日志 + 自动脱敏过滤器 |
| | `helpers.py` | 截断、安全 JSON 解析、计时装饰器 |
| **tools/** | `base_tool.py` | 工具抽象基类，含 OpenAI schema 导出 |
| | `file_operations.py` | 文件读写（路径白名单限制）|
| | `calculator.py` | 安全数学表达式求值（AST 沙箱）|
| | `data_analysis.py` | Pandas CSV 分析 |
| **security/** | `secrets_filter.py` | 过滤 API Key / Token / JWT |
| | `sanitizer.py` | Prompt Injection 检测、长度截断 |
| | `validator.py` | 参数类型/路径穿越校验 |
| **memory/** | `conversation.py` | 滑动窗口对话历史管理 |
| **core/** | `llm_client.py` | OpenAI ChatCompletion 封装，记录 Token/延迟 |
| | `prompt_manager.py` | 系统 Prompt 模板管理 |
| | `agent.py` | **ReAct 主循环**，逐步记录执行轨迹 |
| **tests/** | `test_core_modules.py` | 25 个本地单元测试（无需 API）|
| **根目录** | `main.py` | 交互式/单次提问入口 |
| | `.env.example` | 配置模板 |

---

## 快速上手

### 第一步：安装依赖

```powershell
pip install python-dotenv pydantic openai httpx tiktoken pytest
```

### 第二步：配置 API Key

```powershell
Copy-Item .env.example .env
```

用编辑器打开 `.env`，将 `sk-your-api-key-here` 替换为你的真实 Key：

```env
OPENAI_API_KEY=sk-你的真实Key
```

> 如使用国内代理或第三方中转接口，额外填写：
> ```env
> OPENAI_BASE_URL=https://你的代理地址/v1
> DEFAULT_MODEL=gpt-4o-mini
> ```

---

## 测试验证（无需 API Key）

运行全部单元测试，验证各核心模块是否正常：

```powershell
cd "c:\Users\Lenovo\Desktop\2526source\agent-ai"
python -m pytest tests/test_core_modules.py -v
```

测试覆盖 **25 个用例**，分 8 个模块：

| 模块 | 验证内容 |
|------|---------|
| `config/security` | 系统路径拒绝、`data/` 允许读、禁止写入 `data/` |
| `security/sanitizer` | 长度截断、Prompt Injection 检测 |
| `security/validator` | 路径穿越拒绝、枚举校验 |
| `tools/calculator` | 四则运算、sqrt、除零保护、拒绝 `__import__` |
| `tools/file_operations` | 系统路径拒绝、写入再读取 |
| `memory/conversation` | 滑动裁剪、消息格式 |
| `core/prompt_manager` | 默认 Prompt、追加内容 |
| `utils/helpers` | 截断、JSON 解析、代码块提取 |

---

## 运行 Agent（需要 API Key）

### 单次提问

```powershell
python main.py "帮我计算 sqrt(256) 是多少"
```

### 交互模式

```powershell
python main.py
```

交互模式下支持以下指令：

| 指令 | 说明 |
|------|------|
| 任意文字 | 发送给 Agent 处理 |
| `reset` | 清空对话历史，开启新会话 |
| `exit` | 退出程序 |

---

## 项目文件结构

```
agent-ai/
├── main.py                        # 项目入口
├── pyproject.toml                 # 依赖与版本
├── .env.example                   # 配置模板
├── SETUP.md                       # 本文件：构建与使用说明
├── AI_Agent_计划书.md              # 项目规划文档
│
├── config/                        # 配置层
│   ├── settings.py                # 全局配置（从 .env 加载）
│   └── security.py                # 安全策略（路径白名单等）
│
├── core/                          # Agent 核心层
│   ├── agent.py                   # ReAct 主循环
│   ├── llm_client.py              # OpenAI 调用封装
│   └── prompt_manager.py          # 系统 Prompt 管理
│
├── tools/                         # 工具层
│   ├── base_tool.py               # 工具基类
│   ├── file_operations.py         # 文件读写
│   ├── calculator.py              # 安全计算器
│   └── data_analysis.py           # Pandas 数据分析
│
├── security/                      # 安全层
│   ├── secrets_filter.py          # 敏感信息过滤
│   ├── sanitizer.py               # 输入清理 & Injection 检测
│   └── validator.py               # 参数校验
│
├── memory/                        # 记忆层
│   └── conversation.py            # 对话历史（滑动窗口）
│
├── utils/                         # 工具层
│   ├── logger.py                  # 脱敏日志
│   └── helpers.py                 # 辅助函数
│
├── tests/                         # 单元测试
│   └── test_core_modules.py       # 25 个本地测试用例
│
└── benchmarks/                    # 测试数据集
    └── test_cases.yaml            # 功能测试用例
```

---

## 常见问题

**Q: 运行测试时提示 `ModuleNotFoundError`？**  
确保在项目根目录运行，并已激活正确的 Python 环境：
```powershell
cd "c:\Users\Lenovo\Desktop\2526source\agent-ai"
python -m pytest tests/test_core_modules.py -v
```

**Q: 调用 Agent 时提示 `OPENAI_API_KEY 未设置`？**  
检查项目根目录是否存在 `.env` 文件（注意不是 `.env.example`），且其中填写了有效的 Key。

**Q: 想切换到本地 Ollama 模型？**  
在 `.env` 中配置：
```env
OPENAI_BASE_URL=http://localhost:11434/v1
DEFAULT_MODEL=llama3.1
OPENAI_API_KEY=ollama
```
