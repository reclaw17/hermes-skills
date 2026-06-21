from __future__ import annotations

from format_human import _wrap_quote, format_human
from formats import _plural, _short_topic


def test_plural_and_short_topic():
    assert _plural(1, ("автор", "автора", "авторов")) == "автор"
    assert _plural(2, ("автор", "автора", "авторов")) == "автора"
    assert _plural(5, ("автор", "автора", "авторов")) == "авторов"
    assert _short_topic("x" * 90).endswith("…")


def test_wrap_quote_html_and_md2():
    html = _wrap_quote("a < b", fmt="html")
    md2 = _wrap_quote("a.b", fmt="md2")
    assert html[0].startswith("<blockquote>")
    assert "&lt;" in html[0]
    assert md2[0].startswith("> ")
    assert "\\." in md2[0]


def test_format_human_empty_digest():
    text = format_human({"ok": True, "count": 0})
    assert "нового ничего нет" in text
