"""
网络搜索工具
支持两种后端（按优先级自动选择）：
  1. Tavily Search API  —— 专为 LLM 设计，结果质量高（推荐）
  2. DuckDuckGo 即时答案 API —— 无需 Key，免费，但结果较简短

环境变量：
  TAVILY_API_KEY   填写后自动使用 Tavily；留空则降级到 DuckDuckGo
  SEARCH_MAX_RESULTS  单次搜索最多返回条目数，默认 5
  SEARCH_TIMEOUT      请求超时秒数，默认 10
"""
import json

import httpx

from config.settings import settings
from tools.base_tool import BaseTool, ToolResult
from utils.logger import get_logger

logger = get_logger("tool.web_search")


# ── Tavily 后端 ────────────────────────────────────────────────────────────

def _search_tavily(query: str, max_results: int, timeout: int) -> list[dict]:
    """调用 Tavily Search API，返回结果列表。"""
    api_key = settings.TAVILY_API_KEY
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
        "include_answer": True,
    }
    resp = httpx.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    results = []
    # Tavily 会返回一个 answer 字段（直接摘要）
    if data.get("answer"):
        results.append({"title": "摘要", "url": "", "snippet": data["answer"]})
    for r in data.get("results", [])[:max_results]:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", ""),
        })
    return results


# ── DuckDuckGo 后端（无 Key 降级方案）─────────────────────────────────────

def _search_duckduckgo(query: str, max_results: int, timeout: int) -> list[dict]:
    """
    使用 DuckDuckGo Instant Answer API（非官方，仅返回摘要级内容）。
    适合快速验证流程，生产环境建议换 Tavily。
    """
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    }
    resp = httpx.get(url, params=params, timeout=timeout,
                     headers={"User-Agent": "agent-ai/0.1 (learning project)"})
    resp.raise_for_status()
    data = resp.json()

    results: list[dict] = []

    # AbstractText：最主要的摘要
    if data.get("AbstractText"):
        results.append({
            "title": data.get("Heading", "摘要"),
            "url": data.get("AbstractURL", ""),
            "snippet": data["AbstractText"],
        })

    # RelatedTopics：相关条目
    for topic in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(topic, dict) and topic.get("Text"):
            results.append({
                "title": topic.get("Text", "")[:60],
                "url": topic.get("FirstURL", ""),
                "snippet": topic.get("Text", ""),
            })
        if len(results) >= max_results:
            break

    # Answer：即时答案（如汇率、时间等）
    if data.get("Answer") and len(results) < max_results:
        results.insert(0, {
            "title": "即时答案",
            "url": "",
            "snippet": data["Answer"],
        })

    return results


# ── 工具类 ─────────────────────────────────────────────────────────────────

class WebSearchTool(BaseTool):
    """
    网络搜索工具。
    - 有 TAVILY_API_KEY → 使用 Tavily（质量更高）
    - 无 Key → 自动降级到 DuckDuckGo Instant Answer API
    Agent 会根据用户问题自行判断是否需要调用此工具，
    典型场景：天气查询、最新新闻、实时数据等需要联网获取的问题。
    """

    name = "web_search"
    description = (
        "在互联网上搜索信息。适用于需要获取实时、最新或未知信息的问题，"
        "例如：天气查询、新闻、价格、当前事件等。"
        "不适合纯计算或本地文件操作。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词或自然语言问题，如 '北京今天天气' 或 '最新 Python 版本'",
            },
            "max_results": {
                "type": "integer",
                "description": "最多返回条目数，默认 5，最大 10",
            },
        },
        "required": ["query"],
    }

    def run(self, query: str, max_results: int = 0, **_) -> ToolResult:  # type: ignore[override]
        # 参数边界
        max_results = max(1, min(max_results or settings.SEARCH_MAX_RESULTS, 10))
        timeout = settings.SEARCH_TIMEOUT

        logger.info(
            "网络搜索 | 后端=%s | query=%r | max_results=%d",
            "tavily" if settings.TAVILY_API_KEY else "duckduckgo",
            query,
            max_results,
        )

        try:
            if settings.TAVILY_API_KEY:
                results = _search_tavily(query, max_results, timeout)
            else:
                results = _search_duckduckgo(query, max_results, timeout)
        except httpx.TimeoutException:
            return ToolResult(
                success=False, output=None,
                error=f"搜索请求超时（>{timeout}s），请稍后重试。",
                tool_name=self.name,
            )
        except httpx.HTTPStatusError as e:
            return ToolResult(
                success=False, output=None,
                error=f"搜索接口返回错误 {e.response.status_code}：{e.response.text[:200]}",
                tool_name=self.name,
            )
        except Exception as e:
            return ToolResult(
                success=False, output=None,
                error=f"搜索失败：{e}",
                tool_name=self.name,
            )

        if not results:
            return ToolResult(
                success=True,
                output="未找到相关结果，请尝试换一个关键词。",
                tool_name=self.name,
            )

        # 格式化输出，便于 LLM 阅读
        lines = [f"搜索关键词：{query}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] {r['title']}")
            if r["url"]:
                lines.append(f"    链接：{r['url']}")
            lines.append(f"    内容：{r['snippet']}")
            lines.append("")

        output = "\n".join(lines).strip()
        logger.info("搜索完成，共返回 %d 条结果", len(results))
        return ToolResult(success=True, output=output, tool_name=self.name)
