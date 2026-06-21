from __future__ import annotations

from typing import Any

from chat import _message_author, _message_date, _message_id
from threads import _cluster_threads, _guess_type


DEFAULT_LIMIT = 200
TEXT_PREVIEW_CHARS = 240


def _truncate(text: str, limit: int = TEXT_PREVIEW_CHARS) -> str:
    text = (text or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _maybe_truncate(text: str, limit: int | None) -> str:
    flat = (text or "").strip().replace("\n", " ").replace("\r", " ")
    if limit is None or limit <= 0:
        return flat
    return _truncate(flat, limit)


def build_digest(
    messages: list[dict[str, Any]],
    last_message_id: int,
    classified: dict[str, Any] | None = None,
    topics: dict[str, Any] | None = None,
    limit: int = DEFAULT_LIMIT,
    full_text: bool = False,
) -> dict[str, Any]:
    classified = classified or {}
    topics = topics or {}

    fresh = [m for m in messages if _message_id(m) > last_message_id]
    fresh.sort(key=_message_id)
    if limit > 0:
        fresh = fresh[-limit:]

    text_limit: int | None = None if full_text else TEXT_PREVIEW_CHARS
    items: list[dict[str, Any]] = []
    authors: list[str] = []
    seen = set()
    for msg in fresh:
        mid = _message_id(msg)
        meta = classified.get(str(mid)) or {}
        text = (msg.get("text") or "").strip()
        item = {
            "message_id": mid,
            "date": _message_date(msg),
            "username": _message_author(msg),
            "text": _maybe_truncate(text, text_limit),
            "text_full": text,
            "type": meta.get("type") or _guess_type(text),
            "topic": meta.get("topic"),
            "relevant": bool(meta.get("relevant")),
            "_raw": msg,
        }
        items.append(item)
        if item["username"] not in seen:
            seen.add(item["username"])
            authors.append(item["username"])

    threads = _cluster_threads(items, _message_date)
    new_cursor = last_message_id
    if fresh:
        new_cursor = max(_message_id(m) for m in fresh)

    return {
        "ok": True,
        "count": len(fresh),
        "authors": authors,
        "new_cursor": new_cursor,
        "items": items,
        "threads": threads,
        "topics": topics,
    }
