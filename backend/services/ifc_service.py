from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import ifcopenshell

try:
    from ..models.session import ModelInfo, Session
    from ..services.session_manager import session_manager
    from ..tools.common import reinitialize_session, run_in_executor
except ImportError:
    from models.session import ModelInfo, Session
    from services.session_manager import session_manager
    from tools.common import reinitialize_session, run_in_executor


async def load_from_upload(session: Session, upload_bytes: bytes, filename: str) -> ModelInfo:
    safe_name = Path(filename).name
    session_dir = session_manager.get_session_dir(session.session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    target_path = session_dir / safe_name
    target_path.write_bytes(upload_bytes)

    try:
        model = await run_in_executor(ifcopenshell.open, str(target_path))
        entity_count = sum(1 for _ in model)
        model_info = ModelInfo(
            filename=safe_name,
            size_bytes=len(upload_bytes),
            schema_name=model.schema,
            entity_count=entity_count,
        )
    except Exception:
        target_path.unlink(missing_ok=True)
        raise

    reinitialize_session(session, model)
    session.ifc_path = str(target_path)
    session.ifc_filename = safe_name
    return model_info


async def save_to_bytes(session: Session) -> bytes:
    if session.active_model is None:
        raise ValueError("No IFC model is currently loaded.")

    session_dir = session_manager.get_session_dir(session.session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(session.ifc_filename or "model.ifc").suffix or ".ifc"

    with NamedTemporaryFile(delete=False, suffix=suffix, dir=session_dir) as temp_file:
        export_path = Path(temp_file.name)

    def _write() -> None:
        session.active_model.write(str(export_path))

    try:
        await run_in_executor(_write)
        return export_path.read_bytes()
    finally:
        export_path.unlink(missing_ok=True)


def clear_model(session: Session) -> None:
    if session.ifc_path:
        Path(session.ifc_path).unlink(missing_ok=True)
    session.active_model = None
    session.ifc_path = None
    session.ifc_filename = None
    session.ifc_types.clear()
    session.ifc_instances.clear()
    session.ifc_materials.clear()
