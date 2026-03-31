from __future__ import annotations

import logging
from typing import Any

import ifcopenshell.geom
import ifcopenshell.util.shape
import numpy as np

try:
    from ..models.session import Session
    from ..utils.thread_pool import CPU_WORKERS
except ImportError:
    from models.session import Session
    from utils.thread_pool import CPU_WORKERS

try:
    from .common import ALL_IFC_ENTITIES, get_active_model, run_in_executor
except ImportError:
    from tools.common import ALL_IFC_ENTITIES, get_active_model, run_in_executor


async def get_object_dims(session: Session, object_id: int) -> dict:
    """Get bounding-box dimensions (X, Y, Z in metres) of an element by its step ID."""
    model = get_active_model(session)

    def _compute():
        entity = model.by_id(object_id)
        if not entity:
            return {"error": f"No entity with ID {object_id}."}
        try:
            settings = ifcopenshell.geom.settings()
            shape = ifcopenshell.geom.create_shape(settings, entity)
            vertices = ifcopenshell.util.shape.get_vertices(shape.geometry, is_2d=False)
            low, high = ifcopenshell.util.shape.get_bbox(vertices)
            dims = np.round(np.abs(np.subtract(high, low)), 4).tolist()
            return {"X-DIM": dims[0], "Y-DIM": dims[1], "Z-DIM": dims[2]}
        except Exception as exc:
            return {"error": str(exc)}

    return await run_in_executor(_compute)


async def get_min_max_3dcoords(session: Session, entity_id: int) -> dict:
    """Get the minimum and maximum world-space 3D coordinates of an element."""
    model = get_active_model(session)

    def _compute():
        entity = model.by_id(entity_id)
        if not entity:
            return {"error": f"No entity with ID {entity_id}."}
        try:
            settings = ifcopenshell.geom.settings()
            shape = ifcopenshell.geom.create_shape(settings, entity)
            vertices = ifcopenshell.util.shape.get_vertices(shape.geometry)
            return {
                "min_coord": np.amin(vertices, axis=0).tolist(),
                "max_coord": np.amax(vertices, axis=0).tolist(),
            }
        except Exception as exc:
            return {"error": str(exc)}

    return await run_in_executor(_compute)


async def get_takeoffs(session: Session, object_type: str) -> dict:
    """Compute total surface area and volume for all elements matching 'object_type'."""
    model = get_active_model(session)

    def _compute():
        target_ids: set[int] = set()
        for entity_name in ALL_IFC_ENTITIES:
            if object_type.lower() in entity_name.lower():
                target_ids.update(entity.id() for entity in model.by_type(entity_name))

        if not target_ids:
            return {
                "total_area": 0.0,
                "total_volume": 0.0,
                "warning": f"No elements matching '{object_type}' found.",
            }

        settings = ifcopenshell.geom.settings()
        iterator = ifcopenshell.geom.iterator(settings, model, CPU_WORKERS)
        total_area = 0.0
        total_volume = 0.0

        if iterator.initialize():
            while True:
                shape = iterator.get()
                if shape.id in target_ids:
                    try:
                        total_volume += ifcopenshell.util.shape.get_volume(shape.geometry)
                        total_area += ifcopenshell.util.shape.get_area(shape.geometry)
                    except Exception:
                        pass
                if not iterator.next():
                    break

        return {
            "total_area": round(total_area, 4),
            "total_volume": round(total_volume, 4),
        }

    return await run_in_executor(_compute)


async def calculate_distance_between_2_shapes(session: Session, entity_id_1: int, entity_id_2: int) -> Any:
    """Calculate the centroid-to-centroid distance (metres) between two IFC elements."""
    model = get_active_model(session)

    def _compute():
        entity_1 = model.by_id(entity_id_1)
        entity_2 = model.by_id(entity_id_2)
        if not entity_1 or not entity_2:
            return f"Error: entity {entity_id_1} or {entity_id_2} not found."
        try:
            settings = ifcopenshell.geom.settings()
            shape_1 = ifcopenshell.geom.create_shape(settings, entity_1)
            shape_2 = ifcopenshell.geom.create_shape(settings, entity_2)
            center_1 = ifcopenshell.util.shape.get_shape_bbox_centroid(shape_1, shape_1.geometry)
            center_2 = ifcopenshell.util.shape.get_shape_bbox_centroid(shape_2, shape_2.geometry)
            return round(float(np.linalg.norm(np.subtract(center_1, center_2))), 4)
        except Exception as exc:
            return f"Error: {exc}"

    return await run_in_executor(_compute)


