from __future__ import annotations

from typing import Any

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.type
import ifcopenshell.api.unit
import ifcopenshell.util.placement
import ifcopenshell.util.shape_builder
import numpy as np

try:
    from ..models.session import Session
except ImportError:
    from models.session import Session

try:
    from .common import get_active_model, get_body_context, ifc_value, run_in_executor
except ImportError:
    from tools.common import get_active_model, get_body_context, ifc_value, run_in_executor


async def create_ifc_entity(session: Session, **kwargs) -> str:
    """Create a physical building element in the active model."""
    model = get_active_model(session)
    ifc_path = session.ifc_path
    ifc_types = session.ifc_types
    ifc_instances = session.ifc_instances

    def _create():
        entity_type: str = kwargs["entity_type"]
        type_name: str = kwargs["type_name"]
        dimensions: dict[str, Any] = kwargs["dimensions"]
        instance_name: str | None = kwargs.get("instance_name")
        placement: list[float] = kwargs.get("placement", [0.0, 0.0, 0.0, 0.0])

        if not model.by_type("IfcProject"):
            ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name="New Project")
            ifcopenshell.api.unit.assign_unit(model)

        body_ctx = get_body_context(model)

        matrix = np.eye(4)
        if placement[3] != 0:
            matrix = ifcopenshell.util.placement.rotation(float(placement[3]), "Z")
        matrix[:, 3][:3] = placement[:3]

        type_map = {
            "wall": "IfcWallType",
            "beam": "IfcBeamType",
            "column": "IfcColumnType",
            "slab": "IfcSlabType",
            "roof": "IfcRoofType",
        }
        type_class = type_map.get(entity_type)
        if not type_class:
            return f"Error: Unknown entity type '{entity_type}'. Choose from: {list(type_map)}."
        if type_name not in ifc_types:
            ifc_types[type_name] = ifcopenshell.api.root.create_entity(model, ifc_class=type_class, name=type_name)

        builder = ifcopenshell.util.shape_builder.ShapeBuilder(model)
        representation = None

        try:
            if entity_type == "wall":
                representation = ifcopenshell.api.geometry.add_wall_representation(
                    model,
                    context=body_ctx,
                    length=dimensions["length"],
                    height=dimensions["height"],
                    thickness=dimensions["thickness"],
                )
            elif entity_type in ("beam", "column"):
                profile = model.create_entity(
                    "IfcRectangleProfileDef",
                    ProfileType="AREA",
                    XDim=float(dimensions["width"]) * 1000,
                    YDim=float(dimensions["height"]) * 1000,
                )
                representation = ifcopenshell.api.geometry.add_profile_representation(
                    model,
                    context=body_ctx,
                    profile=profile,
                    depth=float(dimensions["length"]),
                )
                if entity_type == "beam":
                    matrix = matrix @ ifcopenshell.util.placement.rotation(-90, "Y")
            elif entity_type == "slab":
                length_mm = float(dimensions["length"]) * 1000
                width_mm = float(dimensions["width"]) * 1000
                thickness_mm = float(dimensions["thickness"]) * 1000
                curve = builder.polyline([(0, 0), (length_mm, 0), (length_mm, width_mm), (0, width_mm)], closed=True)
                representation = ifcopenshell.api.geometry.add_profile_representation(
                    model,
                    context=body_ctx,
                    profile=builder.profile(curve),
                    depth=thickness_mm,
                )
            elif entity_type == "roof":
                length_mm = float(dimensions["length"]) * 1000
                width_mm = float(dimensions["width"]) * 1000
                thickness_mm = float(dimensions["thickness"]) * 1000
                pitch = float(dimensions.get("pitch", 0))
                if pitch == 0:
                    curve = builder.polyline([(0, 0), (length_mm, 0), (length_mm, width_mm), (0, width_mm)], closed=True)
                    representation = ifcopenshell.api.geometry.add_profile_representation(
                        model,
                        context=body_ctx,
                        profile=builder.profile(curve),
                        depth=thickness_mm,
                    )
                else:
                    peak = (width_mm / 2.0) * np.tan(np.radians(pitch))
                    points = np.array([[0, 0], [width_mm, 0], [width_mm, thickness_mm], [width_mm / 2.0, thickness_mm + peak], [0, thickness_mm]])
                    profile = builder.profile(builder.polyline(points, closed=True))
                    wedge = builder.extrude(profile, length_mm)
                    builder.rotate(wedge, ifcopenshell.util.placement.rotation(-90, "X"))
                    representation = builder.get_representation(context=body_ctx, items=[wedge])
        except Exception as exc:
            return f"Error building geometry for '{entity_type}': {exc}"

        instance_class = ifc_types[type_name].is_a().replace("Type", "")
        instance = ifcopenshell.api.root.create_entity(model, ifc_class=instance_class, name=instance_name)
        ifcopenshell.api.type.assign_type(model, related_objects=[instance], relating_type=ifc_types[type_name])
        ifcopenshell.api.geometry.edit_object_placement(model, product=instance, matrix=matrix, is_si=True)
        if representation:
            ifcopenshell.api.geometry.assign_representation(model, product=instance, representation=representation)
        if instance_name:
            ifc_instances[instance_name] = instance

        if ifc_path:
            model.write(ifc_path)

        return f"Success! Created {entity_type} '{instance_name or 'unnamed'}' (type='{type_name}', ID={instance.id()})."

    return await run_in_executor(_create)


