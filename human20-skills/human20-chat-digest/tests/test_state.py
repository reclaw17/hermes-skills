from __future__ import annotations

import json

import state


def test_load_state_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_PATH", tmp_path / "state.json")
    loaded = state._load_state()
    assert loaded["last_message_id"] == 0
    assert loaded["classified"] == {}
    assert loaded["topics"] == {}


def test_save_and_load_state_roundtrip(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    monkeypatch.setattr(state, "STATE_PATH", path)
    payload = {"last_message_id": 42, "classified": {"42": {"type": "question"}}, "topics": {}}
    state._save_state(payload)

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["last_message_id"] == 42
    assert "last_run_at" in raw

    loaded = state._load_state()
    assert loaded["classified"]["42"]["type"] == "question"


def test_apply_classification_updates_state():
    s = {"classified": {}, "topics": {}}
    cls = {
        "items": {"100": {"type": "answer", "topic": "T", "relevant": True}},
        "threads": {"t_100": "Thread title"},
    }
    state.apply_classification(s, cls)
    assert s["classified"]["100"]["type"] == "answer"
    assert s["topics"]["t_100"]["title"] == "Thread title"
