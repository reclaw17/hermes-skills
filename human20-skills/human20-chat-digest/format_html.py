from __future__ import annotations

from typing import Any

from format_human import format_human


def format_human_html(digest: dict[str, Any], chat_meta: dict[str, Any] | None = None) -> str:
    return format_human(digest, chat_meta=chat_meta, fmt="html")
