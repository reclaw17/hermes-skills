from __future__ import annotations


def _telegram_link(chat_id: int | None, message_id: int) -> str:
    if not chat_id:
        return f"#{message_id}"
    cid = str(chat_id)
    if cid.startswith("-100"):
        cid = cid[4:]
    return f"https://t.me/c/{cid}/{message_id}"


telegram_link = _telegram_link
