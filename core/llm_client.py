"""
LLM 客户端封装 - 统一 OpenAI SDK 调用，记录性能指标
"""
import time
from dataclasses import dataclass, field
from typing import Any

from utils.logger import get_logger

logger = get_logger("core.llm_client")


@dataclass
class LLMResponse:
    """LLM 调用结果。"""
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    latency: float = 0.0           # 秒
    model: str = ""
    finish_reason: str = ""


class LLMClient:
    """
    OpenAI ChatCompletion 封装。
    支持 function calling / tool_use 两种协议。
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        from config.settings import settings
        from openai import OpenAI

        self.model = model or settings.DEFAULT_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens

        self._client = OpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=base_url or settings.OPENAI_BASE_URL,
        )
        logger.info("LLMClient 初始化完成，模型: %s", self.model)

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
    ) -> LLMResponse:
        """
        发送对话请求。
        messages: OpenAI 格式消息列表
        tools: OpenAI function schema 列表
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        start = time.perf_counter()
        try:
            response = self._client.chat.completions.create(**kwargs)
        except Exception as e:
            logger.error("LLM 调用失败: %s", e)
            raise

        latency = time.perf_counter() - start
        choice = response.choices[0]
        msg = choice.message

        # 解析 tool_calls
        tool_calls: list[dict] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                })

        usage = response.usage
        result = LLMResponse(
            content=msg.content or "",
            tool_calls=tool_calls,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            latency=latency,
            model=response.model,
            finish_reason=choice.finish_reason or "",
        )

        logger.info(
            "LLM 响应 | 模型=%s | in=%d out=%d tokens | latency=%.2fs | finish=%s",
            result.model, result.input_tokens, result.output_tokens,
            result.latency, result.finish_reason,
        )
        return result
