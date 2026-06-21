from __future__ import annotations


MD2_SPECIAL = r"_*[]()~`>#+-=|{}.!"


def _md2_escape(text: str) -> str:
    if not text:
        return ""
    out = []
    for ch in text:
        if ch in MD2_SPECIAL:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def _html_escape(text: str) -> str:
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt_escape(text: str, fmt: str) -> str:
    if fmt == "html":
        return _html_escape(text)
    return _md2_escape(text)


def _fmt_link(text: str, url: str, fmt: str) -> str:
    text_esc = _fmt_escape(text, fmt)
    url_esc = _html_escape(url) if fmt == "html" else url
    if fmt == "html":
        return f'<a href="{url_esc}">{text_esc}</a>'
    return f"[{text_esc}]({url_esc})"


def _fmt_bold(text: str, fmt: str) -> str:
    esc = _fmt_escape(text, fmt)
    if fmt == "html":
        return f"<b>{esc}</b>"
    return f"*{esc}*"


def _fmt_italic(text: str, fmt: str) -> str:
    esc = _fmt_escape(text, fmt)
    if fmt == "html":
        return f"<i>{esc}</i>"
    return f"_{esc}_"


def _plural(n: int, forms: tuple[str, str, str]) -> str:
    n100 = n % 100
    if 11 <= n100 <= 14:
        return forms[2]
    n10 = n % 10
    if n10 == 1:
        return forms[0]
    if 2 <= n10 <= 4:
        return forms[1]
    return forms[2]


def _short_topic(title: str) -> str:
    if not title:
        return "обсуждение"
    t = title.strip()
    if len(t) <= 60:
        return t
    return t[:59] + "…"
