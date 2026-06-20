#!/usr/bin/env python3
"""
human20-chat-digest — дайджест новых сообщений из чата Human 2.0.

Читает через human20-helper / human20_mcp_client.get_workshop_chat_json.
Хранит курсор (last_message_id) и метаданные классификации в state.json
рядом со скриптом.
По умолчанию read-only: ничего не пишет в Human20, ничего не отправляет.
"""
from __future__ import annotations

import argparse
import json
import os
import re
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

# Telegram MarkdownV2: символы, которые нужно экранировать внутри обычного текста.
# В наших блоках (<details>, blockquote, task list, code/pre) экранирование не нужно.
MD2_SPECIAL = r"_*[]()~`>#+-=|{}.!"

# Простая эвристика для типа сообщения (если LLM не передал meta.type).
QUESTION_RE = re.compile(r"\?")
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


def _md2_escape(text: str) -> str:
    """Экранировать спец-символы MarkdownV2 для обычного текста."""
    if not text:
        return ""
    out = []
    for ch in text:
        if ch in MD2_SPECIAL:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def _md2_escape_inline(text: str) -> str:
    """Экранировать без бэкслеша перед > и +, чтобы не ломать blockquote/task list.
    Используется внутри уже структурированных блоков."""
    # Здесь не экранируем, потому что текст уже внутри своей разметки.
    return text or ""


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {
            "last_message_id": 0,
            "last_run_at": None,
            "classified": {},  # message_id → {type, topic, relevant, summary}
            "topics": {},      # topic_id → {title, opened_at, last_message_id}
        }
    try:
        s = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        # Миграция: добавим недостающие ключи.
        s.setdefault("classified", {})
        s.setdefault("topics", {})
        return s
    except Exception:
        return {
            "last_message_id": 0,
            "last_run_at": None,
            "classified": {},
            "topics": {},
        }


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


def _maybe_truncate(text: str, limit: int | None) -> str:
    flat = (text or "").strip().replace("\n", " ").replace("\r", " ")
    if limit is None or limit <= 0:
        return flat
    return _truncate(flat, limit)


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


def _guess_type(text: str) -> str:
    """Простая эвристика для типа сообщения, если LLM не дал meta.type."""
    t = (text or "").strip()
    if not t:
        return "discussion"
    # Вопрос — последний непустой символ `?`, либо `? )` (со смайликом после).
    stripped = t.rstrip()
    if stripped.endswith("?") or stripped.rstrip(")").endswith("?"):
        return "question"
    if LINK_RE.search(t):
        return "link"
    if len(t) > LONG_TEXT_CHARS:
        return "discussion"
    return "discussion"


def fetch_chat(client: Human20McpClient) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Получить все сообщения чата через MCP и, если есть, заголовок чата."""
    raw = client.structured_tool("get_workshop_chat_json", {})
    chat_meta: dict[str, Any] | None = None
    if isinstance(raw, dict):
        chat_meta = {
            k: raw[k]
            for k in ("chat_id", "chat_type", "title", "username", "link")
            if k in raw
        }
    return _normalize_messages(raw), chat_meta


def _cluster_threads(
    items: list[dict[str, Any]], gap_minutes: int = 5, merge_by_topic: bool = True
) -> list[dict[str, Any]]:
    """Грубая кластеризация: тред = серия сообщений в пределах gap_minutes
    с одинаковым topic (если LLM классифицировал).

    merge_by_topic=True: даже если время далеко, объединять сообщения с тем же topic.
    """
    if not items:
        return []

    def _ts(it: dict[str, Any]) -> datetime | None:
        d = _message_date(it.get("_raw", {})) or it.get("date")
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
        same_topic = (
            merge_by_topic
            and it.get("topic")
            and it.get("topic") == cur[0].get("topic")
        )
        time_close = ts and prev_ts and (ts - prev_ts).total_seconds() <= gap_minutes * 60

        if same_topic or (time_close and not (it.get("topic") or cur[0].get("topic"))):
            cur.append(it)
        else:
            threads.append(_finalize_thread(cur))
            cur = [it]
    if cur:
        threads.append(_finalize_thread(cur))

    # Сортировка: ⭐ первыми, потом по времени последнего сообщения (новые выше).
    threads.sort(
        key=lambda t: (
            0 if t.get("relevant") else 1,
            -(_ts(t["items"][-1]) or datetime.min).timestamp(),
        )
    )
    return threads


def _finalize_thread(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Сформировать описание треда из списка сообщений."""
    first_id = items[0]["message_id"]
    topic_id = f"t_{first_id}"
    topic = items[0].get("topic")
    # Если у разных сообщений разные topic — берём самый частый.
    if not topic:
        from collections import Counter
        topics_seen = [it.get("topic") for it in items if it.get("topic")]
        if topics_seen:
            topic = Counter(topics_seen).most_common(1)[0][0]
    relevant = any(it.get("relevant") for it in items)
    has_question = any(it.get("type") == "question" for it in items)
    last = items[-1]
    has_answer = (
        last.get("type") == "answer"
        or (has_question and last.get("username") != items[0].get("username"))
    )
    status = "answered" if has_question and has_answer else "open"
    return {
        "topic_id": topic_id,
        "title": topic or "обсуждение",
        "relevant": relevant,
        "status": status,
        "items": items,
    }


