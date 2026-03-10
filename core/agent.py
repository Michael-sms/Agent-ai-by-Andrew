"""
Agent 核心 - ReAct 模式主循环
Thought → Action (tool call) → Observation → 循环 → Final Answer
"""
import json
from dataclasses import dataclass, field

from config.settings import settings
from core.llm_client import LLMClient, LLMResponse
from core.prompt_manager import PromptManager
from memory.conversation import ConversationMemory
from security.sanitizer import sanitize_input, sanitize_output
from tools.base_tool import BaseTool, ToolResult
from utils.logger import get_logger

logger = get_logger("core.agent")


@dataclass
class AgentStep:
    """单步执行记录，用于评估与调试。"""
    iteration: int
    thought: str = ""
    tool_name: str = ""
    tool_args: dict = field(default_factory=dict)
    tool_result: str = ""
    final_answer: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency: float = 0.0


@dataclass
class AgentResult:
    """完整的 Agent 执行结果。"""
    answer: str
    steps: list[AgentStep] = field(default_factory=list)
    success: bool = True
    error: str = ""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency: float = 0.0
    total_tool_calls: int = 0


class Agent:
    """
    基于 ReAct (Reasoning + Acting) 范式的 AI Agent。

    支持：
    - 多工具并发注册
    - OpenAI Function Calling
    - 对话历史管理
    - 安全输入输出过滤
    - 逐步执行记录（方便评估）
    """

    def __init__(
        self,
        tools: list[BaseTool] | None = None,
        llm_client: LLMClient | None = None,
        prompt_manager: PromptManager | None = None,
        max_iterations: int | None = None,
    ):
        self.prompt_manager = prompt_manager or PromptManager()
        self.llm = llm_client or LLMClient()
        self.max_iterations = max_iterations or settings.MAX_ITERATIONS
        self.memory = ConversationMemory(
            system_prompt=self.prompt_manager.system_prompt,
            max_turns=settings.MAX_HISTORY,
        )

        # 工具注册表
        self._tools: dict[str, BaseTool] = {}
        for t in (tools or []):
            self.register_tool(t)

        logger.info(
            "Agent 初始化完成 | 工具数=%d | max_iter=%d",
            len(self._tools), self.max_iterations,
        )

    def register_tool(self, tool: BaseTool) -> None:
        """注册工具到 Agent。"""
        self._tools[tool.name] = tool
        logger.debug("注册工具: %s", tool.name)

    def _tool_schemas(self) -> list[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]

    def _call_tool(self, name: str, arguments: str) -> ToolResult:
        """根据 LLM 返回的 tool call 执行对应工具。"""
        if name not in self._tools:
            return ToolResult(success=False, output=None, error=f"未找到工具: {name}", tool_name=name)

        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return ToolResult(success=False, output=None, error=f"工具参数解析失败: {arguments}", tool_name=name)

        return self._tools[name].safe_run(**args)

    def run(self, user_input: str) -> AgentResult:
        """
        执行一次完整的 Agent 推理过程。

        参数:
            user_input: 用户输入的自然语言问题或指令

        返回:
            AgentResult 包含最终答案与每步执行记录
        """
        # ── 输入安全过滤 ───────────────────────────────────
        clean_input, warnings = sanitize_input(user_input)
        for w in warnings:
            logger.warning("输入安全警告: %s", w)

        self.memory.add("user", clean_input)
        steps: list[AgentStep] = []
        total_in_tok = total_out_tok = total_lat = 0.0
        total_tool_calls = 0

        logger.info(">>> Agent 开始执行 | 输入: %s", clean_input[:100])

        for iteration in range(1, self.max_iterations + 1):
            step = AgentStep(iteration=iteration)
            logger.info("--- 迭代 %d/%d ---", iteration, self.max_iterations)

            # ── LLM 推理 ───────────────────────────────────
            try:
                llm_resp: LLMResponse = self.llm.chat(
                    messages=self.memory.to_openai_messages(),
                    tools=self._tool_schemas() if self._tools else None,
                )
            except Exception as e:
                err_msg = f"LLM 调用异常: {e}"
                logger.error(err_msg)
                return AgentResult(answer="", success=False, error=err_msg, steps=steps)

            step.input_tokens = llm_resp.input_tokens
            step.output_tokens = llm_resp.output_tokens
            step.latency = llm_resp.latency
            total_in_tok += llm_resp.input_tokens
            total_out_tok += llm_resp.output_tokens
            total_lat += llm_resp.latency

            # ── 判断是否有工具调用 ─────────────────────────
            if llm_resp.tool_calls:
                # 将含 tool_calls 的 assistant 消息以原始 dict 形式写入 memory
                # 这是 OpenAI/DeepSeek 协议要求：tool 消息必须紧跟在含 tool_calls 的 assistant 消息之后
                assistant_msg: dict = {
                    "role": "assistant",
                    "content": llm_resp.content,  # 可以为空字符串或 None
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": tc["arguments"],
                            },
                        }
                        for tc in llm_resp.tool_calls
                    ],
                }
                self.memory.add_raw(assistant_msg)

                for tc in llm_resp.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["arguments"]
                    step.tool_name = tool_name
                    step.tool_args = json.loads(tool_args) if tool_args else {}
                    total_tool_calls += 1

                    logger.info("调用工具: %s | 参数: %s", tool_name, tool_args[:200])
                    result = self._call_tool(tool_name, tool_args)
                    step.tool_result = result.to_str()

                    # tool 结果消息：必须包含 tool_call_id 与对应的 assistant tool_calls id 匹配
                    self.memory.add_raw({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tool_name,
                        "content": result.to_str(),
                    })
                    logger.info("工具结果: %s", result.to_str()[:200])

            else:
                # ── 无工具调用 → Final Answer ───────────────
                raw_answer = llm_resp.content.strip()
                final_answer = sanitize_output(raw_answer)
                step.final_answer = final_answer

                self.memory.add("assistant", final_answer)
                steps.append(step)

                logger.info("<<< Agent 完成 | 答案: %s", final_answer[:200])
                return AgentResult(
                    answer=final_answer,
                    steps=steps,
                    success=True,
                    total_input_tokens=int(total_in_tok),
                    total_output_tokens=int(total_out_tok),
                    total_latency=total_lat,
                    total_tool_calls=total_tool_calls,
                )

            steps.append(step)

        # ── 超出最大迭代次数 ───────────────────────────────
        timeout_msg = f"已达最大迭代次数 ({self.max_iterations})，未能完成任务。"
        logger.warning(timeout_msg)
        return AgentResult(
            answer=timeout_msg,
            steps=steps,
            success=False,
            error=timeout_msg,
            total_input_tokens=int(total_in_tok),
            total_output_tokens=int(total_out_tok),
            total_latency=total_lat,
            total_tool_calls=total_tool_calls,
        )

    def reset(self) -> None:
        """清空对话历史，开启新会话。"""
        self.memory.clear()
        logger.info("对话历史已清空。")
