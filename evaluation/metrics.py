"""
性能指标收集（MetricsCollector）
汇总一批 CaseResult，生成统计摘要。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evaluation.evaluator import CaseResult


@dataclass
class SuiteSummary:
    """一个测试套件的汇总指标。"""
    suite_name: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: float = 0.0

    avg_latency: float = 0.0
    max_latency: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    avg_steps: float = 0.0

    # 按 category 统计
    category_stats: dict[str, dict] = field(default_factory=dict)
    # 失败用例列表
    failures: list[dict] = field(default_factory=list)


class MetricsCollector:
    """
    从 CaseResult 列表中提取统计指标。

    用法::

        from evaluation.metrics import MetricsCollector
        summary = MetricsCollector.summarize("功能测试", results)
        print(f"通过率：{summary.pass_rate:.1%}")
    """

    @staticmethod
    def summarize(suite_name: str, results: list["CaseResult"]) -> SuiteSummary:
        if not results:
            return SuiteSummary(suite_name=suite_name)

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        latencies = [r.latency for r in results]
        steps_list = [r.steps for r in results]

        # 按 category 分组
        cat_stats: dict[str, dict] = {}
        for r in results:
            cat = r.category or "unknown"
            if cat not in cat_stats:
                cat_stats[cat] = {"total": 0, "passed": 0}
            cat_stats[cat]["total"] += 1
            if r.passed:
                cat_stats[cat]["passed"] += 1

        failures = [
            {"name": r.name, "reason": r.reason, "answer": r.answer[:200]}
            for r in results if not r.passed
        ]

        return SuiteSummary(
            suite_name=suite_name,
            total=total,
            passed=passed,
            failed=failed,
            pass_rate=passed / total,
            avg_latency=sum(latencies) / total,
            max_latency=max(latencies),
            total_input_tokens=sum(r.input_tokens for r in results),
            total_output_tokens=sum(r.output_tokens for r in results),
            avg_steps=sum(steps_list) / total,
            category_stats=cat_stats,
            failures=failures,
        )