def build_digest(
    messages: list[dict[str, Any]],
    last_message_id: int,
    classified: dict[str, Any] | None = None,
    topics: dict[str, Any] | None = None,
    limit: int = DEFAULT_LIMIT,
    full_text: bool = False,
) -> dict[str, Any]:
    """Отфильтровать новые сообщения и сформировать дайджест."""
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

    threads = _cluster_threads(items)
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


def _telegram_link(chat_id: int | None, message_id: int) -> str:
    """Ссылка на сообщение Telegram: t.me/c/<id>/<msg> для supergroup."""
    if not chat_id:
        return f"#{message_id}"
    # chat_id для supergroup приходит как -100XXXXXXXXXX, для ссылки берём без -100.
    cid = str(chat_id)
    if cid.startswith("-100"):
        cid = cid[4:]
    return f"https://t.me/c/{cid}/{message_id}"


def _short_topic(title: str) -> str:
    """Сократить заголовок треда до 60 символов."""
    if not title:
        return "обсуждение"
    t = title.strip()
    if len(t) <= 60:
        return t
    return t[:59] + "…"


def format_human(digest: dict[str, Any], chat_meta: dict[str, Any] | None = None) -> str:
    """Шаблон v2: task list в шапке, треды, blockquote, <details>, sub-подписи."""
    if not digest.get("ok"):
        return f"⚠️ human20-chat-digest: {_md2_escape(digest.get('error', 'unknown error'))}"

    count = digest["count"]
    if count == 0:
        return "💤 В чате Human 2\\.0 нового ничего нет\\."

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
    # Если chat_id не на верхнем уровне, берём из первого сообщения.
    if not chat_id and digest["items"]:
        chat_id = digest["items"][0].get("_raw", {}).get("chat_id")

    # Шапка
    first_ts = (digest["items"][0].get("date") or "")[:16].replace("T", " ")
    last_ts = (digest["items"][-1].get("date") or "")[:16].replace("T", " ")
    authors = digest["authors"]

    # Топ-3 авторов по числу сообщений.
    author_counts: dict[str, int] = {}
    for it in digest["items"]:
        author_counts[it["username"]] = author_counts.get(it["username"], 0) + 1
    top_authors = sorted(author_counts.items(), key=lambda kv: -kv[1])[:3]

    lines: list[str] = []
    lines.append(f"*✦ Human 2\\.0 · {_md2_escape(first_ts)}–{_md2_escape(last_ts)} · {count} новых ✦*")
    lines.append("")
    lines.append("- [x] 🕐 Период: ~30 минут")
    authors_word = _plural(len(authors), ("автор", "автора", "авторов"))
    threads_word = _plural(len(threads), ("тред", "треда", "тредов"))
    lines.append(f"- [x] 👤 {len(authors)} {authors_word} · 💬 {count} сообщений · 🧵 {len(threads)} {threads_word}")
    if authors:
        lines.append("- [x] 🔥 Участники: " + ", ".join(f"@{_md2_escape(a)}" for a in authors[:8]))
    if top_authors:
        top_str = " · ".join(f"@{_md2_escape(a)} ×{n}" for a, n in top_authors)
        lines.append(f"- [x] 🏆 Топ: {top_str}")

    # Тело по тредам
    for ti, thread in enumerate(threads, 1):
        items = thread["items"]
        topic_title = _short_topic(thread.get("title") or "обсуждение")
        status_icon = "✅" if thread.get("status") == "answered" else "💭"
        relevant_mark = " ⭐" if thread.get("relevant") else ""
        author_set = sorted({it["username"] for it in items})

        lines.append("")
        lines.append(
            f"*▎Тред {ti} \\| {status_icon} {_md2_escape(topic_title)}*{relevant_mark}"
        )
        sub_bits = [_plural(len(items), ("сообщение", "сообщения", "сообщений"))]
        if author_set:
            sub_bits.append(", ".join(f"@{_md2_escape(a)}" for a in author_set[:3]))
            if len(author_set) > 3:
                sub_bits.append(f"\\+{len(author_set) - 3}")
        lines.append("  " + " · ".join(sub_bits))

        # Сворачиваем старые сообщения: первые N-2 уходят в <details>.
        VISIBLE = 2
        if len(items) > VISIBLE:
            hidden = items[:-VISIBLE]
            visible = items[-VISIBLE:]
            hidden_lines = [
                f"{_md2_escape((it.get('date') or '')[:16].replace('T', ' '))} · "
                f"@{_md2_escape(it.get('username') or '?')} · "
                f"{_md2_escape(_truncate(it.get('text') or '', 80))}"
                for it in hidden
            ]
            lines.append(
                f"  <details>📂 ещё {len(hidden)} сообщ: "
                + "\\n".join(_md2_escape(l) for l in hidden_lines)
                + "</details>"
            )
            items_to_show = visible
        else:
            items_to_show = items

        for it in items_to_show:
            ts = (it.get("date") or "")[:16].replace("T", " ")
            icon = TYPE_ICONS.get(it.get("type"), "💬")
            star = " ⭐" if it.get("relevant") else ""
            uname = it.get("username") or "?"
            mid = it["message_id"]
            link = _telegram_link(chat_id, mid)

            lines.append(f"- [ ] {icon} @{_md2_escape(uname)} \\| {_md2_escape(ts)} \\| \\#{mid}{star}")
            for chunk in _wrap_quote(it.get("text") or ""):
                lines.append(f"  > {chunk}")
            lines.append(f"  <details>📎 {link}</details>")

    # Подвал
    lines.append("")
    lines.append("──────────")
    lines.append("")
    lines.append("*💡 Инсайды и что полезно для нас*")
    lines.append("_(блок готовится LLM в cron\\-job; если видишь это — он ещё не отработал)_")

    cursor = digest.get("new_cursor") or 0
    # Ссылка на чат для «открыть чат»
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
        lines.append(
            f"_Курсор → {cursor} · [следующий тик через ~30 мин]({chat_link})_"
        )
    else:
        lines.append(f"_Курсор → {cursor} · следующий тик через ~30 мин_")

    return "\n".join(lines)


