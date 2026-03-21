"""
Web 聊天服务入口。

运行：
    python -m webapp.server
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import settings
from core import Agent
from tools import get_default_tools

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Agent AI Web UI", version="0.1.0")
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

_AGENT: Agent | None = None
_AGENT_LOCK = threading.Lock()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    success: bool
    answer: str
    error: str = ""
    total_latency: float = 0.0
    total_tool_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


def get_agent() -> Agent:
    global _AGENT
    if _AGENT is None:
        settings.validate()
        settings.ensure_dirs()
        _AGENT = Agent(tools=get_default_tools())
    return _AGENT


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent-ai-web"}


@app.post("/api/reset")
def reset_chat() -> dict[str, str]:
    try:
        agent = get_agent()
        with _AGENT_LOCK:
            agent.reset()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"重置失败: {exc}") from exc
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message 不能为空")

    try:
        agent = get_agent()
        with _AGENT_LOCK:
            result = agent.run(message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"调用失败: {exc}") from exc

    return ChatResponse(
        success=result.success,
        answer=result.answer,
        error=result.error,
        total_latency=result.total_latency,
        total_tool_calls=result.total_tool_calls,
        total_input_tokens=result.total_input_tokens,
        total_output_tokens=result.total_output_tokens,
    )


def run() -> None:
    import uvicorn

    uvicorn.run(
        "webapp.server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    run()
