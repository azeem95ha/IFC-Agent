from __future__ import annotations

from fastapi import APIRouter, Response, status

try:
    from ..models.session import SessionMeta
    from ..services.session_manager import session_manager
except ImportError:
    from models.session import SessionMeta
    from services.session_manager import session_manager

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_session() -> dict[str, str]:
    session = session_manager.create()
    return {"session_id": session.session_id}


@router.get("/{session_id}", response_model=SessionMeta)
async def get_session(session_id: str) -> SessionMeta:
    session = session_manager.get(session_id)
    return SessionMeta.from_session(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str) -> Response:
    session_manager.delete(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
