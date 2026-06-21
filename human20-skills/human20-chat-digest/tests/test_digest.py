from __future__ import annotations

from builder import build_digest
from format_human import format_human


def test_build_digest_and_render_end_to_end():
    messages = [
        {
            "message_id": 10,
            "date": "2026-06-20T10:00:00+00:00",
            "username": "ChipCR",
            "text": "Ищу запись сегодняшнего созвона?",
            "chat_id": -1003598068116,
        },
        {
            "message_id": 11,
            "date": "2026-06-20T10:01:00+00:00",
            "username": "Alexey_Petryashev",
            "text": "в процессе",
            "chat_id": -1003598068116,
        },
    ]
    digest = build_digest(messages, last_message_id=0, limit=5)
    out = format_human(digest, chat_meta={"chat_id": -1003598068116}, fmt="html")

    assert digest["count"] == 2
    assert digest["new_cursor"] == 11
    assert "Human 2.0" in out
    assert "https://t.me/c/3598068116/11" in out
