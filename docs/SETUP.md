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
| | `web_search.py` | 网络搜索（Tavily / DuckDuckGo 双后端）|
| **security/** | `secrets_filter.py` | 过滤 API Key / Token / JWT |
| | `sanitizer.py` | Prompt Injection 检测、长度截断 |
| | `validator.py` | 参数类型/路径穿越校验 |
| **memory/** | `conversation.py` | 滑动窗口对话历史管理 |
| **core/** | `llm_client.py` | OpenAI ChatCompletion 封装，记录 Token/延迟 |
| | `prompt_manager.py` | 系统 Prompt 模板管理 |
| | `agent.py` | **ReAct 主循环**，逐步记录执行轨迹 |
| **tests/** | `test_core_modules.py` | 25 个本地单元测试（无需 API）|
| **evaluation/** | `evaluator.py` | 按 YAML 测试套件驱动 Agent，自动判断结果 |
| | `metrics.py` | 汇总通过率、延迟、Token 等指标 |
| | `reporter.py` | 控制台输出 + 生成 Markdown 报告 |
| **benchmarks/** | `test_cases.yaml` | 功能测试用例（各工具正常场景）|
| | `edge_cases.yaml` | 边界测试用例（安全拦截、异常输入）|
| | `regression_suite.yaml` | 回归测试套件（历史 Bug + 冒烟测试）|
| | `run_benchmark.py` | 基准测试命令行入口 |
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
│   ├── data_analysis.py           # Pandas 数据分析
│   └── web_search.py              # 网络搜索（Tavily/DuckDuckGo）
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

## Prompt 模版管理器使用说明

`core/prompt_manager.py` 已升级为结构化模板，包含：
- 身份（你是谁）
- 核心目标（要完成什么、输出什么）
- 行为边界与准则
- 异常与错误处理（Bug 时如何操作）
- 工具调用格式

### 1）默认使用（无需改代码）

直接创建 `Agent` 时，会自动加载默认模板：

```python
from core import Agent

agent = Agent()
```

### 2）构建专用 Prompt（推荐）

使用 `PromptManager.build()` 指定身份与任务目标：

```python
from core import Agent
from core.prompt_manager import PromptManager

pm = PromptManager.build(
    identity="企业招聘的简历筛选 Agent",
    objective="根据岗位要求对候选人简历进行匹配评分，输出评分表与推荐理由",
    extra_rules="输出结果必须包含：候选人姓名、匹配分数、三条推荐理由。",
)

agent = Agent(prompt_manager=pm)
```

### 3）运行中动态修改 Prompt

```python
from core.prompt_manager import PromptManager

pm = PromptManager()
pm.set_system("你的完整 system prompt")
pm.append_system("\n补充规则：禁止输出候选人手机号")
```

### 4）查看“生成后的 Prompt”日志

`PromptManager` 已在以下场景输出完整 Prompt 日志：
- 初始化 `PromptManager()`
- 调用 `PromptManager.build(...)`
- 调用 `set_system(...)`
- 调用 `append_system(...)`

要看到这些日志，请在 `.env` 中设置：

```env
LOG_LEVEL=DEBUG
```

然后运行程序，查看控制台或 `logs/agent.log`。

### 5）DeepSeek 最小可运行示例（可直接复制）

先在 `.env` 中配置（DeepSeek 走 OpenAI 兼容接口）：

```env
OPENAI_API_KEY=sk-你的DeepSeekKey
OPENAI_BASE_URL=https://api.deepseek.com/v1
DEFAULT_MODEL=deepseek-chat
LOG_LEVEL=DEBUG
```

然后在项目根目录新建并运行以下代码（示例中会打印当前生效 Prompt，便于你核对模板准确性）：

```python
from core import Agent
from core.prompt_manager import PromptManager
from tools import get_default_tools

pm = PromptManager.build(
    identity="企业招聘的简历筛选 Agent",
    objective="根据岗位要求筛选候选人简历，输出候选人评分、匹配理由与推荐结论",
    extra_rules="输出必须包含：候选人姓名、匹配分、三条理由、是否推荐。",
)

print("===== 当前生效 Prompt =====")
print(pm.system_prompt)
print("==========================")

agent = Agent(
    tools=get_default_tools(),
    prompt_manager=pm,
)

question = "请给出一个用于筛选 Python 后端工程师简历的评分标准模板"
result = agent.run(question)

print("\n===== Agent 输出 =====")
print(result.answer)
print("\n===== 执行摘要 =====")
print(
    f"steps={len(result.steps)}, "
    f"tool_calls={result.total_tool_calls}, "
    f"tokens(in/out)={result.total_input_tokens}/{result.total_output_tokens}, "
    f"latency={result.total_latency:.2f}s"
)
```

运行命令：

```powershell
cd "c:\Users\Lenovo\Desktop\2526source\agent-ai"
python main.py "给我一份用于招聘 Python 后端工程师的简历筛选标准"
```

或运行你自己的脚本：

```powershell
cd "c:\Users\Lenovo\Desktop\2526source\agent-ai"
python your_demo.py
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

---

## 测试数据集与基准测试使用说明

### 文件结构

```
benchmarks/
├── test_cases.yaml        # 功能测试：各工具正常调用场景（13 条）
├── edge_cases.yaml        # 边界测试：安全拦截、Prompt Injection、异常输入（13 条）
├── regression_suite.yaml  # 回归测试：历史 Bug + 冒烟 + 多步推理（11 条）
└── run_benchmark.py       # 命令行运行入口

evaluation/
├── evaluator.py   # 核心：加载 YAML → 运行 Agent → 自动判定通过/失败
├── metrics.py     # 汇总统计：通过率、延迟、Token、分类明细
└── reporter.py    # 输出：控制台可读报告 + Markdown 文件（outputs/）
```

### 前置条件

1. 已配置 `.env`（需要真实 API Key，因为要调用 LLM）
2. 安装新增依赖（新增了 `pyyaml`）：

```powershell
cd "c:\Users\Lenovo\Desktop\2526source\agent-ai"
uv sync
```

### 运行测试套件

```powershell
# 功能测试（验证各工具正常调用）
python benchmarks/run_benchmark.py --suite test_cases

# 边界测试（验证安全拦截是否有效）
python benchmarks/run_benchmark.py --suite edge_cases

# 回归测试（防止历史 Bug 重现）
python benchmarks/run_benchmark.py --suite regression_suite

# 一键运行全部套件
python benchmarks/run_benchmark.py --suite all

# 运行并保存 Markdown 报告到 outputs/ 目录
python benchmarks/run_benchmark.py --suite all --save
```

### 查看报告

控制台会直接打印汇总表：

```
────────────────────────────────────────────────────────────
  📊 Benchmark Report — 功能测试
────────────────────────────────────────────────────────────
  总用例：13  通过：12  失败：1
  通过率：92.3%
  平均延迟：1.83s  最大延迟：4.21s
  平均步骤：1.5
  Token 消耗：输入 4200  输出 860

  分类                 总数 通过  通过率
  ──────────────────── ──── ──── ───────
  calculator              4    4  100.0%
  file_operations         4    3   75.0%
  web_search              2    2  100.0%
  ...
────────────────────────────────────────────────────────────
```

加 `--save` 后报告还会写入 `outputs/benchmark_功能测试_20260311_120000.md`。

### 在代码中直接调用

```python
from evaluation import Evaluator, MetricsCollector, BenchmarkReport

# 运行套件
ev = Evaluator()
results = ev.run_suite("benchmarks/test_cases.yaml")

# 统计
summary = MetricsCollector.summarize("功能测试", results)
BenchmarkReport.print_summary(summary)
BenchmarkReport.save_markdown(summary)  # 写入 outputs/
```

### 添加自定义测试用例

在任意 YAML 文件的 `cases:` 列表中追加，字段说明：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | str | ✅ | 用例名称（唯一标识）|
| `category` | str | ✅ | 分类（用于报告分组）|
| `input` | str | ✅ | 发送给 Agent 的问题 |
| `expected_tool` | str | — | Agent 必须调用的工具名 |
| `expected_tools` | list | — | Agent 必须调用的全部工具（多步）|
| `expected_output_contains` | list | — | 答案中必须包含其中至少一个字符串 |
| `expected_output_not_contains` | list | — | 答案中不得包含任意一个字符串 |
| `expected_behavior` | str | — | 描述性说明（不做自动判断，仅记录）|
| `should_succeed` | bool | — | `false` 时要求 Agent 输出拒绝词 |
| `max_steps` | int | — | Agent 完成任务允许的最大步骤数 |
| `prompt_override` | dict | — | 覆盖 Agent 的 identity / objective |

**示例：**

```yaml
cases:
  - name: "我的自定义用例"
    category: "calculator"
    input: "计算 99 * 99"
    expected_tool: "calculator"
    expected_output_contains: ["9801"]
    max_steps: 2
```

---

## web_search 工具使用说明

`tools/web_search.py` 实现了 `WebSearchTool`，已内置于 `get_default_tools()`，无需手动注册。

### 工作原理

Agent 会根据问题语义**自动判断**是否调用该工具，无需用户指定。典型触发场景：
- "北京今天天气怎么样"
- "最新的 Python 版本是什么"
- "今天有什么热点新闻"
- 任何需要**实时/联网**获取信息的问题

### 两种搜索后端

| 后端 | 需要 Key | 结果质量 | 适用场景 |
|------|---------|---------|---------|
| **Tavily** | 是（免费额度） | ⭐⭐⭐⭐⭐ | 生产/演示推荐 |
| **DuckDuckGo** | 否 | ⭐⭐⭐ | 快速验证、学习调试 |

未设置 `TAVILY_API_KEY` 时自动降级到 DuckDuckGo，零配置可运行。

### 配置 Tavily（推荐）

1. 前往 [https://app.tavily.com](https://app.tavily.com) 免费注册，获取 API Key
2. 在 `.env` 中添加：

```env
TAVILY_API_KEY=tvly-your-tavily-key-here
SEARCH_MAX_RESULTS=5    # 可选，单次最多返回条数，默认 5
SEARCH_TIMEOUT=10       # 可选，请求超时秒数，默认 10
```

### 示例：验证 web_search 是否正常调用

```powershell
cd "c:\Users\Lenovo\Desktop\2526source\agent-ai"
python main.py "北京今天的天气怎么样"
```

看到日志中出现如下内容，说明工具已被 Agent 正确调用：

```
[INFO] tool.web_search | 网络搜索 | 后端=duckduckgo | query='北京今天的天气' | max_results=5
[INFO] tool.web_search | 搜索完成，共返回 3 条结果
```

### 在文件结构中的位置

```
tools/
├── base_tool.py       # 工具基类
├── file_operations.py
├── calculator.py
├── data_analysis.py
└── web_search.py      # ← 新增：网络搜索工具
```
