#!/usr/bin/env python3
"""
human20-chat-digest — дайджест новых сообщений из чата Human 2.0.

Читает через human20-helper / human20_mcp_client.get_workshop_chat_json.
Хранит курсор (last_message_id) в state.json рядом со скриптом.
По умолчанию read-only: ничего не пишет в Human20, ничего не отправляет.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Импортируем готовый клиент из соседнего скилла.
HUMAN20_HELPER_DIR = Path("/home/hermes-agent/.hermes/skills/human20-helper")
sys.path.insert(0, str(HUMAN20_HELPER_DIR / "scripts"))

try:
    from human20_mcp_client import Human20McpClient, Human20McpError  # type: ignore
except Exception as exc:  # pragma: no cover - среда не готова
    print(
        json.dumps(
            {"ok": False, "error": f"human20_mcp_client недоступен: {exc}"},
            ensure_ascii=False,
        )
    )
    sys.exit(2)

SKILL_DIR = Path(__file__).resolve().parent
STATE_PATH = SKILL_DIR / "state.json"
DEFAULT_LIMIT = 200
TEXT_PREVIEW_CHARS = 240


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"last_message_id": 0, "last_run_at": None}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        # Повреждённый state.json — безопасный сброс.
        return {"last_message_id": 0, "last_run_at": None}


def _save_state(state: dict[str, Any]) -> None:
    state["last_run_at"] = datetime.now(timezone.utc).isoformat()
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        os.chmod(STATE_PATH, 0o600)
    except Exception:
        pass


def _truncate(text: str, limit: int = TEXT_PREVIEW_CHARS) -> str:
    text = (text or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _normalize_messages(chat_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Привести разные формы ответа Human20 к единому списку."""
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
                    return [m for m in inner if isinstance(m, dict)]
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


def fetch_chat(client: Human20McpClient) -> list[dict[str, Any]]:
    """Получить все сообщения чата через MCP."""
    raw = client.structured_tool("get_workshop_chat_json", {})
    return _normalize_messages(raw)


def build_digest(
    messages: list[dict[str, Any]],
    last_message_id: int,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Отфильтровать новые сообщения и сформировать дайджест."""
    fresh = [m for m in messages if _message_id(m) > last_message_id]
    fresh.sort(key=_message_id)
    if limit > 0:
        fresh = fresh[-limit:]

    authors: list[str] = []
    seen = set()
    for msg in fresh:
        author = _message_author(msg)
        if author not in seen:
            seen.add(author)
            authors.append(author)

    items = [
        {
            "message_id": _message_id(msg),
            "date": msg.get("date"),
            "username": _message_author(msg),
            "preview": _truncate(msg.get("text", "")),
        }
        for msg in fresh
    ]

    new_cursor = last_message_id
    if fresh:
        new_cursor = max(_message_id(m) for m in fresh)

    return {
        "ok": True,
        "count": len(fresh),
        "authors": authors,
        "new_cursor": new_cursor,
        "items": items,
    }


def format_human(digest: dict[str, Any]) -> str:
    """Красиво для Telegram/чата."""
    if not digest.get("ok"):
        return f"⚠️ human20-chat-digest: {digest.get('error', 'unknown error')}"
    count = digest["count"]
    if count == 0:
        return "💤 В чате Human 2.0 нового ничего нет."
    authors = digest["authors"]
    lines = [
        f"📨 Human 2.0 чат: +{count} сообщений от {len(authors)} авторов",
    ]
    if authors:
        lines.append("👤 " + ", ".join(f"@{a}" for a in authors[:8]))
        if len(authors) > 8:
            lines.append(f"   …и ещё {len(authors) - 8}")
    lines.append("")
    for item in digest["items"][:10]:
        date = (item.get("date") or "")[:16].replace("T", " ")
        uname = item.get("username") or "?"
        lines.append(f"• [{date}] @{uname} (#{item['message_id']})")
        lines.append(f"  {item['preview']}")
    if len(digest["items"]) > 10:
        lines.append(f"\n…и ещё {len(digest['items']) - 10} сообщений")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Human20 chat digest")
    parser.add_argument("--dry-run", action="store_true", help="не сохранять state.json")
    parser.add_argument("--reset", action="store_true", help="начать с нуля")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument(
        "--since-message-id",
        type=int,
        default=None,
        help="явный курсор, перекрывает state.json",
    )
    parser.add_argument("--json", action="store_true", help="вывести JSON вместо текста")
    args = parser.parse_args(argv)

    state = _load_state()
    cursor = args.since_message_id if args.since_message_id is not None else state.get("last_message_id", 0)
    if args.reset:
        cursor = 0

    try:
        client = Human20McpClient()
        messages = fetch_chat(client)
    except Human20McpError as exc:
        print(
            json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False),
            file=sys.stdout,
        )
        return 1
    except Exception as exc:  # network / json / etc.
        print(
            json.dumps({"ok": False, "error": f"fetch failed: {exc}"}, ensure_ascii=False),
            file=sys.stdout,
        )
        return 1

    digest = build_digest(messages, cursor, limit=args.limit)

    if not args.dry_run and digest["count"] > 0:
        state["last_message_id"] = digest["new_cursor"]
        _save_state(state)

    if args.json:
        print(json.dumps(digest, ensure_ascii=False, indent=2))
    else:
        print(format_human(digest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())