from __future__ import annotations

import re
from datetime import datetime
from typing import Any


LINK_RE = re.compile(r"https?://|t\.me/|\bPR\b|\bgithub\.com/")
LONG_TEXT_CHARS = 400

TYPE_ICONS = {
    "question": "❓",
    "answer": "✅",
    "discussion": "💬",
    "announcement": "📢",
    "tooling": "🛠",
    "bug": "🐛",
    "link": "🔗",
    "media": "🖼",
}


def _guess_type(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "discussion"
    stripped = t.rstrip()
    if stripped.endswith("?") or stripped.rstrip(")").endswith("?"):
        return "question"
    if LINK_RE.search(t):
        return "link"
    if len(t) > LONG_TEXT_CHARS:
        return "discussion"
    return "discussion"


def _finalize_thread(items: list[dict[str, Any]]) -> dict[str, Any]:
    first_id = items[0]["message_id"]
    topic_id = f"t_{first_id}"
    topic = items[0].get("topic")
    if not topic:
        from collections import Counter

        topics_seen = [it.get("topic") for it in items if it.get("topic")]
        if topics_seen:
            topic = Counter(topics_seen).most_common(1)[0][0]
    relevant = any(it.get("relevant") for it in items)
    has_question = any(it.get("type") == "question" for it in items)
    last = items[-1]
    has_answer = last.get("type") == "answer" or (
        has_question and last.get("username") != items[0].get("username")
    )
    status = "answered" if has_question and has_answer else "open"
    return {
        "topic_id": topic_id,
        "title": topic or "обсуждение",
        "relevant": relevant,
        "status": status,
        "items": items,
    }


def _cluster_threads(
    items: list[dict[str, Any]],
    message_date,
    gap_minutes: int = 5,
    merge_by_topic: bool = True,
) -> list[dict[str, Any]]:
    if not items:
        return []

    def _ts(it: dict[str, Any]) -> datetime | None:
        d = message_date(it.get("_raw", {})) or it.get("date")
        if not d:
            return None
        try:
            return datetime.fromisoformat(str(d).replace("Z", "+00:00"))
        except Exception:
            return None

    threads: list[dict[str, Any]] = []
    cur: list[dict[str, Any]] = [items[0]]

    for it in items[1:]:
        ts = _ts(it)
        prev_ts = _ts(cur[-1])
        same_topic = merge_by_topic and it.get("topic") and it.get("topic") == cur[0].get("topic")
        time_close = ts and prev_ts and (ts - prev_ts).total_seconds() <= gap_minutes * 60

        if same_topic or (time_close and not (it.get("topic") or cur[0].get("topic"))):
            cur.append(it)
        else:
            threads.append(_finalize_thread(cur))
            cur = [it]
    if cur:
        threads.append(_finalize_thread(cur))

    threads.sort(
        key=lambda t: (
            0 if t.get("relevant") else 1,
            -(_ts(t["items"][-1]) or datetime.min).timestamp(),
        )
    )
    return threads


guess_type = _guess_type
cluster_threads = _cluster_threads
finalize_thread = _finalize_thread
