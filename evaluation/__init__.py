"""
evaluation 包 —— 输出质量评估与性能监控
"""
from evaluation.evaluator import CaseResult, Evaluator
from evaluation.metrics import MetricsCollector
from evaluation.reporter import BenchmarkReport

__all__ = ["Evaluator", "CaseResult", "MetricsCollector", "BenchmarkReport"]
