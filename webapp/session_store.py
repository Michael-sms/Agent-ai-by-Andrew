from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class SessionMessage:
    role: str
    content: str
    created_at: str

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
        }


class SessionStore:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._lock = Lock()
        self._data: dict[str, list | str | dict] = {
            "sessions": [],
            "active_session_id": "",
        }
        self._load()

    def _load(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._save_unlocked()
            return

        try:
            self._data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            self._data = {"sessions": [], "active_session_id": ""}
            self._save_unlocked()

    def _save_unlocked(self) -> None:
        self.file_path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _sessions(self) -> list[dict]:
        return self._data.setdefault("sessions", [])  # type: ignore[return-value]

    def list_sessions(self) -> list[dict]:
        with self._lock:
            sessions = sorted(
                self._sessions(),
                key=lambda x: x.get("updated_at", ""),
                reverse=True,
            )
            return [
                {
                    "id": s["id"],
                    "title": s["title"],
                    "created_at": s["created_at"],
                    "updated_at": s["updated_at"],
                    "preview": s.get("preview", ""),
                    "message_count": len(s.get("messages", [])),
                }
                for s in sessions
            ]

    def get_active_session_id(self) -> str:
        with self._lock:
            return str(self._data.get("active_session_id", ""))

    def set_active_session(self, session_id: str) -> None:
        with self._lock:
            self._data["active_session_id"] = session_id
            self._save_unlocked()

    def create_session(self, title: str = "新对话") -> dict:
        with self._lock:
            timestamp = now_iso()
            session_id = uuid4().hex
            session = {
                "id": session_id,
                "title": title,
                "created_at": timestamp,
                "updated_at": timestamp,
                "preview": "",
                "messages": [],
            }
            self._sessions().append(session)
            self._data["active_session_id"] = session_id
            self._save_unlocked()
            return {
                "id": session_id,
                "title": title,
                "created_at": timestamp,
                "updated_at": timestamp,
                "preview": "",
                "message_count": 0,
            }

    def get_session(self, session_id: str) -> dict | None:
        with self._lock:
            for s in self._sessions():
                if s["id"] == session_id:
                    return {
                        "id": s["id"],
                        "title": s["title"],
                        "created_at": s["created_at"],
                        "updated_at": s["updated_at"],
                        "preview": s.get("preview", ""),
                        "messages": list(s.get("messages", [])),
                    }
            return None

    def rename_session(self, session_id: str, title: str) -> dict | None:
        with self._lock:
            for s in self._sessions():
                if s["id"] == session_id:
                    s["title"] = title.strip() or "未命名对话"
                    s["updated_at"] = now_iso()
                    self._save_unlocked()
                    return {
                        "id": s["id"],
                        "title": s["title"],
                        "created_at": s["created_at"],
                        "updated_at": s["updated_at"],
                        "preview": s.get("preview", ""),
                        "message_count": len(s.get("messages", [])),
                    }
            return None

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            sessions = self._sessions()
            old_len = len(sessions)
            sessions[:] = [s for s in sessions if s["id"] != session_id]
            if len(sessions) == old_len:
                return False
            if self._data.get("active_session_id") == session_id:
                self._data["active_session_id"] = sessions[0]["id"] if sessions else ""
            self._save_unlocked()
            return True

    def clear_session_messages(self, session_id: str) -> bool:
        with self._lock:
            for s in self._sessions():
                if s["id"] == session_id:
                    s["messages"] = []
                    s["preview"] = ""
                    s["updated_at"] = now_iso()
                    self._save_unlocked()
                    return True
            return False

    def append_messages(self, session_id: str, messages: list[SessionMessage]) -> dict | None:
        with self._lock:
            for s in self._sessions():
                if s["id"] == session_id:
                    s.setdefault("messages", [])
                    s["messages"].extend(m.to_dict() for m in messages)
                    if s["messages"]:
                        first_user = next((m["content"] for m in s["messages"] if m["role"] == "user"), "")
                        if first_user and (s.get("title") in ("新对话", "") or len(s.get("messages", [])) <= 2):
                            s["title"] = first_user[:24] + ("..." if len(first_user) > 24 else "")
                        s["preview"] = s["messages"][-1]["content"][:60]
                    s["updated_at"] = now_iso()
                    self._save_unlocked()
                    return {
                        "id": s["id"],
                        "title": s["title"],
                        "created_at": s["created_at"],
                        "updated_at": s["updated_at"],
                        "preview": s.get("preview", ""),
                        "message_count": len(s.get("messages", [])),
                    }
            return None
