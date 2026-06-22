#!/usr/bin/env python3
"""
self-check.py — прогон чеклиста pre-publish-sanity-check против одного или нескольких файлов.

Использование:
    python3 self-check.py <file1> [file2 ...]

Что считается чистым:
    - 0 находок в prose (вне code-блоков) — обязательно для публикации.
    - Находки внутри code-блоков (``` ... ```) — допустимы (это функциональные
      примеры regex'ов), но лучше фиксировать их в комментарии к коммиту.

Возвращает exit code:
    0 — файл чист
    1 — есть находки в prose
    2 — ошибка (файл не найден, и т.п.)
"""
import re
import sys
from pathlib import Path

# Чеклисты по разделам skill'а
CHECKS = [
    ("API token (ghp_/sk-/AIza)", r"\bghp_[A-Za-z0-9]{20,}|\bsk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z\-_]{30,}"),
    ("API env name (PERPLEXITY/OPENAI/...)", r"\bPERPLEXITY_API_KEY|\bOPENAI_API_KEY|\bANTHROPIC_API_KEY|\bTELEGRAM_BOT_TOKEN"),
    ("Private path (/home/<user>)", r"/home/(rx00|hermes-agent|<your-user>|<agent-user>)"),
    ("Private repo (<owner>/<repo>-private)", r"<owner>/[a-z-]+-private"),
    ("Local hostname (cachyos-/macbook-)", r"cachyos-[a-z0-9]+|macbook-[a-z0-9]+"),
    ("SSH key literal", r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    ("user:pass URL", r"https?://[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+@"),
    ("Email", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    ("Phone RU (+7/8)", r"\+?[78][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"),
    ("IPv4", r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    ("MAC address", r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}"),
]


def find_in_code(content: str):
    """Находки ТОЛЬКО вне code-блоков (prose)."""
    findings = []
    in_code = False
    for lineno, line in enumerate(content.split("\n"), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for name, pat in CHECKS:
            for m in re.finditer(pat, line):
                findings.append((lineno, name, m.group(0)[:60]))
    return findings


def check(path: Path):
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"ERROR: not a text file: {path}", file=sys.stderr)
        return 2

    findings = find_in_code(content)
    if findings:
        print(f"\n❌ {path}: {len(findings)} prose finding(s)")
        for lineno, name, snippet in findings:
            print(f"   L{lineno} [{name}]: {snippet!r}")
    else:
        print(f"✅ {path}: clean (0 prose findings)")
    return 1 if findings else 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 self-check.py <file1> [file2 ...]", file=sys.stderr)
        return 2
    rc = 0
    for arg in sys.argv[1:]:
        result = check(Path(arg))
        rc = rc or result
    if rc == 0:
        print("\n✅ ALL FILES CLEAN — ready to publish")
    else:
        print(f"\n🛑 STOP: fix findings before publishing (exit {rc})")
    return rc


if __name__ == "__main__":
    sys.exit(main())