def _plural(n: int, forms: tuple[str, str, str]) -> str:
    """Русское склонение: (1, 2-4, 5+)."""
    n100 = n % 100
    if 11 <= n100 <= 14:
        return forms[2]
    n10 = n % 10
    if n10 == 1:
        return forms[0]
    if 2 <= n10 <= 4:
        return forms[1]
    return forms[2]


def _wrap_quote(text: str, width: int = 80) -> list[str]:
    """Разбить текст на строки шириной width, экранируя спец-символы."""
    flat = (text or "").replace("\n", " ").replace("\r", " ").strip()
    if not flat:
        return [_md2_escape("(пусто)")]
    # Простая разбивка по словам.
    words = flat.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return [_md2_escape(l) for l in lines]


def apply_classification(state: dict[str, Any], classification: dict[str, Any]) -> None:
    """Применить классификацию от LLM (из cron-job) к state.

    classification = {
        "items": {"<message_id>": {"type": "...", "topic": "...", "relevant": bool, "summary": "..."}, ...},
        "threads": {"<topic_id>": "Новый заголовок треда"},
    }
    """
    classified = state.setdefault("classified", {})
    topics = state.setdefault("topics", {})
    for mid, meta in (classification.get("items") or {}).items():
        classified[str(mid)] = meta
    for tid, title in (classification.get("threads") or {}).items():
        if title:
            topics[tid] = {"title": title}


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
        print(format_human(digest, chat_meta=chat_meta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())