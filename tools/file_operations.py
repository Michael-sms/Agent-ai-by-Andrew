"""
文件读写工具 - 仅允许访问白名单目录
"""
from pathlib import Path

from config.security import security_config
from config.settings import settings
from tools.base_tool import BaseTool, ToolResult


class FileReadTool(BaseTool):
    name = "file_read"
    description = "读取指定文件的文本内容，路径限定在 data/ 或 outputs/ 目录内。"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "相对于项目根目录的文件路径，如 data/example.txt"},
        },
        "required": ["path"],
    }

    def run(self, path: str, **_) -> ToolResult:  # type: ignore[override]
        abs_path = (settings.ROOT_DIR / path).resolve()

        if not security_config.is_path_allowed(abs_path, mode="read"):
            return ToolResult(
                success=False, output=None,
                error=f"拒绝访问：路径 '{abs_path}' 不在允许范围内。",
                tool_name=self.name,
            )

        if not abs_path.exists():
            return ToolResult(success=False, output=None, error=f"文件不存在: {abs_path}", tool_name=self.name)

        if abs_path.stat().st_size > security_config.MAX_FILE_SIZE:
            return ToolResult(success=False, output=None, error="文件超过最大读取限制 (1MB)。", tool_name=self.name)

        content = abs_path.read_text(encoding="utf-8", errors="replace")
        return ToolResult(success=True, output=content, tool_name=self.name)


class FileWriteTool(BaseTool):
    name = "file_write"
    description = "将内容写入 outputs/ 目录下的文件（自动创建目录）。"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "相对路径，如 outputs/result.txt"},
            "content": {"type": "string", "description": "要写入的文本内容"},
            "mode": {"type": "string", "enum": ["overwrite", "append"], "description": "写入模式，默认 overwrite"},
        },
        "required": ["path", "content"],
    }

    def run(self, path: str, content: str, mode: str = "overwrite", **_) -> ToolResult:  # type: ignore[override]
        abs_path = (settings.ROOT_DIR / path).resolve()

        if not security_config.is_path_allowed(abs_path, mode="write"):
            return ToolResult(
                success=False, output=None,
                error=f"拒绝写入：路径 '{abs_path}' 不在写入白名单内。",
                tool_name=self.name,
            )

        abs_path.parent.mkdir(parents=True, exist_ok=True)
        write_mode = "a" if mode == "append" else "w"
        abs_path.write_text(content, encoding="utf-8") if write_mode == "w" else \
            abs_path.open("a", encoding="utf-8").write(content)

        return ToolResult(success=True, output=f"已写入 {abs_path}", tool_name=self.name)
