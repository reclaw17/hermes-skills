---
name: pre-publish-sanity-check
description: Перед публикацией чего-либо (skill, story, отчёт, скрипт) в общий доступ — обязательный sanity check на утечку секретов, приватных путей и персональных данных.
---

# Pre-publish Sanity Check

**Правило: перед записью в публичный репо / отправкой в публичный чат / публикацией скилла — прогнать чеклист ниже. Без исключений.**

## 🛑 STOP-RULE

**Любая находка чеклиста = СТОП. Не «зацензурим потом», не «и так сойдёт».**

Workflow при находке:
1. **Остановить публикацию.** Не выполнять `gh api PUT` / `git push` / отправку.
2. **Прочитать находку глазами** — это реальный секрет или false positive (пример regex'а внутри самого skill'а, и т.п.)?
3. **Если реальный секрет** → заменить на плейсхолдер (`<your-token>`, `${VAR_NAME}`), сохранить, **перепрогнать чеклист**.
4. **Если false positive** (regex внутри кода, пример имени, тестовая строка) → зафиксировать, что находка false positive, продолжить.
5. **Только после чистого прогона** → публикация.

**Никаких «потом зацензурим в следующем коммите» — это не работает: git history не прощается (см. pitfalls).**

## Когда применять

Перед любой из этих операций:
- `gh api PUT` в **публичный** репо (не свой приватный)
- `git push` в публичную ветку
- Создание/обновление скилла в `reclaw17/hermes-skills`
- Публикация в Telegram-канале с публичным доступом
- Шеринг через публичный gist / pastebin
- Копирование в общую папку / шару с другими пользователями

## Чеклист

### 1. Поиск секрет-паттернов

```bash
# API-ключи и токены
grep -nE "ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|xai-[A-Za-z0-9]{20,}|sk_live_|sk_test_|AIza[0-9A-Za-z\-_]{30,}" <file>

# Perplexity / OpenAI / прочие
grep -nE "PERPLEXITY_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|api[_-]?key\s*=\s*[\"'][A-Za-z0-9]{10,}" <file>

# Telegram-токены
grep -nE "[0-9]{8,10}:[A-Za-z0-9_\-]{30,}" <file>

# Приватные SSH ключи
grep -nE "-----BEGIN OPENSSH PRIVATE KEY-----|-----BEGIN RSA PRIVATE KEY-----|-----BEGIN PRIVATE KEY-----" <file>

# Seed-фразы (12/24 слова)
grep -nE "\b([a-z]+\s+){11,23}[a-z]+\b" <file>  # грубый паттерн, см. pitfalls
```

### 2. Поиск приватных путей

```bash
# Системные пути пользователя
grep -nE "/home/(<your-user>|<agent-user>)/|/Users/[a-z]+/|C:\\\\Users\\\\[a-z]+\\\\" <file>

# Внутренние имена репо
grep -nE "<owner>/<your-private-repo>|reclaw17/[a-z-]+-private" <file>

# Внутренние URL с токенами
grep -nE "https?://[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+@" <file>  # user:pass@host
```

### 3. Поиск персональных данных

```bash
# Email-адреса
grep -nE "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" <file>

# Номера телефонов (грубо)
grep -nE "\+?[78][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}" <file>

# IP-адреса
grep -nE "\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b" <file>

# MAC-адреса
grep -nE "([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}" <file>
```

### 4. Поиск контекстных утечек

Не только паттерны, но и **контекст**:
- Название модели провайдера, если он проприетарный и не должен светиться (`minimax` — наш провайдер).
- Имена коллег / соавторов, не данные публично.
- Названия внутренних проектов компании, если публикуешь под личным именем.
- Локальные домены (`<local-hostname>`, `cachyos.local`, etc.).

### 5. Bash-функция для быстрой проверки

Положи в `~/.bashrc` или вызывай по необходимости:

```bash
sanity-publish() {
  local file="$1"
  if [ -z "$file" ] || [ ! -f "$file" ]; then
    echo "Usage: sanity-publish <file>"
    return 1
  fi
  echo "=== secrets ==="
  grep -nE "ghp_|sk-[A-Za-z]|api[_-]?key|-----BEGIN.*PRIVATE KEY-----|PERPLEXITY|ANTHROPIC|OPENAI" "$file" || echo "  (clean)"
  echo "=== private paths ==="
  grep -nE "/home/(<your-user>|<agent-user>)|reclaw17/.*-private|<local-hostname>" "$file" || echo "  (clean)"
  echo "=== emails / phones / IPs ==="
  grep -nE "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\+?[78][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b" "$file" || echo "  (clean)"
}
```

