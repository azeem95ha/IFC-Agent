from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CreateIfcEntityInput(BaseModel):
    entity_type: str = Field(
        ...,
        description="Building element type: 'wall', 'beam', 'column', 'slab', or 'roof'.",
    )
    type_name: str = Field(
        ...,
        description="Unique name for the IFC type definition, e.g. 'W-01' or 'SLAB-C30'.",
    )
    dimensions: dict[str, Any] = Field(
        ...,
        description=(
            "All dimension values in METRES:\n"
            "  wall   -> {length, height, thickness}\n"
            "  beam   -> {width, height, length}\n"
            "  column -> {width, height, length}\n"
            "  slab   -> {length, width, thickness}\n"
            "  roof   -> {length, width, thickness, pitch}  (pitch in degrees)"
        ),
    )
    instance_name: str | None = Field(
        None, description="Optional unique name for this element instance."
    )
    placement: list[float] = Field(
        default_factory=lambda: [0.0, 0.0, 0.0, 0.0],
        description="[x, y, z, rotation_z_degrees] in metres.",
    )

    @field_validator("dimensions", mode="before")
    @classmethod
    def _parse_dimensions(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError("dimensions must be a valid JSON object") from exc
        return value
