from __future__ import annotations

import asyncio
import inspect
import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

try:
    from ..models.chat import DoneEvent, ErrorEvent, MessageEvent, ThinkingEvent, ToolCallEvent, ToolResultEvent
    from ..models.ifc_entities import CreateIfcEntityInput
    from ..models.session import Session
    from ..tools import authoring_tools, geometry_tools, query_tools
except ImportError:
    from models.chat import DoneEvent, ErrorEvent, MessageEvent, ThinkingEvent, ToolCallEvent, ToolResultEvent
    from models.ifc_entities import CreateIfcEntityInput
    from models.session import Session
    from tools import authoring_tools, geometry_tools, query_tools


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompt.md"

TOOL_SPECS: list[tuple[Any, type | None]] = [
    (query_tools.get_project_info, None),
    (query_tools.list_all_types, None),
    (query_tools.list_all_objects, None),
    (query_tools.list_entities, None),
    (query_tools.get_objects_count, None),
    (query_tools.get_object_info, None),
    (query_tools.list_all_materials, None),
    (query_tools.list_all_related_materials, None),
    (query_tools.get_object_geometry_properties, None),
    (query_tools.filter_elements_by_query, None),
    (query_tools.get_applicable_psets, None),
    (query_tools.get_schema_entity_info, None),
    (geometry_tools.get_object_dims, None),
    (geometry_tools.get_min_max_3dcoords, None),
    (geometry_tools.get_takeoffs, None),
    (geometry_tools.calculate_distance_between_2_shapes, None),
    (geometry_tools.find_nearby_elements, None),
    (geometry_tools.detect_clashes, None),
    (geometry_tools.validate_model, None),
    (query_tools.load_ifc_model, None),
    (query_tools.save_ifc_model, None),
    (authoring_tools.create_ifc_entity, CreateIfcEntityInput),
    (authoring_tools.edit_entity_location, None),
    (authoring_tools.rotate_entity, None),
    (authoring_tools.assign_material_to_entity, None),
    (authoring_tools.add_property_to_entity, None),
    (authoring_tools.remove_entities, None),
    (authoring_tools.create_spatial_structure, None),
    (authoring_tools.assign_to_spatial_container, None),
]


class StreamingCallbackHandler(AsyncCallbackHandler):
    def __init__(self, queue: asyncio.Queue[Any]) -> None:
        self.queue = queue
        self._announced_thinking = False
        self._tool_names: dict[str, str] = {}

    async def on_chat_model_start(self, *args: Any, **kwargs: Any) -> None:
        if not self._announced_thinking:
            self._announced_thinking = True
            await self.queue.put(ThinkingEvent(content="Planning the next steps and preparing tool calls."))

    async def on_tool_start(self, serialized: dict[str, Any], input_str: str, *, run_id: UUID, **kwargs: Any) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        self._tool_names[str(run_id)] = tool_name
        payload: dict[str, object]
        try:
            raw = json.loads(input_str) if input_str else {}
            payload = raw if isinstance(raw, dict) else {"input": raw}
        except json.JSONDecodeError:
            payload = {"input": input_str}
        await self.queue.put(ToolCallEvent(tool=tool_name, input=payload))

    async def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        tool_name = self._tool_names.pop(str(run_id), "unknown_tool")
        await self.queue.put(ToolResultEvent(tool=tool_name, output=self._stringify(output)))

    async def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        tool_name = self._tool_names.pop(str(run_id), "unknown_tool")
        await self.queue.put(ErrorEvent(message=f"{tool_name}: {error}"))

    @staticmethod
    def _stringify(output: Any) -> str:
        if isinstance(output, str):
            return output
        try:
            return json.dumps(output, ensure_ascii=True, default=str)
        except TypeError:
            return str(output)


def _load_system_prompt(current_ifc_path: str | None) -> str:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    active_path = current_ifc_path or "None"
    if "{current_ifc_path}" in prompt:
        prompt = prompt.replace("{current_ifc_path}", active_path)
    else:
        prompt = (
            f"{prompt}\n\n"
            "## Active IFC File\n"
            f"`{active_path}`\n\n"
            "Use that exact path for any tool that requires a file path argument."
        )
    return prompt


def _make_bound_coroutine(session: Session, fn: Any):
    async def bound_tool(*args: Any, **kwargs: Any):
        return await fn(session, *args, **kwargs)

    original_signature = inspect.signature(fn)
    remaining_params = list(original_signature.parameters.values())[1:]
    bound_tool.__name__ = fn.__name__
    bound_tool.__doc__ = inspect.getdoc(fn) or ""
    bound_tool.__signature__ = original_signature.replace(parameters=remaining_params)
    bound_tool.__annotations__ = {
        key: value for key, value in fn.__annotations__.items() if key != "session"
    }
    return bound_tool


def _bind_tool(session: Session, fn: Any, args_schema: type | None):
    bound = _make_bound_coroutine(session, fn)
    return tool(
        name_or_callable=bound,
        description=inspect.getdoc(fn),
        args_schema=args_schema,
        infer_schema=True,
        parse_docstring=False,
    )


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            else:
                parts.append(str(item))
        normalized = "\n\n".join(part.strip() for part in parts if part and part.strip())
        return normalized or str(content)
    return str(content)


def build_agent(session: Session, api_key: str):
    resolved_api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
    if not resolved_api_key:
        raise ValueError("A Google API key is required.")

    session.api_key = resolved_api_key
    tools = [_bind_tool(session, fn, args_schema) for fn, args_schema in TOOL_SPECS]
    system_prompt = _load_system_prompt(session.ifc_path)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        google_api_key=resolved_api_key,
    )
    return create_react_agent(model=llm, tools=tools, prompt=system_prompt)


async def run_agent_streaming(session: Session, message: str, api_key: str, queue: asyncio.Queue[Any]) -> None:
    if session.active_model is None:
        await queue.put(MessageEvent(content="Please upload an IFC file first."))
        await queue.put(DoneEvent())
        return

    try:
        agent = build_agent(session, api_key)
        callback = StreamingCallbackHandler(queue)
        messages = list(session.chat_history) + [HumanMessage(content=message)]
        result = await agent.ainvoke(
            {"messages": messages},
            config={"callbacks": [callback], "recursion_limit": 30},
        )
        final_message = result["messages"][-1] if result.get("messages") else None
        if not isinstance(final_message, AIMessage):
            raise ValueError("Agent did not return a valid AI response.")

        content = _extract_text_content(final_message.content)
        session.chat_history.extend([HumanMessage(content=message), AIMessage(content=content)])
        await queue.put(MessageEvent(content=content))
    except Exception as exc:
        await queue.put(ErrorEvent(message=str(exc)))
    finally:
        await queue.put(DoneEvent())
