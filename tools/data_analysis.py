"""
数据分析工具 - Pandas 封装
"""
from tools.base_tool import BaseTool, ToolResult


class DataAnalysisTool(BaseTool):
    name = "data_analysis"
    description = "对 CSV 文件执行数据分析：统计摘要、列描述、过滤、排序、聚合。"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "CSV 文件相对路径，如 data/sales.csv"},
            "operation": {
                "type": "string",
                "enum": ["describe", "head", "shape", "columns", "value_counts", "groupby_sum", "sort"],
                "description": "操作类型",
            },
            "column": {"type": "string", "description": "目标列名（部分操作需要）"},
            "by_column": {"type": "string", "description": "groupby/sort 的依据列"},
            "n": {"type": "integer", "description": "返回行数，默认 5"},
            "ascending": {"type": "boolean", "description": "排序方向，默认 False（降序）"},
        },
        "required": ["path", "operation"],
    }

    def run(  # type: ignore[override]
        self,
        path: str,
        operation: str,
        column: str = "",
        by_column: str = "",
        n: int = 5,
        ascending: bool = False,
        **_,
    ) -> ToolResult:
        try:
            import pandas as pd
            from config.security import security_config
            from config.settings import settings

            abs_path = (settings.ROOT_DIR / path).resolve()
            if not security_config.is_path_allowed(abs_path, mode="read"):
                return ToolResult(success=False, output=None, error=f"拒绝访问: {abs_path}", tool_name=self.name)

            df = pd.read_csv(abs_path)

            if operation == "describe":
                result = df.describe(include="all").to_string()
            elif operation == "head":
                result = df.head(n).to_string()
            elif operation == "shape":
                result = f"行: {df.shape[0]}, 列: {df.shape[1]}"
            elif operation == "columns":
                result = str(df.columns.tolist())
            elif operation == "value_counts":
                if not column:
                    return ToolResult(success=False, output=None, error="value_counts 需要指定 column", tool_name=self.name)
                result = df[column].value_counts().head(n).to_string()
            elif operation == "groupby_sum":
                if not by_column or not column:
                    return ToolResult(success=False, output=None, error="groupby_sum 需要 column 和 by_column", tool_name=self.name)
                result = df.groupby(by_column)[column].sum().sort_values(ascending=ascending).head(n).to_string()
            elif operation == "sort":
                if not by_column:
                    return ToolResult(success=False, output=None, error="sort 需要 by_column", tool_name=self.name)
                result = df.sort_values(by_column, ascending=ascending).head(n).to_string()
            else:
                return ToolResult(success=False, output=None, error=f"未知操作: {operation}", tool_name=self.name)

            return ToolResult(success=True, output=result, tool_name=self.name)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e), tool_name=self.name)
