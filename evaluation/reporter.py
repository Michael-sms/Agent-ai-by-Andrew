"""
评估报告生成（BenchmarkReport）
将 SuiteSummary 输出为控制台文本或写入 Markdown 报告文件。
"""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from config.settings import settings
from utils.logger import get_logger

if TYPE_CHECKING:
    from evaluation.metrics import SuiteSummary

logger = get_logger("evaluation.reporter")


class BenchmarkReport:
    """
    用法::

        from evaluation.reporter import BenchmarkReport
        BenchmarkReport.print_summary(summary)
        BenchmarkReport.save_markdown(summary)   # 写入 outputs/benchmark_report_*.md
    """

    @staticmethod
    def print_summary(summary: "SuiteSummary") -> None:
        """在控制台打印可读报告。"""
        sep = "─" * 60
        print(f"\n{sep}")
        print(f"  📊 Benchmark Report — {summary.suite_name}")
        print(sep)
        print(f"  总用例：{summary.total}  通过：{summary.passed}  失败：{summary.failed}")
        print(f"  通过率：{summary.pass_rate:.1%}")
        print(f"  平均延迟：{summary.avg_latency:.2f}s  最大延迟：{summary.max_latency:.2f}s")
        print(f"  平均步骤：{summary.avg_steps:.1f}")
        print(f"  Token 消耗：输入 {summary.total_input_tokens}  输出 {summary.total_output_tokens}")

        if summary.category_stats:
            print(f"\n  {'分类':<20} {'总数':>4} {'通过':>4} {'通过率':>7}")
            print(f"  {'─'*20} {'─'*4} {'─'*4} {'─'*7}")
            for cat, s in summary.category_stats.items():
                rate = s["passed"] / s["total"] if s["total"] else 0
                print(f"  {cat:<20} {s['total']:>4} {s['passed']:>4} {rate:>7.1%}")

        if summary.failures:
            print(f"\n  ❌ 失败用例（{len(summary.failures)} 条）：")
            for f in summary.failures:
                print(f"    • [{f['name']}] {f['reason']}")
        print(f"{sep}\n")

    @staticmethod
    def save_markdown(summary: "SuiteSummary", output_dir: Path | None = None) -> Path:
        """将报告写入 outputs/ 目录下的 Markdown 文件，返回文件路径。"""
        if output_dir is None:
            output_dir = settings.OUTPUT_DIR
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = summary.suite_name.replace(" ", "_").replace("/", "-")
        out_path = output_dir / f"benchmark_{safe_name}_{ts}.md"

        lines: list[str] = [
            f"# Benchmark Report — {summary.suite_name}",
            f"\n生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "## 汇总",
            f"| 指标 | 值 |",
            f"|------|-----|",
            f"| 总用例 | {summary.total} |",
            f"| 通过 | {summary.passed} |",
            f"| 失败 | {summary.failed} |",
            f"| 通过率 | {summary.pass_rate:.1%} |",
            f"| 平均延迟 | {summary.avg_latency:.2f}s |",
            f"| 最大延迟 | {summary.max_latency:.2f}s |",
            f"| 平均步骤数 | {summary.avg_steps:.1f} |",
            f"| 总输入 Token | {summary.total_input_tokens} |",
            f"| 总输出 Token | {summary.total_output_tokens} |",
            "",
        ]

        if summary.category_stats:
            lines += [
                "## 分类统计",
                "| 分类 | 总数 | 通过 | 通过率 |",
                "|------|------|------|--------|",
            ]
            for cat, s in summary.category_stats.items():
                rate = s["passed"] / s["total"] if s["total"] else 0
                lines.append(f"| {cat} | {s['total']} | {s['passed']} | {rate:.1%} |")
            lines.append("")

        if summary.failures:
            lines += [
                "## 失败用例",
                "| 用例名 | 失败原因 |",
                "|--------|---------|",
            ]
            for f in summary.failures:
                reason = f["reason"].replace("|", "\\|")
                lines.append(f"| {f['name']} | {reason} |")
            lines.append("")

        out_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("评估报告已写入 %s", out_path)
        return out_path
