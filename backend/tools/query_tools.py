from __future__ import annotations

import os
from typing import Any

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.pset
import ifcopenshell.util.selector

try:
    from ..models.session import Session
except ImportError:
    from models.session import Session

try:
    from .common import ALL_IFC_ENTITIES, get_active_model, reinitialize_session, run_in_executor, unpack_entity
except ImportError:
    from tools.common import ALL_IFC_ENTITIES, get_active_model, reinitialize_session, run_in_executor, unpack_entity


async def get_project_info(session: Session) -> dict:
    """Retrieve high-level project metadata: name, description, owner, and authoring application."""
    model = get_active_model(session)
    projects = model.by_type("IfcProject")
    if not projects:
        return {"error": "No IfcProject found in the model."}
    proj = projects[0]
    owner_history = proj.OwnerHistory
    person = owner_history.OwningUser.ThePerson if (owner_history and owner_history.OwningUser) else None
    org = owner_history.OwningUser.TheOrganization if (owner_history and owner_history.OwningUser) else None
    app = owner_history.OwningApplication if owner_history else None
    return {
        "project_name": proj.Name,
        "long_name": proj.LongName,
        "description": proj.Description,
        "phase": proj.Phase,
        "schema": model.schema,
        "owner": f"{getattr(person, 'GivenName', '') or ''} {getattr(person, 'FamilyName', '') or ''}".strip() or "N/A",
        "organisation": getattr(org, "Name", "N/A"),
        "application": getattr(app, "ApplicationFullName", "N/A"),
        "app_version": getattr(app, "Version", "N/A"),
    }


async def list_all_types(session: Session) -> list[str]:
    """List every distinct IFC class name that has at least one instance in the model."""
    model = get_active_model(session)
    return sorted({entity.is_a() for entity in model.by_type("IfcObject") if entity.is_a()})


async def list_all_objects(session: Session, object_type: str) -> list[str]:
    """List all unique Name values for entities whose IFC class contains 'object_type'."""
    model = get_active_model(session)
    names: set[str] = set()
    for entity_name in ALL_IFC_ENTITIES:
        if object_type.lower() in entity_name.lower():
            for elem in model.by_type(entity_name):
                if hasattr(elem, "Name") and elem.Name:
                    names.add(elem.Name)
    return sorted(names)


async def list_entities(session: Session, object_type: str) -> list[int]:
    """Return integer IDs of all entities whose IFC class contains 'object_type'."""
    model = get_active_model(session)
    ids: list[int] = []
    for entity_name in ALL_IFC_ENTITIES:
        if object_type.lower() in entity_name.lower():
            ids.extend(entity.id() for entity in model.by_type(entity_name))
    return ids


async def get_objects_count(session: Session, object_type: str) -> dict[str, int]:
    """Count instances per IFC class for all classes matching 'object_type'."""
    model = get_active_model(session)
    counts: dict[str, int] = {}
    term = object_type.lower()
    for entity_name in ALL_IFC_ENTITIES:
        if term in entity_name.lower():
            count = len(model.by_type(entity_name))
            if count:
                counts[entity_name] = count
    return counts


async def get_object_info(session: Session, object_id: int) -> dict:
    """Return all attributes of a single IFC entity by its numeric step ID."""
    model = get_active_model(session)
    entity = model.by_id(object_id)
    if not entity:
        return {"error": f"No entity found with ID {object_id}."}
    return unpack_entity(entity)


async def list_all_materials(session: Session, object_type: str) -> list[tuple]:
    """Return material tuples for all elements whose IFC class contains 'object_type'."""
    model = get_active_model(session)
    result: list[tuple] = []
    for entity_name in ALL_IFC_ENTITIES:
        if object_type.lower() in entity_name.lower():
            for elem in model.by_type(entity_name):
                if not hasattr(elem, "HasAssociations"):
                    continue
                for assoc in elem.HasAssociations:
                    if not assoc.is_a("IfcRelAssociatesMaterial"):
                        continue
                    material = assoc.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        result.append((elem.id(), elem.Name, material.Name))
                    elif material.is_a("IfcMaterialList"):
                        for sub_material in material.Materials:
                            result.append((elem.id(), elem.Name, sub_material.Name))
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            result.append((elem.id(), elem.Name, layer.Material.Name))
    return result


