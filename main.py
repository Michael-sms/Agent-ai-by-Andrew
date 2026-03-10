"""
Agent 项目主入口
用法:
  python main.py                   # 交互式对话
  python main.py "你的问题"         # 单次提问
"""
import sys
from pathlib import Path

# 确保项目根在 sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_agent():
    """构建并返回配置好的 Agent 实例。"""
    from config.settings import settings
    from tools import get_default_tools
    from core import Agent

    settings.validate()
    settings.ensure_dirs()

    agent = Agent(tools=get_default_tools())
    return agent


def run_interactive(agent) -> None:
    """交互式对话模式。"""
    print("=" * 50)
    print("  AI Agent 交互模式  |  输入 'exit' 退出  |  输入 'reset' 清空历史")
    print("=" * 50)
    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("再见！")
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("[对话历史已清空]")
            continue

        result = agent.run(user_input)
        print(f"\nAgent: {result.answer}")

        # 展示性能摘要
        if result.steps:
            print(
                f"\n[{len(result.steps)} 步 | {result.total_tool_calls} 次工具调用 | "
                f"in={result.total_input_tokens} out={result.total_output_tokens} tokens | "
                f"耗时 {result.total_latency:.2f}s]"
            )


def main():
    try:
        agent = build_agent()
    except ValueError as e:
        print(f"[配置错误] {e}")
        sys.exit(1)

    if len(sys.argv) > 1:
        # 单次提问
        question = " ".join(sys.argv[1:])
        result = agent.run(question)
        print(result.answer)
    else:
        run_interactive(agent)


if __name__ == "__main__":
    main()
