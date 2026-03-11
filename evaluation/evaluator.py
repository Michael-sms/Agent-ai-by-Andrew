"""
评估器（Evaluator）
对单条测试用例运行 Agent，并根据 YAML 中定义的期望判断是否通过。

判断逻辑：
  expected_output_contains    → 答案中必须包含其中至少一个字符串
  expected_output_not_contains→ 答案中不得包含其中任意一个字符串
  expected_tool               → Agent 必须调用了该工具
  expected_tools              → Agent 必须调用了列表中所有工具
  expected_behavior           → 仅记录描述，不做自动判断（需人工核对）
  should_succeed              → 若为 false，则要求 Agent 明确拒绝（输出含拒绝词）
  max_steps                   → Agent 完成任务不超过该步骤数
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from core.agent import Agent, AgentResult
from core.prompt_manager import PromptManager
from tools import get_default_tools
from utils.logger import get_logger

logger = get_logger("evaluation.evaluator")

# 拒绝操作时输出中常见的关键词
_REJECT_KEYWORDS = ["拒绝", "不允许", "无法", "权限", "禁止", "不能", "不支持", "错误"]


@dataclass
class CaseResult:
    """单条用例的评估结果。"""
    name: str
    category: str
    passed: bool
    reason: str = ""                     # 失败原因或通过说明
    answer: str = ""                     # Agent 实际输出
    tools_called: list[str] = field(default_factory=list)
    steps: int = 0
    latency: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    error: str = ""                      # 运行时异常


class Evaluator:
    """
    遍历测试套件，逐条运行 Agent 并判断结果。

    用法::

        from evaluation import Evaluator
        ev = Evaluator()
        results = ev.run_suite("benchmarks/test_cases.yaml")
    """

    def __init__(self, agent: Agent | None = None) -> None:
        if agent is None:
            agent = Agent(tools=get_default_tools())
        self.agent = agent

    # ── 公开 API ───────────────────────────────────────────

    def run_suite(self, yaml_path: str) -> list[CaseResult]:
        """加载 YAML 测试套件，逐条执行并返回结果列表。"""
        import yaml
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        suite_name = data.get("suite", yaml_path)
        cases = data.get("cases", [])
        logger.info("开始执行测试套件 [%s]，共 %d 条用例", suite_name, len(cases))

        results: list[CaseResult] = []
        for case in cases:
            result = self._run_case(case)
            results.append(result)
            status = "✅ PASS" if result.passed else "❌ FAIL"
            logger.info("%s  %s — %s", status, result.name, result.reason)

        return results

    def run_case(self, case: dict[str, Any]) -> CaseResult:
        """对外暴露单条用例执行接口。"""
        return self._run_case(case)

    # ── 内部实现 ───────────────────────────────────────────

    def _run_case(self, case: dict[str, Any]) -> CaseResult:
        name = case.get("name", "未命名")
        category = case.get("category", "")
        user_input = self._expand_input(case)

        # 构建 Agent（支持 prompt_override）
        agent = self._build_agent(case)

        # 运行
        t0 = time.perf_counter()
        try:
            result: AgentResult = agent.run(user_input)
        except Exception as e:
            elapsed = time.perf_counter() - t0
            return CaseResult(
                name=name, category=category, passed=False,
                reason=f"运行时异常：{e}", error=str(e), latency=elapsed,
            )

        elapsed = time.perf_counter() - t0
        answer = result.answer
        tools_called = [s.tool_name for s in result.steps if s.tool_name]

        # 判断
        passed, reason = self._judge(case, answer, tools_called, result)

        return CaseResult(
            name=name,
            category=category,
            passed=passed,
            reason=reason,
            answer=answer,
            tools_called=tools_called,
            steps=len(result.steps),
            latency=elapsed,
            input_tokens=result.total_input_tokens,
            output_tokens=result.total_output_tokens,
        )

    def _expand_input(self, case: dict) -> str:
        """处理 input_expansion，将占位符替换为重复文本。"""
        raw = case.get("input", "")
        expansion = case.get("input_expansion")
        if expansion:
            placeholder = expansion.get("placeholder", "")
            repeat = expansion.get("repeat", 1)
            raw = raw.replace("{placeholder}", placeholder * repeat)
        return raw

    def _build_agent(self, case: dict) -> Agent:
        """支持 prompt_override 覆盖 Agent 身份。"""
        override = case.get("prompt_override")
        if override:
            pm = PromptManager.build(
                identity=override.get("identity", "测试 Agent"),
                objective=override.get("objective", "回答测试问题"),
            )
            return Agent(tools=get_default_tools(), prompt_manager=pm)
        return self.agent

    def _judge(
        self,
        case: dict,
        answer: str,
        tools_called: list[str],
        result: AgentResult,
    ) -> tuple[bool, str]:
        """综合所有判断条件，返回 (passed, reason)。"""
        answer_lower = answer.lower()

        # 1. expected_output_contains（至少命中一个）
        must_have: list[str] = case.get("expected_output_contains", [])
        if must_have:
            hit = any(kw.lower() in answer_lower for kw in must_have)
            if not hit:
                return False, f"输出未包含期望关键词 {must_have}；实际：{answer[:120]}"

        # 2. expected_output_not_contains（一个都不能有）
        must_not: list[str] = case.get("expected_output_not_contains", [])
        for kw in must_not:
            if kw.lower() in answer_lower:
                return False, f"输出包含禁止关键词 '{kw}'；实际：{answer[:120]}"

        # 3. expected_tool（单工具）
        expected_tool: str | None = case.get("expected_tool")
        if expected_tool and expected_tool != "null":
            if expected_tool not in tools_called:
                return False, f"未调用期望工具 '{expected_tool}'；实际调用：{tools_called}"

        # 4. expected_tools（多工具，全部需要调用）
        expected_tools: list[str] = case.get("expected_tools", [])
        for t in expected_tools:
            if t not in tools_called:
                return False, f"未调用期望工具 '{t}'；实际调用：{tools_called}"

        # 5. should_succeed=false → 输出中须含拒绝词
        should_succeed = case.get("should_succeed", True)
        if should_succeed is False:
            rejected = any(kw in answer for kw in _REJECT_KEYWORDS)
            if not rejected:
                return False, f"预期拒绝但未检测到拒绝词；实际：{answer[:120]}"

        # 6. max_steps
        max_steps = case.get("max_steps")
        if max_steps and len(result.steps) > max_steps:
            return False, f"步骤数 {len(result.steps)} 超过上限 {max_steps}"

        behavior = case.get("expected_behavior", "")
        return True, f"通过（{behavior}）" if behavior else "通过"
