# github-sync-agent-work

Двусторонняя синхронизация файлов между локальной `agent-work/` директорией и GitHub-репозиторием через `gh api`. Без `git clone`, без `git push` — только HTTP API.

Надстройка над встроенным [`github-repo-management`](https://github.com/NousResearch/hermes-agent/tree/main/skills/github/github-repo-management), закрывает нишу, которую он не покрывает: **мелкие точечные правки** (1-10 файлов) там, где поднимать локальный git-репо избыточно.

## Что делает

- **Локально → репо:** `gh api PUT .../contents/<path>` — коммит одного файла с указанным сообщением.
- **Репо → локально:** `gh api GET .../contents/<path> | base64 -d` — скачивание файла.
- **Проверка sync:** `md5sum` локально и в репо.
- **Batch-проверка:** Python-скрипт для сравнения md5 по списку путей.

## Когда использовать

- Правка одного или нескольких файлов в `agent-work/coding/`, `agent-work/docs/`, `agent-work/plans/`, `agent-work/reports/`.
- Нет настроенного `git remote`.
- Не нужна история коммитов / ветки / PR-флоу.
- Хочется сделать коммит одной командой без `git add && git commit && git push`.

## Когда **не** использовать

- Много файлов (десятки) — каждый PUT это отдельный API-вызов, лучше `git clone` + `git push`.
- Есть `git remote` — `git pull` / `git push` проще и сохраняют историю.
- Бинарные файлы или >1MB — `gh api` ненадёжен.
- Совместная работа над одними путями — нет merge-механизма.
- Нужна история / ветки / теги — этот скилл не сохраняет ничего, кроме текущего содержимого файлов.

## Быстрый старт

### Commit одного файла

```bash
SHA=$(gh api repos/<owner>/<repo>/contents/<path> --jq '.sha')
CONTENT=$(base64 -w 0 <local_path>)
JSON=$(jq -n --arg msg "My commit" --arg content "$CONTENT" --arg sha "$SHA" \
  '{message:$msg, content:$content, sha:$sha}')
gh api -X PUT repos/<owner>/<repo>/contents/<path> \
  --input <(echo "$JSON") --jq '.commit.sha'
```

### Скачать файл

```bash
gh api repos/<owner>/<repo>/contents/<path> --jq '.content' | base64 -d > <local_path>
```

### Проверить, что локальный и репо-файл совпадают

```bash
md5sum <local_path>
gh api repos/<owner>/<repo>/contents/<path> --jq '.content' | base64 -d | md5sum
```

## Типичные грабли

1. **Забыл sync после правки через `/tmp`** — локальная копия остаётся старой, скрипты/cron работают с устаревшим кодом. Всегда проверяй `md5sum` после PUT.
2. **PUT без `sha` пытается создать новый файл** — для обновления существующего **обязательно** передавай текущий `sha`.
3. **Конфиги Hermes (`~/.hermes/config.yaml`, `.env`, `scripts/`)** — не синхронизируй этим скиллом, используй `hermes config set` / `hermes cron update` / `cp`.
4. **`subprocess.run(capture_output=True).stdout`** в Python возвращает `memoryview`, не `bytes` — оборачивай в `bytes(...)` перед `hashlib.md5()`.
5. **Новые скрипты для cron** — после добавления в `coding/scripts/` продублируй в `~/.hermes/scripts/`, иначе cron не найдёт (`Script not found`).
6. **`Last run: ok`** для cron-задачи ≠ успех. Всегда смотри содержимое отчёта.

Полный список и подробности — в [`SKILL.md`](./SKILL.md).

## Требования

- `gh` CLI: `gh auth status` должен показывать `Logged in`.
- `jq` для построения JSON.
- `base64` и `python3`.
- Read-access к репо (для скачивания), write-access (для коммитов).

## Установка

### Через `hermes skills install`

```bash
hermes skills install https://github.com/reclaw17/hermes-skills
hermes skills reload
```

### Вручную

```bash
git clone https://github.com/reclaw17/hermes-skills.git
cp -r hermes-skills/github/github-sync-agent-work ~/.hermes/skills/
hermes skills reload
```

## Лицензия

MIT