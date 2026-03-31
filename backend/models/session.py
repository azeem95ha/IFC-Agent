from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Session:
    session_id: str
    api_key: str | None = None
    active_model: Any | None = None
    ifc_path: str | None = None
    ifc_filename: str | None = None
    chat_history: list[Any] = field(default_factory=list)
    ifc_types: dict[str, Any] = field(default_factory=dict)
    ifc_instances: dict[str, Any] = field(default_factory=dict)
    ifc_materials: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    last_active: datetime = field(default_factory=utc_now)

    @property
    def has_model(self) -> bool:
        return self.active_model is not None


class SessionMeta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    has_model: bool
    ifc_filename: str | None
    created_at: datetime
    last_active: datetime

    @classmethod
    def from_session(cls, session: Session) -> "SessionMeta":
        return cls(
            session_id=session.session_id,
            has_model=session.has_model,
            ifc_filename=session.ifc_filename,
            created_at=session.created_at,
            last_active=session.last_active,
        )


class ModelInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    filename: str
    size_bytes: int
    schema_name: str = Field(alias="schema", serialization_alias="schema")
    entity_count: int
