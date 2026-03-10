"""
安全策略配置 - 文件路径白名单、工具权限
"""
from pathlib import Path


class SecurityConfig:
    """安全边界配置。"""

    # 允许读写的目录（相对于项目根）
    ALLOWED_READ_DIRS: list[str] = ["data", "outputs", "benchmarks"]
    ALLOWED_WRITE_DIRS: list[str] = ["outputs", "logs"]

    # 禁止访问的系统目录（绝对路径前缀）
    BLOCKED_PATH_PREFIXES: list[str] = [
        "C:\\Windows",
        "C:\\Program Files",
        "/etc",
        "/sys",
        "/proc",
        "/root",
    ]

    # 启用的工具白名单（None 表示全部允许）
    ENABLED_TOOLS: list[str] | None = None

    # 最大文件读取大小 (bytes)
    MAX_FILE_SIZE: int = 1024 * 1024  # 1 MB

    # 网络请求超时 (秒)
    REQUEST_TIMEOUT: int = 15

    # 单次会话最多调用同一工具次数
    MAX_TOOL_CALLS_PER_SESSION: int = 50

    def is_path_allowed(self, path: str | Path, mode: str = "read") -> bool:
        """
        校验路径是否在允许范围内。
        mode: 'read' | 'write'
        """
        from config.settings import settings

        p = Path(path).resolve()

        # 拒绝系统目录
        for prefix in self.BLOCKED_PATH_PREFIXES:
            if str(p).startswith(prefix):
                return False

        # 必须在项目根目录下
        try:
            p.relative_to(settings.ROOT_DIR)
        except ValueError:
            return False

        allowed_dirs = self.ALLOWED_WRITE_DIRS if mode == "write" else self.ALLOWED_READ_DIRS
        for d in allowed_dirs:
            if str(p).startswith(str(settings.ROOT_DIR / d)):
                return True

        return False


security_config = SecurityConfig()
