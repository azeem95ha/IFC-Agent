from __future__ import annotations

import os

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status

try:
    from ..models.session import ModelInfo
    from ..services.ifc_service import clear_model, load_from_upload, save_to_bytes
    from ..services.session_manager import session_manager
except ImportError:
    from models.session import ModelInfo
    from services.ifc_service import clear_model, load_from_upload, save_to_bytes
    from services.session_manager import session_manager

router = APIRouter(prefix="/sessions/{session_id}", tags=["files"])

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024


@router.post("/upload", response_model=ModelInfo)
async def upload_ifc(session_id: str, file: UploadFile = File(...)) -> ModelInfo:
    session = session_manager.get(session_id)
    filename = file.filename or "upload.ifc"
    if not filename.lower().endswith(".ifc"):
        raise HTTPException(status_code=422, detail="Only .ifc files are allowed")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Maximum upload size is {MAX_UPLOAD_MB} MB")

    try:
        return await load_from_upload(session, content, filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to load IFC file: {exc}") from exc


@router.get("/download")
async def download_model(session_id: str) -> Response:
    session = session_manager.get(session_id)
    try:
        content = await save_to_bytes(session)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    filename = session.ifc_filename or "model.ifc"
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/model", status_code=status.HTTP_204_NO_CONTENT)
async def remove_model(session_id: str) -> Response:
    session = session_manager.get(session_id)
    clear_model(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
