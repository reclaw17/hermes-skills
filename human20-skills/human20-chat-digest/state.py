from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parent
STATE_PATH = SKILL_DIR / "state.json"


def default_state() -> dict[str, Any]:
    return {
        "last_message_id": 0,
        "last_run_at": None,
        "classified": {},
        "topics": {},
    }


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return default_state()
    try:
        s = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        s.setdefault("classified", {})
        s.setdefault("topics", {})
        return s
    except Exception:
        return default_state()


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


def apply_classification(state: dict[str, Any], classification: dict[str, Any]) -> None:
    classified = state.setdefault("classified", {})
    topics = state.setdefault("topics", {})
    for mid, meta in (classification.get("items") or {}).items():
        classified[str(mid)] = meta
    for tid, title in (classification.get("threads") or {}).items():
        if title:
            topics[tid] = {"title": title}


load_state = _load_state
save_state = _save_state
