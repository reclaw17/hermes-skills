from __future__ import annotations

from threads import _cluster_threads, _finalize_thread, _guess_type


def _date(msg):
    return msg.get("date") or ""


def test_guess_type_question_and_link():
    assert _guess_type("где запись?") == "question"
    assert _guess_type("смотри https://example.com") == "link"


def test_finalize_thread_answered_status():
    items = [
        {"message_id": 1, "username": "u1", "type": "question", "topic": "x", "relevant": False},
        {"message_id": 2, "username": "u2", "type": "answer", "topic": "x", "relevant": True},
    ]
    thread = _finalize_thread(items)
    assert thread["status"] == "answered"
    assert thread["relevant"] is True
    assert thread["title"] == "x"


def test_cluster_threads_sorts_relevant_first():
    items = [
        {"message_id": 1, "username": "u1", "type": "discussion", "topic": "A", "relevant": False, "_raw": {"date": "2026-06-20T10:00:00+00:00"}, "date": "2026-06-20T10:00:00+00:00"},
        {"message_id": 2, "username": "u2", "type": "discussion", "topic": "B", "relevant": True, "_raw": {"date": "2026-06-20T10:01:00+00:00"}, "date": "2026-06-20T10:01:00+00:00"},
    ]
    threads = _cluster_threads(items, _date)
    assert threads[0]["relevant"] is True