async def find_nearby_elements(session: Session, entity_id: int, range: float) -> Any:
    """Find all IFC elements within 'range' metres of the given element."""
    model = get_active_model(session)

    def _compute():
        source = model.by_id(entity_id)
        if not source:
            return f"Error: entity {entity_id} not found."
        try:
            settings = ifcopenshell.geom.settings()
            tree = ifcopenshell.geom.tree()
            iterator = ifcopenshell.geom.iterator(settings, model, CPU_WORKERS)
            if iterator.initialize():
                tree.add_elements_in_iterator(iterator)
            nearby = tree.select_box(source, extend=range)
            return [
                {"id": entity.id(), "name": getattr(entity, "Name", None), "class": entity.is_a()}
                for entity in nearby
                if entity.id() != entity_id
            ]
        except Exception as exc:
            return f"Error: {exc}"

    return await run_in_executor(_compute)


async def detect_clashes(session: Session, type_a: str, type_b: str, tolerance: float = 0.002) -> Any:
    """Detect geometric clashes between two groups of IFC element types."""
    model = get_active_model(session)

    def _compute():
        group_a = model.by_type(type_a)
        group_b = model.by_type(type_b)
        if not group_a:
            return {"error": f"No elements of type '{type_a}' found."}
        if not group_b:
            return {"error": f"No elements of type '{type_b}' found."}
        try:
            settings = ifcopenshell.geom.settings()
            tree = ifcopenshell.geom.tree()
            iterator = ifcopenshell.geom.iterator(settings, model, CPU_WORKERS)
            if iterator.initialize():
                tree.add_elements_in_iterator(iterator)
            clashes = tree.clash_intersection_many(group_a, group_b, tolerance=tolerance, check_all=True)
            results = [
                {
                    "element_a": {"id": clash.a.id(), "name": getattr(clash.a, "Name", None)},
                    "element_b": {"id": clash.b.id(), "name": getattr(clash.b, "Name", None)},
                    "penetration_m": round(float(clash.distance), 5),
                }
                for clash in clashes
            ]
            return {"total_clashes": len(results), "clashes": results}
        except Exception as exc:
            return {"error": str(exc)}

    return await run_in_executor(_compute)


async def validate_model(session: Session) -> dict:
    """Validate the active IFC model against the IFC schema specification."""
    model = get_active_model(session)

    def _compute():
        try:
            import ifcopenshell.validate as ifc_validate

            issues: list[dict] = []

            if hasattr(ifc_validate, "json_logger"):
                logger = ifc_validate.json_logger()
                ifc_validate.validate(model, logger, express_rules=True)
                raw = getattr(logger, "statements", [])
                issues = raw if isinstance(raw, list) else list(raw)
            else:
                class Handler(logging.Handler):
                    def __init__(self):
                        super().__init__()
                        self.records: list[dict] = []

                    def emit(self, record: logging.LogRecord) -> None:
                        self.records.append({"level": record.levelname, "message": record.getMessage()})

                handler = Handler()
                logger = logging.getLogger("ifcopenshell.validate")
                logger.addHandler(handler)
                logger.setLevel(logging.WARNING)
                try:
                    ifc_validate.validate(model, logger, express_rules=True)
                finally:
                    logger.removeHandler(handler)
                issues = handler.records

            return {
                "valid": len(issues) == 0,
                "issue_count": len(issues),
                "issues": issues[:50],
            }
        except Exception as exc:
            return {"error": f"Validation error: {exc}"}

    return await run_in_executor(_compute)
