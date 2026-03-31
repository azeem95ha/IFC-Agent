from __future__ import annotations

import asyncio
import logging
import pickle
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.api.context
import ifcopenshell.util.placement

try:
    from ..models.session import Session
    from ..utils.thread_pool import EXECUTOR
except ImportError:
    from models.session import Session
    from utils.thread_pool import EXECUTOR


def reinitialize_session(session: Session, model: ifcopenshell.file) -> None:
    """Store a new model and clear derived caches plus chat history."""
    session.active_model = model
    session.ifc_types.clear()
    session.ifc_instances.clear()
    session.ifc_materials.clear()
    session.chat_history.clear()


def get_active_model(session: Session) -> ifcopenshell.file:
    """Return the active IFC model or raise a descriptive ValueError."""
    model = session.active_model
    if model is None:
        raise ValueError(
            "No IFC model is currently loaded. "
            "Upload a file first or use the 'load_ifc_model' tool."
        )
    return model


async def run_in_executor(fn, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(EXECUTOR, fn, *args)


def get_body_context(model: ifcopenshell.file):
    """Return or create the Body geometric representation sub-context."""
    for ctx in model.by_type("IfcGeometricRepresentationSubContext"):
        if ctx.ContextIdentifier == "Body":
            return ctx

    parent = None
    for ctx in model.by_type("IfcGeometricRepresentationContext"):
        if ctx.ContextType == "Model" and not ctx.is_a("IfcGeometricRepresentationSubContext"):
            parent = ctx
            break
    if parent is None:
        parent = ifcopenshell.api.context.add_context(model, context_type="Model")

    return ifcopenshell.api.context.add_context(
        model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=parent,
    )


def ifc_value(model: ifcopenshell.file, value: Any):
    """Wrap a Python scalar in its corresponding IFC value entity."""
    if isinstance(value, bool):
        return model.create_entity("IfcBoolean", value)
    if isinstance(value, int):
        return model.create_entity("IfcInteger", value)
    if isinstance(value, float):
        return model.create_entity("IfcReal", value)
    return model.create_entity("IfcLabel", str(value))


def unpack_entity(entity: Any) -> Any:
    """Recursively convert an IFC entity instance to plain Python data."""
    if isinstance(entity, ifcopenshell.entity_instance):
        return {key: unpack_entity(value) for key, value in entity.get_info().items()}
    if isinstance(entity, (list, tuple)):
        return [unpack_entity(item) for item in entity]
    return entity


def load_ifc_entities() -> list[str]:
    asset_path = Path(__file__).resolve().parent.parent / "utils" / "ifc_entities.pkl"
    with asset_path.open("rb") as fh:
        entities = pickle.load(fh)
    return list(entities)


ALL_IFC_ENTITIES = load_ifc_entities()

LOGGER = logging.getLogger(__name__)
