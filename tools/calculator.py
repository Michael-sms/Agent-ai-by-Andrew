"""
数学计算工具 - 安全的表达式求值
"""
import ast
import math
import operator

from tools.base_tool import BaseTool, ToolResult

# 仅允许的操作符和函数
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}

_SAFE_FUNCS = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "pi": math.pi, "e": math.e, "ceil": math.ceil, "floor": math.floor,
}


def _safe_eval(node):
    """递归安全求值 AST 节点。"""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in _SAFE_FUNCS:
            return _SAFE_FUNCS[node.id]
        raise ValueError(f"不允许的变量名: {node.id}")
    if isinstance(node, ast.Call):
        func = _safe_eval(node.func)
        args = [_safe_eval(a) for a in node.args]
        return func(*args)
    if isinstance(node, ast.BinOp):
        op = type(node.op)
        if op not in _SAFE_OPERATORS:
            raise ValueError(f"不允许的操作符: {op}")
        return _SAFE_OPERATORS[op](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op = type(node.op)
        if op not in _SAFE_OPERATORS:
            raise ValueError(f"不允许的操作符: {op}")
        return _SAFE_OPERATORS[op](_safe_eval(node.operand))
    raise ValueError(f"不支持的表达式类型: {type(node)}")


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "安全的数学表达式求值，支持四则运算及常用数学函数（sqrt, sin, cos, log 等）。"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "合法的数学表达式，如 '(3+4)*2' 或 'sqrt(16)'"},
        },
        "required": ["expression"],
    }

    def run(self, expression: str, **_) -> ToolResult:  # type: ignore[override]
        try:
            tree = ast.parse(expression.strip(), mode="eval")
            result = _safe_eval(tree)
            return ToolResult(success=True, output=result, tool_name=self.name)
        except (ValueError, ZeroDivisionError, TypeError) as e:
            return ToolResult(success=False, output=None, error=str(e), tool_name=self.name)
        except SyntaxError:
            return ToolResult(success=False, output=None, error=f"表达式语法错误: {expression}", tool_name=self.name)