Использование:
```bash
sanity-publish /tmp/my-new-skill.md
```

### 6. Sanity check батча (несколько файлов)

```python
import subprocess, re

CHECKS = [
    ("API key", r"ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z\-_]{30,}"),
    ("API env", r"PERPLEXITY|ANTHROPIC|OPENAI|TELEGRAM|HUMAN20.*KEY|HUMAN20.*TOKEN"),
    ("Private path", r"/home/(<your-user>|<agent-user>)|reclaw17/.*-private|<local-hostname>"),
    ("SSH key", r"-----BEGIN .* PRIVATE KEY-----"),
    ("Email", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    ("Phone", r"\+?[78][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"),
    ("IP", r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    ("user:pass URL", r"https?://[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+@"),
]

def check(path):
    with open(path, "rb") as f:
        content = f.read().decode("utf-8", errors="replace")
    findings = []
    for name, pat in CHECKS:
        for m in re.finditer(pat, content):
            line = content[:m.start()].count("\n") + 1
            findings.append((name, line, m.group(0)[:60]))
    return findings

import sys
for p in sys.argv[1:]:
    f = check(p)
    if f:
        print(f"\n{p}:")
        for name, line, snippet in f:
            print(f"  L{line} [{name}]: {snippet!r}")
    else:
        print(f"{p}: clean")
```

Использование:
```bash
python3 sanity.py /tmp/file1.md /tmp/file2.sh
```

## Pitfalls

1. **Seed-фразы не ловятся regex'ом надёжно** — 12/24 слова могут быть и обычным текстом. Если есть подозрение, что в файле могли оказаться слова из BIP39-словаря, читай глазами.

2. **Контекст важнее паттерна.** `1234567890` это может быть номер телефона, или ID задачи, или просто число. Смотри на окружающие слова: «phone», «token», «user_id», «password» — это триггеры для тщательной проверки.

3. **Git history не прощается.** Если уже закоммитил и запушил — `git rm` в следующем коммите **не стирает** секрет из истории. Нужен `git filter-repo` или `BFG Repo Cleaner`. **Поэтому sanity check ДО push, не после.**

4. **Бинарные файлы (`.pdf`, `.png`, `.ipynb`)** не grep'аются. Если публикуешь блокнот — открой в Jupyter и пробегись глазами по output-ячейкам.

5. **JSON / YAML ключи** могут выглядеть невинно: `"PERPLEXITY_API_KEY": "pplx-..."` — поэтому ищи и `api_key=`, и `PERPLEXITY`, и другие контекстные слова, не только формальный regex.

6. **Плейсхолдеры должны быть узнаваемыми**, но не похожими на реальные токены. Используй `<your-token-here>`, `${PERPLEXITY_API_KEY}`, `***`, но **не** `sk-XXXXXXXXXXXX` — это похоже на реальный `sk-...` и может пройти автоматические сканеры у принимающей стороны.

7. **`.env.example` ≠ `.env`**. Публикуй `.env.example` с плейсхолдерами, **никогда** не коммить настоящий `.env`.

8. **Локальные хостнеймы утекают** (`<local-hostname>` — это имя ноутбука, может раскрывать владельца). Заменяй на `<local-machine>` или убери совсем.

9. **«Я же закомитил в приватный репо, потом сделаю публичным — там не будет секретов»** — ложное чувство безопасности. Приватный → публичный переход часто делается через `gh repo edit --visibility public`, и **всё, что там было, становится публичным**, включая старые коммиты.

10. **Sanity check ≠ security audit.** Этот чеклист ловит очевидное. Для критичных публикаций (публичный API-сервис, прод-система) — отдельный security review специалистом.

## Verification

После sanity check **и** перед коммитом:
1. Прогони `sanity-publish <file>` или `python3 sanity.py <files>`.
2. Если найдено что-то — это **стоп-сигнал**, не «ок, зацензурим потом».
3. Если чисто — `git diff` (или `gh api GET` для сравнения) ещё раз глазами: что реально попадёт в публичный diff?
4. Только после этого — `git push` / `gh api PUT`.

## Связанные skill'ы

- `github-sync-agent-work` — после его применения тоже прогоняй этот чеклист, потому что skill не делает sanitization сам.

## Когда НЕ применять

- Коммит в **приватный** репо, к которому нет публичного доступа — обычные правила безопасности, без этого чеклиста.
- Локальные одноразовые скрипты в `agent-work/`, которые не публикуются.
- `~/.hermes/` файлы — это per-user, не публичные по построению.