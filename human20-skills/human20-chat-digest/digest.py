#!/usr/bin/env python3
"""human20-chat-digest CLI entrypoint."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from builder import DEFAULT_LIMIT, build_digest
from chat import fetch_chat
from format_human import format_human
from state import _load_state, _save_state, apply_classification

HUMAN20_HELPER_DIR = Path("/home/hermes-agent/.hermes/skills/human20-helper")
sys.path.insert(0, str(HUMAN20_HELPER_DIR / "scripts"))

try:
    from human20_mcp_client import Human20McpClient, Human20McpError  # type: ignore
except Exception as exc:  # pragma: no cover - среда не готова
    print(json.dumps({"ok": False, "error": f"human20_mcp_client недоступен: {exc}"}, ensure_ascii=False))
    raise SystemExit(2)


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
    parser.add_argument(
        "--full",
        action="store_true",
        help="не обрезать тексты сообщений (для LLM-анализа)",
    )
    parser.add_argument(
        "--format",
        choices=["html", "md2"],
        default="html",
        help="формат вывода: html (Telegram HTML, по умолчанию) или md2 (MarkdownV2)",
    )
    parser.add_argument(
        "--apply-classification",
        type=str,
        default=None,
        help="путь к JSON с классификацией от LLM (записывается в state)",
    )
    args = parser.parse_args(argv)

    state = _load_state()
    cursor = (
        args.since_message_id
        if args.since_message_id is not None
        else state.get("last_message_id", 0)
    )
    if args.reset:
        cursor = 0

    if args.apply_classification:
        try:
            cls = json.loads(Path(args.apply_classification).read_text(encoding="utf-8"))
            apply_classification(state, cls)
            _save_state(state)
            print(json.dumps({"ok": True, "applied": len(cls.get("items", {}))}, ensure_ascii=False))
            return 0
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
            return 1

    try:
        client = Human20McpClient()
        messages, chat_meta = fetch_chat(client)
    except Human20McpError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"fetch failed: {exc}"}, ensure_ascii=False))
        return 1

    digest = build_digest(
        messages,
        cursor,
        classified=state.get("classified"),
        topics=state.get("topics"),
        limit=args.limit,
        full_text=args.full,
    )

    if not args.dry_run and digest["count"] > 0:
        state["last_message_id"] = digest["new_cursor"]
        _save_state(state)

    if args.json:
        out = dict(digest)
        if chat_meta:
            out["chat"] = chat_meta
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(format_human(digest, chat_meta=chat_meta, fmt=args.format))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
