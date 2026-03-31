from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    api_key: str


class ThinkingEvent(BaseModel):
    type: Literal["thinking"] = "thinking"
    content: str


class ToolCallEvent(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    tool: str
    input: dict[str, object]


class ToolResultEvent(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool: str
    output: str


class MessageEvent(BaseModel):
    type: Literal["message"] = "message"
    content: str


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"


SSEEvent = Annotated[
    ThinkingEvent | ToolCallEvent | ToolResultEvent | MessageEvent | ErrorEvent | DoneEvent,
    Field(discriminator="type"),
]
