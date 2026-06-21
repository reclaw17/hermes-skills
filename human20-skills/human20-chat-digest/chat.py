from __future__ import annotations

from typing import Any


def _normalize_messages(chat_payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(chat_payload, list):
        return [m for m in chat_payload if isinstance(m, dict)]
    if isinstance(chat_payload, dict):
        for key in ("messages", "items", "data", "result", "chat"):
            value = chat_payload.get(key)
            if isinstance(value, list):
                return [m for m in value if isinstance(m, dict)]
            if isinstance(value, dict):
                inner = value.get("messages") or value.get("items")
                if isinstance(inner, list):
                    return [m for m in inner if isinstance(inner, list) and isinstance(m, dict)]
    return []


def _message_id(msg: dict[str, Any]) -> int:
    raw = msg.get("message_id") or msg.get("id") or 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _message_author(msg: dict[str, Any]) -> str:
    return (
        msg.get("username")
        or msg.get("author")
        or msg.get("from")
        or (str(msg.get("user_id")) if msg.get("user_id") is not None else "unknown")
    )


def _message_date(msg: dict[str, Any]) -> str:
    return msg.get("date") or msg.get("ts") or ""


def fetch_chat(client) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    raw = client.structured_tool("get_workshop_chat_json", {})
    chat_meta: dict[str, Any] | None = None
    if isinstance(raw, dict):
        chat_meta = {
            k: raw[k]
            for k in ("chat_id", "chat_type", "title", "username", "link")
            if k in raw
        }
    return _normalize_messages(raw), chat_meta


normalize_messages = _normalize_messages
message_id = _message_id
message_author = _message_author
message_date = _message_date
