from core import Agent
from core.prompt_manager import PromptManager
from tools import get_default_tools

pm = PromptManager.build(
    identity="企业招聘的简历筛选 Agent",
    objective="根据岗位要求筛选候选人简历，输出候选人评分、匹配理由与推荐结论",
    extra_rules="输出必须包含：候选人姓名、匹配分、三条理由、是否推荐。",
)

print("===== 当前生效 Prompt =====")
print(pm.system_prompt)
print("==========================")

agent = Agent(
    tools=get_default_tools(),
    prompt_manager=pm,
)

question = "请给出一个用于筛选 Python 后端工程师简历的评分标准模板"
result = agent.run(question)

print("\n===== Agent 输出 =====")
print(result.answer)
print("\n===== 执行摘要 =====")
print(
    f"steps={len(result.steps)}, "
    f"tool_calls={result.total_tool_calls}, "
    f"tokens(in/out)={result.total_input_tokens}/{result.total_output_tokens}, "
    f"latency={result.total_latency:.2f}s"
)