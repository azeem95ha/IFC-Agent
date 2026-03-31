from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .routers.chat import router as chat_router
    from .routers.files import router as files_router
    from .routers.sessions import router as sessions_router
    from .services.session_manager import session_manager
except ImportError:
    from routers.chat import router as chat_router
    from routers.files import router as files_router
    from routers.sessions import router as sessions_router
    from services.session_manager import session_manager

load_dotenv()

LOGGER = logging.getLogger(__name__)


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


async def _session_cleanup_loop() -> None:
    while True:
        removed = session_manager.cleanup_expired()
        if removed:
            LOGGER.info("Removed %s expired session(s)", removed)
        await asyncio.sleep(600)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    cleanup_task = asyncio.create_task(_session_cleanup_loop())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task


def create_app() -> FastAPI:
    app = FastAPI(title="IFC AI Assistant API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(sessions_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(files_router, prefix="/api")
    return app


app = create_app()
