---
name: github-sync-agent-work
description: Sync files between a local agent-work directory and a GitHub repo via gh api PUT (bidirectional, no git clone required).
---

# Sync agent-work ↔ GitHub repo via gh api

## When to use

- Editing one or a few files in `agent-work/coding/`, `agent-work/docs/`, `agent-work/plans/`, `agent-work/reports/`
- Need to commit to a GitHub repo (or read from it)
- No `git clone` / no local git remote configured
- Especially useful for small stories / single-file changes

## Key invariant

**Bidirectional sync is TWO separate operations:**

1. Local → repo: `gh api PUT .../contents/<path>` with the full new content
2. Repo → local: `gh api .../contents/<path>` → `base64 -d > <local_path>`

After ANY edit to a file in `agent-work/` that also lives in the repo, verify md5 match. If they differ — sync.

## Commands

### 1. Local → repo (commit)

```bash
SHA=$(gh api repos/<owner>/<repo>/contents/<path> --jq '.sha')
CONTENT=$(base64 -w 0 <local_path>)
MSG="<commit message>"
JSON=$(jq -n --arg msg "$MSG" --arg content "$CONTENT" --arg sha "$SHA" \
  '{message:$msg, content:$content, sha:$sha}')
gh api -X PUT repos/<owner>/<repo>/contents/<path> \
  --input <(echo "$JSON") --jq '.commit.sha'
```

**For a new file** — omit the `sha` field:
```bash
JSON=$(jq -n --arg msg "$MSG" --arg content "$CONTENT" \
  '{message:$msg, content:$content}')
```

### 2. Repo → local (sync down)

```bash
gh api repos/<owner>/<repo>/contents/<path> --jq '.content' \
  | base64 -d > <local_path>
```

### 3. Check sync (compare md5)

```bash
# local
md5sum <local_path>
# repo
gh api repos/<owner>/<repo>/contents/<path> --jq '.content' \
  | base64 -d | md5sum
```

### 4. Check many files at once

```python
import subprocess, json, hashlib, os

def repo_md5(path):
    r = subprocess.run(
        ["gh", "api", f"repos/<owner>/<repo>/contents/{path}"],
        capture_output=True
    )
    if r.returncode != 0:
        return ("ERR", r.stderr.decode(errors="replace").strip()[:40])
    data = json.loads(r.stdout)
    if "content" not in data:
        return ("NOTFILE", data.get("type", "?"))
    content_b64 = data["content"].replace("\n", "").encode()
    proc = subprocess.run(["base64", "-d"], input=content_b64, capture_output=True)
    return (hashlib.md5(bytes(proc.stdout)).hexdigest(), len(proc.stdout))

def local_md5(path):
    full = f"<agent-work-dir>/{path}"
    if not os.path.exists(full):
        return None
    with open(full, "rb") as f:
        return hashlib.md5(f.read()).hexdigest(), os.path.getsize(full)
```

**CRITICAL: `proc.stdout` from `subprocess.run(capture_output=True)` is a `memoryview`, not `bytes`.** Wrap it in `bytes(proc.stdout)` before passing to `hashlib.md5()`. Otherwise: `TypeError: a bytes-like object is required, not 'memoryview'`.

## Pitfalls

1. **Forgotten sync after editing via `/tmp`**: if you edit a file in `/tmp/`, then commit to the repo, **the local copy in `agent-work/` stays old** → cron / local scripts keep using the stale version. Always check `md5sum` locally after `gh api PUT`.

2. **PUT without `sha` tries to create a new file**, not update. If file already exists — 422 / conflict. For update **always pass the current file's `sha`**.

3. **Hermes configs** (`~/.hermes/config.yaml`, `~/.hermes/.env`, `~/.hermes/scripts/`) — don't sync via `gh api`. Use `hermes config set` / `hermes cron update` / `cp` (for scripts). Either the `patch` tool will refuse, or these files must stay local.

4. **Binary files and large files** (>1MB) — `gh api PUT` is slow and unreliable for them. Use `git clone` or `git pull` instead.

5. **`subprocess.run(capture_output=True).stdout` is a `memoryview`** (at least on some Linux distros). Wrap in `bytes()` or pass `text=False` (the default).

6. **Don't forget `~/.hermes/scripts/`**. If you edit `coding/scripts/foo.sh` or add a new one, also place a copy at `~/.hermes/scripts/foo.sh`, otherwise cron will report `Script not found`. This is a common cause of broken cron jobs.

7. **After sync, always inspect the report** for cron-driven scripts — `Last run: ok` is not proof of success, the report may still contain errors.

## Verification

After any sync:
1. `md5sum` local and repo — must match
2. If file runs via cron — `hermes cron run <job_id>` AND inspect the report contents (not just `Last run: ok`)
3. If file is a Python script — `python3 -c "import ast; ast.parse(open(path).read())"`

## When NOT to use

- Bulk changes (tens of files) — prefer `git clone` + local `git push`
- If a `git remote` is already set up — `git pull` / `git push` is simpler
- Binary files or files >1MB — `gh api` is unreliable