from __future__ import annotations

import os
import shutil
import tempfile
import threading
import uuid
from datetime import timedelta
from pathlib import Path

from fastapi import HTTPException

try:
    from ..models.session import Session, utc_now
except ImportError:
    from models.session import Session, utc_now


class SessionManager:
    def __init__(self, session_dir: str | Path, ttl_seconds: int = 7200) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.RLock()
        self._session_dir = Path(session_dir)
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._ttl = timedelta(seconds=ttl_seconds)

    def create(self) -> Session:
        session = Session(session_id=str(uuid.uuid4()))
        with self._lock:
            self._sessions[session.session_id] = session
        self.get_session_dir(session.session_id).mkdir(parents=True, exist_ok=True)
        return session

    def get(self, session_id: str) -> Session:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise HTTPException(status_code=404, detail="Session not found")
            session.last_active = utc_now()
            return session

    def delete(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        self._delete_session_files(session.session_id, session.ifc_path)

    def cleanup_expired(self) -> int:
        now = utc_now()
        expired_ids: list[str] = []
        with self._lock:
            for session_id, session in self._sessions.items():
                if now - session.last_active > self._ttl:
                    expired_ids.append(session_id)
            expired_sessions = [self._sessions.pop(session_id) for session_id in expired_ids]
        for session in expired_sessions:
            self._delete_session_files(session.session_id, session.ifc_path)
        return len(expired_sessions)

    def touch(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise HTTPException(status_code=404, detail="Session not found")
            session.last_active = utc_now()

    def get_session_dir(self, session_id: str) -> Path:
        return self._session_dir / session_id

    def _delete_session_files(self, session_id: str, ifc_path: str | None) -> None:
        if ifc_path:
            try:
                Path(ifc_path).unlink(missing_ok=True)
            except OSError:
                pass
        try:
            shutil.rmtree(self.get_session_dir(session_id), ignore_errors=True)
        except OSError:
            pass


DEFAULT_SESSION_DIR = os.getenv(
    "IFC_SESSION_DIR",
    str(Path(tempfile.gettempdir()) / "ifc_sessions"),
)
DEFAULT_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "7200"))

session_manager = SessionManager(
    session_dir=DEFAULT_SESSION_DIR,
    ttl_seconds=DEFAULT_TTL_SECONDS,
)
