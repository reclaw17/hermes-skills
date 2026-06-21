from __future__ import annotations

from typing import Any

from formats import _fmt_bold, _fmt_escape, _fmt_italic, _html_escape, _md2_escape, _plural, _short_topic
from telegram import _telegram_link
from threads import TYPE_ICONS


def _truncate(text: str, limit: int = 240) -> str:
    text = (text or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _wrap_quote(text: str, width: int = 80, fmt: str = "html") -> list[str]:
    flat = (text or "").replace("\n", " ").replace("\r", " ").strip()
    if not flat:
        return [_fmt_escape("(пусто)", fmt)]
    words = flat.split()
    raw_lines: list[str] = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            if cur:
                raw_lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        raw_lines.append(cur)

    if fmt == "html":
        return [f"<blockquote>{_html_escape(l)}</blockquote>" for l in raw_lines]
    return [f"> {_md2_escape(l)}" for l in raw_lines]


def format_human(
    digest: dict[str, Any],
    chat_meta: dict[str, Any] | None = None,
    fmt: str = "html",
) -> str:
    if not digest.get("ok"):
        return f"⚠️ human20-chat-digest: {_fmt_escape(digest.get('error', 'unknown error'), fmt)}"

    count = digest["count"]
    if count == 0:
        return "💤 В чате Human 2.0 нового ничего нет."

    threads = digest.get("threads") or []
    if not threads:
        threads = [
            {
                "topic_id": "all",
                "title": "обсуждение",
                "status": "open",
                "items": digest["items"],
            }
        ]

    chat_id = (chat_meta or {}).get("chat_id") if chat_meta else None
    chat_username = (chat_meta or {}).get("username") if chat_meta else None
    if not chat_id and digest["items"]:
        chat_id = digest["items"][0].get("_raw", {}).get("chat_id")

    first_ts = (digest["items"][0].get("date") or "")[:16].replace("T", " ")
    last_ts = (digest["items"][-1].get("date") or "")[:16].replace("T", " ")
    authors = digest["authors"]

    author_counts: dict[str, int] = {}
    for it in digest["items"]:
        author_counts[it["username"]] = author_counts.get(it["username"], 0) + 1
    top_authors = sorted(author_counts.items(), key=lambda kv: -kv[1])[:3]

    if fmt == "html":
        CHECK_DONE = "✅"
        CHECK_TODO = "🔲"
    else:
        CHECK_DONE = "- [x]"
        CHECK_TODO = "- [ ]"

    lines: list[str] = []
    header = f"✦ Human 2.0 · {first_ts}–{last_ts} · {count} новых ✦"
    lines.append(_fmt_bold(header, fmt))
    lines.append("")

    lines.append(f"{CHECK_DONE} 🕐 Период: ~30 минут")
    authors_word = _plural(len(authors), ("автор", "автора", "авторов"))
    threads_word = _plural(len(threads), ("тред", "треда", "тредов"))
    lines.append(
        f"{CHECK_DONE} 👤 {len(authors)} {authors_word} · 💬 {count} сообщений · 🧵 {len(threads)} {threads_word}"
    )
    if authors:
        lines.append(CHECK_DONE + " 🔥 Участники: " + ", ".join(f"@{_fmt_escape(a, fmt)}" for a in authors[:8]))
    if top_authors:
        top_str = " · ".join(f"@{_fmt_escape(a, fmt)} ×{n}" for a, n in top_authors)
        lines.append(f"{CHECK_DONE} 🏆 Топ: {top_str}")

    for ti, thread in enumerate(threads, 1):
        items = thread["items"]
        topic_title = _short_topic(thread.get("title") or "обсуждение")
        status_icon = "✅" if thread.get("status") == "answered" else "💭"
        relevant_mark = " ⭐" if thread.get("relevant") else ""
        author_set = sorted({it["username"] for it in items})

        lines.append("")
        thread_head = f"▎Тред {ti} | {status_icon} {topic_title}{relevant_mark}"
        lines.append(_fmt_bold(thread_head, fmt))

        sub_bits = [_plural(len(items), ("сообщение", "сообщения", "сообщений"))]
        if author_set:
            sub_bits.append(", ".join(f"@{_fmt_escape(a, fmt)}" for a in author_set[:3]))
            if len(author_set) > 3:
                sub_bits.append(f"+{len(author_set) - 3}")
        lines.append("  " + " · ".join(sub_bits))

        VISIBLE = 2
        if len(items) > VISIBLE:
            hidden = items[:-VISIBLE]
            visible = items[-VISIBLE:]
            hidden_lines = []
            for it in hidden:
                ts = (it.get("date") or "")[:16].replace("T", " ")
                uname = _fmt_escape(it.get("username") or "?", fmt)
                preview = _fmt_escape(_truncate(it.get("text") or "", 80), fmt)
                hidden_lines.append(f"{ts} · @{uname} · {preview}")
            if fmt == "html":
                inner = " · ".join(hidden_lines)
                lines.append(f"  <i>▸ ещё {len(hidden)} сообщ: {inner}</i>")
            else:
                inner = "\\n".join(hidden_lines)
                lines.append(f"  <details>📂 ещё {len(hidden)} сообщ: {inner}</details>")
            items_to_show = visible
        else:
            items_to_show = items

        for it in items_to_show:
            ts = (it.get("date") or "")[:16].replace("T", " ")
            icon = TYPE_ICONS.get(it.get("type"), "💬")
            star = " ⭐" if it.get("relevant") else ""
            uname = _fmt_escape(it.get("username") or "?", fmt)
            mid = it["message_id"]
            link = _telegram_link(chat_id, mid)

            line = f"{CHECK_TODO} {icon} @{uname} | {ts} | #{mid}{star}"
            lines.append(line)
            for chunk in _wrap_quote(it.get("text") or "", fmt=fmt):
                lines.append(chunk)
            if fmt == "html":
                link_html = f'<a href="{link}">📎 #{mid}</a>'
                lines.append(f"  {link_html}")
            else:
                lines.append(f"  <details>📎 {link}</details>")

    lines.append("")
    lines.append("──────────")
    lines.append("")
    lines.append(_fmt_bold("💡 Инсайды и что полезно для нас", fmt))
    lines.append(
        _fmt_italic(
            "(блок готовится LLM в cron-job; если видишь это — он ещё не отработал)",
            fmt,
        )
    )

    cursor = digest.get("new_cursor") or 0
    if chat_username:
        chat_link = f"https://t.me/{chat_username}"
    elif chat_id:
        cid = str(chat_id)
        if cid.startswith("-100"):
            cid = cid[4:]
        chat_link = f"https://t.me/c/{cid}"
    else:
        chat_link = None

    lines.append("")
    if chat_link:
        if fmt == "html":
            link_html = f'<a href="{chat_link}">следующий тик через ~30 мин</a>'
            lines.append(f"<i>Курсор → {cursor} · {link_html}</i>")
        else:
            lines.append(_fmt_italic(f"Курсор → {cursor} · следующий тик через ~30 мин", fmt))
    else:
        lines.append(_fmt_italic(f"Курсор → {cursor} · следующий тик через ~30 мин", fmt))

    return "\n".join(lines)
