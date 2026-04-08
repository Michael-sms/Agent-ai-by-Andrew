"""
Web 聊天服务入口。

运行：
    python -m webapp.server
"""
from __future__ import annotations

import sys
import threading
from datetime import datetime
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
from webapp.session_store import SessionMessage, SessionStore, now_iso

STATIC_DIR = Path(__file__).resolve().parent / "static"
SESSION_FILE = ROOT / "data" / "web_sessions" / "sessions.json"

app = FastAPI(title="Agent AI Web UI", version="0.1.0")
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

_AGENT_LOCK = threading.Lock()
_SESSION_STORE = SessionStore(SESSION_FILE)
_AGENTS: dict[str, Agent] = {}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str = ""


class SessionCreateRequest(BaseModel):
    title: str = "新对话"


class SessionRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)


class ChatResponse(BaseModel):
    success: bool
    answer: str
    session_id: str
    session_title: str = ""
    error: str = ""
    ts: str = ""
    total_latency: float = 0.0
    total_tool_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


def _new_agent() -> Agent:
    settings.validate()
    settings.ensure_dirs()
    return Agent(tools=get_default_tools())


def get_or_create_session(session_id: str = "") -> dict:
    if session_id:
        session = _SESSION_STORE.get_session(session_id)
        if session:
            _SESSION_STORE.set_active_session(session_id)
            return session
    active = _SESSION_STORE.get_active_session_id()
    if active:
        session = _SESSION_STORE.get_session(active)
        if session:
            return session
    created = _SESSION_STORE.create_session()
    session = _SESSION_STORE.get_session(created["id"])
    if not session:
        raise HTTPException(status_code=500, detail="创建会话失败")
    return session


def get_agent_for_session(session_id: str) -> Agent:
    if session_id in _AGENTS:
        return _AGENTS[session_id]

    agent = _new_agent()
    session = _SESSION_STORE.get_session(session_id)
    if session:
        for message in session.get("messages", []):
            role = message.get("role", "")
            content = message.get("content", "")
            if role in ("user", "assistant") and content:
                agent.memory.add(role, content)
    _AGENTS[session_id] = agent
    return agent


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent-ai-web"}


@app.get("/api/sessions")
def list_sessions() -> dict:
    return {
        "sessions": _SESSION_STORE.list_sessions(),
        "active_session_id": _SESSION_STORE.get_active_session_id(),
    }


@app.post("/api/sessions")
def create_session(payload: SessionCreateRequest) -> dict:
    return _SESSION_STORE.create_session(payload.title.strip() or "新对话")


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    session = _SESSION_STORE.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    _SESSION_STORE.set_active_session(session_id)
    return session


@app.patch("/api/sessions/{session_id}")
def rename_session(session_id: str, payload: SessionRenameRequest) -> dict:
    updated = _SESSION_STORE.rename_session(session_id, payload.title)
    if not updated:
        raise HTTPException(status_code=404, detail="会话不存在")
    return updated


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str) -> dict:
    deleted = _SESSION_STORE.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    _AGENTS.pop(session_id, None)
    return {"status": "ok"}


@app.post("/api/sessions/{session_id}/reset")
def reset_session(session_id: str) -> dict:
    cleared = _SESSION_STORE.clear_session_messages(session_id)
    if not cleared:
        raise HTTPException(status_code=404, detail="会话不存在")
    _AGENTS.pop(session_id, None)
    return {"status": "ok"}


@app.post("/api/reset")
def reset_chat() -> dict[str, str]:
    active = _SESSION_STORE.get_active_session_id()
    if not active:
        return {"status": "ok"}
    _SESSION_STORE.clear_session_messages(active)
    _AGENTS.pop(active, None)
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message 不能为空")

    session = get_or_create_session(payload.session_id)
    session_id = session["id"]

    try:
        agent = get_agent_for_session(session_id)
        with _AGENT_LOCK:
            result = agent.run(message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"调用失败: {exc}") from exc

    timestamp = now_iso()
    updated = _SESSION_STORE.append_messages(
        session_id,
        [
            SessionMessage(role="user", content=message, created_at=timestamp),
            SessionMessage(role="assistant", content=result.answer, created_at=timestamp),
        ],
    )
    if not updated:
        raise HTTPException(status_code=500, detail="保存会话失败")
    _SESSION_STORE.set_active_session(session_id)

    return ChatResponse(
        success=result.success,
        answer=result.answer,
        session_id=session_id,
        session_title=updated["title"],
        error=result.error,
        ts=timestamp,
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
