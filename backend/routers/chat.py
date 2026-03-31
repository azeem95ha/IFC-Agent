from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, Response, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import messages_to_dict

try:
    from ..models.chat import ChatRequest, DoneEvent
    from ..services.agent_service import run_agent_streaming
    from ..services.session_manager import session_manager
except ImportError:
    from models.chat import ChatRequest, DoneEvent
    from services.agent_service import run_agent_streaming
    from services.session_manager import session_manager

router = APIRouter(prefix="/sessions/{session_id}/chat", tags=["chat"])


@router.post("")
async def chat(session_id: str, body: ChatRequest) -> StreamingResponse:
    session = session_manager.get(session_id)
    queue: asyncio.Queue[object] = asyncio.Queue()
    task = asyncio.create_task(run_agent_streaming(session, body.message, body.api_key, queue))

    async def generate() -> AsyncIterator[str]:
        try:
            while True:
                event = await queue.get()
                yield f"data: {event.model_dump_json()}\n\n"
                if isinstance(event, DoneEvent):
                    break
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(session_id: str) -> Response:
    session = session_manager.get(session_id)
    session.chat_history.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/history")
async def get_chat_history(session_id: str) -> list[dict]:
    session = session_manager.get(session_id)
    return messages_to_dict(session.chat_history)