async def edit_entity_location(session: Session, instance_id: int, new_location: list[float]) -> str:
    """Move an existing entity to a new absolute [x, y, z] world position."""
    model = get_active_model(session)
    ifc_path = session.ifc_path

    def _move():
        instance = model.by_id(instance_id)
        if not instance:
            return f"Error: No entity with ID {instance_id}."
        matrix = ifcopenshell.util.placement.get_local_placement(instance.ObjectPlacement)
        matrix[:, 3][:3] = new_location
        ifcopenshell.api.geometry.edit_object_placement(model, product=instance, matrix=matrix, is_si=True)
        if ifc_path:
            model.write(ifc_path)
        return f"Success! Moved entity {instance_id} to {new_location}."

    return await run_in_executor(_move)


async def rotate_entity(session: Session, instance_id: int, angle: float, axis: str) -> str:
    """Rotate an entity around its local origin by angle degrees on axis X, Y, or Z."""
    model = get_active_model(session)
    ifc_path = session.ifc_path

    def _rotate():
        instance = model.by_id(instance_id)
        if not instance:
            return f"Error: No entity with ID {instance_id}."
        current = ifcopenshell.util.placement.get_local_placement(instance.ObjectPlacement)
        rotation = ifcopenshell.util.placement.rotation(angle, axis.upper())
        ifcopenshell.api.geometry.edit_object_placement(model, product=instance, matrix=current @ rotation, is_si=True)
        if ifc_path:
            model.write(ifc_path)
        return f"Success! Rotated entity {instance_id} by {angle} degrees around {axis.upper()}."

    return await run_in_executor(_rotate)


async def assign_material_to_entity(session: Session, instance_id: int, material_name: str) -> str:
    """Assign a named material to an entity, creating it if needed."""
    model = get_active_model(session)
    ifc_path = session.ifc_path
    ifc_materials = session.ifc_materials

    def _assign():
        instance = model.by_id(instance_id)
        if not instance:
            return f"Error: No entity with ID {instance_id}."
        if material_name not in ifc_materials:
            ifc_materials[material_name] = ifcopenshell.api.material.add_material(model, name=material_name)
        ifcopenshell.api.material.assign_material(model, products=[instance], material=ifc_materials[material_name])
        if ifc_path:
            model.write(ifc_path)
        return f"Success! Assigned material '{material_name}' to entity {instance_id}."

    return await run_in_executor(_assign)


async def add_property_to_entity(session: Session, entity_id: int, pset_name: str, prop_name: str, prop_value: str | int | float | bool) -> str:
    """Add or update a named property under a given property set on an entity."""
    model = get_active_model(session)
    ifc_path = session.ifc_path

    def _add():
        entity = model.by_id(entity_id)
        if not entity:
            return f"Error: Entity {entity_id} not found."
        pset = ifcopenshell.api.pset.add_pset(model, product=entity, name=pset_name)
        ifcopenshell.api.pset.edit_pset(model, pset=pset, properties={prop_name: ifc_value(model, prop_value)})
        if ifc_path:
            model.write(ifc_path)
        return f"Success! Added '{prop_name}={prop_value}' to Pset '{pset_name}' on entity {entity_id}."

    return await run_in_executor(_add)


async def remove_entities(session: Session, object_id: int) -> str:
    """Permanently remove an entity from the active model by its step ID."""
    model = get_active_model(session)
    ifc_path = session.ifc_path

    def _remove():
        entity = model.by_id(object_id)
        if not entity:
            return f"Error: No entity with ID {object_id}."
        model.remove(entity)
        if ifc_path:
            model.write(ifc_path)
        return f"Success! Removed entity {object_id}."

    return await run_in_executor(_remove)


async def create_spatial_structure(session: Session, site_name: str = "Default Site", building_name: str = "Default Building", storey_names: list[str] | None = None) -> str:
    """Create a valid IFC spatial hierarchy."""
    model = get_active_model(session)
    ifc_path = session.ifc_path
    resolved_storey_names = storey_names if storey_names else ["Ground Floor"]

    def _create():
        projects = model.by_type("IfcProject")
        project = projects[0] if projects else ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name="New Project")
        if not projects:
            ifcopenshell.api.unit.assign_unit(model)

        site = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite", name=site_name)
        ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project, products=[site])

        building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding", name=building_name)
        ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site, products=[building])

        storey_ids: list[tuple[str, int]] = []
        for name in resolved_storey_names:
            storey = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name=name)
            ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, products=[storey])
            storey_ids.append((name, storey.id()))

        if ifc_path:
            model.write(ifc_path)

        lines = [
            "Success! Spatial structure created:",
            f"  Site     : '{site_name}' (ID: {site.id()})",
            f"  Building : '{building_name}' (ID: {building.id()})",
            "  Storeys  :",
        ]
        for name, storey_id in storey_ids:
            lines.append(f"    - '{name}' (ID: {storey_id})")
        return "\n".join(lines)

    return await run_in_executor(_create)


async def assign_to_spatial_container(session: Session, element_id: int, container_name: str) -> str:
    """Assign an IFC element to a spatial container identified by its Name."""
    model = get_active_model(session)
    ifc_path = session.ifc_path

    def _assign():
        element = model.by_id(element_id)
        if not element:
            return f"Error: Element {element_id} not found."

        container = None
        for spatial_class in ("IfcBuildingStorey", "IfcBuilding", "IfcSite", "IfcSpace"):
            for candidate in model.by_type(spatial_class):
                if getattr(candidate, "Name", None) == container_name:
                    container = candidate
                    break
            if container:
                break

        if not container:
            return f"Error: No spatial container named '{container_name}' found."

        ifcopenshell.api.run("spatial.assign_container", model, relating_structure=container, products=[element])
        if ifc_path:
            model.write(ifc_path)
        return f"Success! Assigned element {element_id} to '{container_name}'."

    return await run_in_executor(_assign)