async def list_all_related_materials(session: Session, object_id: int) -> list[tuple]:
    """List all materials associated with a specific element ID."""
    model = get_active_model(session)
    entity = model.by_id(object_id)
    if not entity:
        return []
    result: list[tuple] = []
    for assoc in getattr(entity, "HasAssociations", []):
        if not assoc.is_a("IfcRelAssociatesMaterial"):
            continue
        material = assoc.RelatingMaterial
        if material.is_a("IfcMaterial"):
            result.append((entity.id(), entity.Name, material.Name))
        elif material.is_a("IfcMaterialList"):
            for sub_material in material.Materials:
                result.append((entity.id(), entity.Name, sub_material.Name))
        elif material.is_a("IfcMaterialLayerSetUsage"):
            for layer in material.ForLayerSet.MaterialLayers:
                result.append((entity.id(), entity.Name, layer.Material.Name))
    return result


async def get_object_geometry_properties(session: Session, object_id: int) -> dict:
    """Return quantity take-off data (QTO property sets) for a given entity ID."""
    model = get_active_model(session)
    entity = model.by_id(object_id)
    if not entity:
        return {"error": f"No entity found with ID {object_id}."}
    return ifcopenshell.util.element.get_psets(entity, qtos_only=True)


async def filter_elements_by_query(session: Session, query: str) -> list[dict]:
    """Filter IFC elements using ifcopenshell selector syntax."""
    model = get_active_model(session)
    try:
        elements = ifcopenshell.util.selector.filter_elements(model, query)
        return [
            {"id": entity.id(), "class": entity.is_a(), "name": getattr(entity, "Name", None)}
            for entity in elements
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


async def get_applicable_psets(session: Session, entity_type: str) -> list[str]:
    """Return all standard Property Set Template names applicable to an IFC entity type."""
    model = get_active_model(session)
    try:
        templates = ifcopenshell.util.pset.PsetQto(model.schema)
        return templates.get_applicable_names(entity_type)
    except Exception as exc:
        return [f"Error: {exc}"]


async def get_schema_entity_info(session: Session, entity_name: str) -> dict:
    """Query the IFC schema definition for an entity type."""
    model = get_active_model(session)
    try:
        schema = ifcopenshell.schema_by_name(model.schema)
        declaration = schema.declaration_by_name(entity_name)
        return {
            "name": declaration.name(),
            "schema": model.schema,
            "is_abstract": declaration.is_abstract(),
            "supertype": declaration.supertype().name() if declaration.supertype() else None,
            "subtypes": [subtype.name() for subtype in declaration.subtypes()],
            "own_attributes": [attr.name() for attr in declaration.attributes()],
            "all_attributes": [attr.name() for attr in declaration.all_attributes()],
        }
    except Exception as exc:
        return {"error": str(exc)}


async def load_ifc_model(session: Session, path: str) -> str:
    """Load an IFC model from a file path, replacing the current active model."""
    if not os.path.exists(path):
        return f"Error: File not found at '{path}'."
    try:
        model = await run_in_executor(ifcopenshell.open, path)
        reinitialize_session(session, model)
        session.ifc_path = path
        session.ifc_filename = os.path.basename(path)
        return f"Success! Loaded '{os.path.basename(path)}'."
    except Exception as exc:
        return f"Error loading model: {exc}"


async def save_ifc_model(session: Session, filename: str) -> str:
    """Save the current active IFC model to a file."""
    model = get_active_model(session)
    if not filename.lower().endswith(".ifc"):
        filename += ".ifc"
    save_path = os.path.abspath(filename)

    def _write() -> None:
        model.write(save_path)

    try:
        await run_in_executor(_write)
        session.ifc_path = save_path
        session.ifc_filename = os.path.basename(save_path)
        return f"Success! Model saved to '{save_path}'."
    except Exception as exc:
        return f"Error saving model: {exc}"
