"""
基准测试运行入口
用法：

  # 运行单个套件
  python benchmarks/run_benchmark.py --suite test_cases
  python benchmarks/run_benchmark.py --suite edge_cases
  python benchmarks/run_benchmark.py --suite regression_suite

  # 运行全部套件
  python benchmarks/run_benchmark.py --suite all

  # 保存 Markdown 报告到 outputs/ 目录
  python benchmarks/run_benchmark.py --suite test_cases --save

  # 指定套件文件的完整路径
  python benchmarks/run_benchmark.py --file benchmarks/test_cases.yaml --save
"""
import argparse
import sys
from pathlib import Path

# 确保项目根目录在 sys.path，无论从哪个目录启动
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evaluation.evaluator import Evaluator
from evaluation.metrics import MetricsCollector
from evaluation.reporter import BenchmarkReport
from utils.logger import get_logger

logger = get_logger("benchmarks.runner")

SUITE_FILES = {
    "test_cases":       ROOT / "benchmarks" / "test_cases.yaml",
    "edge_cases":       ROOT / "benchmarks" / "edge_cases.yaml",
    "regression_suite": ROOT / "benchmarks" / "regression_suite.yaml",
}


def run_suite(yaml_path: Path, save: bool = False) -> bool:
    """运行单个套件，返回是否全部通过。"""
    if not yaml_path.exists():
        print(f"❌ 找不到文件：{yaml_path}")
        return False

    evaluator = Evaluator()
    results = evaluator.run_suite(str(yaml_path))

    import yaml
    with open(yaml_path, encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    suite_name = meta.get("suite", yaml_path.stem)

    summary = MetricsCollector.summarize(suite_name, results)
    BenchmarkReport.print_summary(summary)

    if save:
        out = BenchmarkReport.save_markdown(summary)
        print(f"📄 报告已保存：{out}")

    return summary.failed == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent-AI 基准测试运行器")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--suite",
        choices=list(SUITE_FILES.keys()) + ["all"],
        help="要运行的测试套件名称，或 'all' 运行全部",
    )
    group.add_argument(
        "--file",
        type=str,
        help="直接指定 YAML 文件路径",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="将评估报告保存为 Markdown 文件到 outputs/ 目录",
    )
    args = parser.parse_args()

    all_passed = True

    if args.file:
        all_passed = run_suite(Path(args.file), save=args.save)
    elif args.suite == "all":
        for name, path in SUITE_FILES.items():
            print(f"\n{'='*60}")
            print(f"  运行套件：{name}")
            print(f"{'='*60}")
            ok = run_suite(path, save=args.save)
            if not ok:
                all_passed = False
    else:
        all_passed = run_suite(SUITE_FILES[args.suite], save=args.save)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
