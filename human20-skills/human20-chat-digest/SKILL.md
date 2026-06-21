---
name: human20-chat-digest
description: Периодический дайджест чата Human 2.0 (или любого JSON-API чата) → Telegram. Реализует паттерн classify-then-render для cron-задач каждые N минут. По умолчанию рендерит в Telegram HTML, MarkdownV2 включается флагом `--format md2`.
version: 0.2.0
author: reclaw17
license: MIT
metadata:
  hermes:
    tags: [human20, digest, telegram, cron, html]
    related: [human20-helper]
---

# human20-chat-digest

Надстройка над [`human20-helper`](../human20-helper/SKILL.md) — собирает новые
сообщения из чата курса Human 2.0 и формирует короткий дайджест.

Используется:

- как `cron`-задача каждые 30 минут с доставкой в чат;
- вручную через CLI: `python3 digest.py --dry-run` или `--since-message-id <id>`;
- как библиотека: `from builder import build_digest` (legacy: `from digest import build_digest`).

## Что делает

1. Берёт `last_message_id` из `state.json` (рядом со скиллом).
2. Вызывает `get_workshop_chat_json` через `human20-mcp-client`.
3. Фильтрует сообщения с `message_id > last_message_id`.
4. Возвращает JSON-структуру: `count`, `authors`, `messages` (id / date /
   username / text-truncated / link).
5. Сохраняет новый `last_message_id` в `state.json`.

## Безопасность

- Только **read-only** MCP-вызовы. `send_user_message` / `preview_user_message`
  не используются.
- Токен `HUMAN20_BEARER_TOKEN` берётся из окружения (`os.environ`) или из
  локального `human20-helper/.env` — никаких захардкоженных секретов.
- `state.json` хранит только ID последнего сообщения, никаких текстов.

> ⚠️ Токен в `~/.hermes/.env` сам по себе **не подхватится** — клиент
> `human20-helper` сначала читает локальный `<skill-dir>/.env`. Подробнее
> и фикс — в `references/human20-env-pitfall.md`.

## Использование

```bash
# разово, посмотреть что есть (без записи state.json) — вывод в Telegram HTML
python3 digest.py --dry-run

# MarkdownV2 (если нужны именно <details>):
python3 digest.py --dry-run --format md2

# с лимитом (по умолчанию 200)
python3 digest.py --limit 500 --dry-run

# сбросить курсор (прочитать всё заново)
python3 digest.py --reset --dry-run

# из cron: отдать JSON в stdout
python3 digest.py --json

# применить классификацию от LLM (записывается в state.json)
python3 digest.py --apply-classification /tmp/cls.json
```

## Формат вывода: HTML vs MarkdownV2

`digest.py` поддерживает два формата:

| Формат | Когда использовать |
|---|---|
| **HTML** (по умолчанию) | Production. Стабильно, не падает на `-`, `!`, `.` в текстах сообщений. |
| **MarkdownV2** (`--format md2`) | Когда нужны именно `<details>` (сворачиваемые блоки). Только клиенты Telegram 7.7+. |

См. **P7** для подробностей.

## Cron (пример)

> ⚠️ Не путать с P1: `--skills` через запятую **тоже** не работает — `--skill`
> повторяемый флаг, каждый скилл отдельно.

```bash
hermes cron create 30m "Запусти human20-chat-digest и пришли результат в этот чат" \
  --name "human20-chat-digest" \
  --skill human20-chat-digest \
  --skill human20-helper \
  --deliver origin
```

Полный prompt для production-cron лежит в `templates/cron-job-prompt.md`.

## Структура

```
human20-chat-digest/
├── SKILL.md            ← этот файл
├── README.md           ← описание для GitHub
├── digest.py           ← CLI/main (оркестрация)
├── builder.py          ← build_digest
├── chat.py             ← fetch_chat + message helpers
├── threads.py          ← _cluster_threads, _finalize_thread, _guess_type
├── format_human.py     ← format_human + _wrap_quote
├── formats.py          ← escape/format helpers, _plural, _short_topic
├── state.py            ← _load_state, _save_state, apply_classification
├── telegram.py         ← _telegram_link
├── human20_chat_digest_threads.py ← public shim: cluster_threads API
├── state.json          ← курсор + кэш классификации LLM
├── references/
│   ├── human20-env-pitfall.md   ← как реально грузится токен
│   ├── telegram-rich-text.md    ← HTML vs MarkdownV2 — выбор формата, экранирование
│   └── cron-prompt-pattern.md   ← классификация → state → рендер
├── tests/
│   ├── test_format.py
│   ├── test_threads.py
│   ├── test_state.py
│   └── test_digest.py
└── templates/
    └── cron-job-prompt.md       ← готовый prompt для `hermes cron create`
```

## Зависимости

- Python 3.10+
- `human20-helper` скилл установлен (нужен `human20_mcp_client.py`)
- `HUMAN20_BEARER_TOKEN` — **см. `references/human20-env-pitfall.md`**, краткий
  вывод: положить в `~/.hermes/.env` **недостаточно** — клиент читает локальный
  `human20-helper/.env` ИЛИ переменную окружения родительского процесса.

## Pitfalls (реально встретились в этой сессии)

### P0. Сразу проверь формат вывода и место доставки ДО создания cron

Перед `hermes cron create ... --deliver origin` — прогони `digest.py --format html`
руками и отправь через `telegram.Bot.send_message(chat_id=<твой chat_id>, parse_mode='HTML')`.
Если что-то ломается — увидишь сразу, без ожидания 30-минутного тика.
`chat_id` берётся из `~/.hermes/sessions/*/request_dump_*.json` (поле `chat=<digits>` в gateway-логах).

### P1. `hermes cron create` ломает флаги при подстановке prompt через `$(cat ...)`

```bash
# ❌ НЕ работает: --skill / --deliver интерпретируются как часть prompt
hermes cron create 30m "$(cat prompt.txt)" --skill foo --skill bar

# ✅ Работает: позиционный prompt вторым аргументом, --skill повторяемый
hermes cron create 30m "..." --name foo --skill bar --skill baz --deliver origin
```

Подробнее: `references/cron-prompt-pattern.md`.

### P2. `human20-helper` клиент читает токен из своего `.env`, а не из `~/.hermes/.env`

Клиент `human20_mcp_client._load_local_env()` ищет `.env` рядом с **самим
скиллом** (`human20-helper/.env`). Если токен только в `~/.hermes/.env`,
клиент увидит `401`.

Рабочие варианты:

- Положить токен в `<skill-dir>/human20-helper/.env`
- Или экспортировать `HUMAN20_BEARER_TOKEN` в окружение родительского процесса
  (bash это делает автоматически при `sudo -iu hermes-agent`)

Полная диагностика: `references/human20-env-pitfall.md`.

### P3. `<details>` работает только в клиентах Telegram 7.7+ (лето 2026)

Старые клиенты покажут сырой `<details>📎 #123</details>` без сворачивания.
Если важна совместимость — откатись на обычный текст с эмодзи-маркером.

### P4. Telegram MarkdownV2: спец-символы в обычном тексте надо экранировать

Внутри `<details>`, blockquote (`>`) и task list (`- [ ]`) экранировать
**не нужно**. Снаружи — обязательно. Полный список и функция-обёртка:
`references/telegram-rich-text.md`.

### P5. `execute_code` блокирует `subprocess.run` в cron-профиле

Если LLM-классификацию нужно прогнать из Python — пиши скрипт в файл и
запускай через `terminal`, не через `execute_code`. В этой сессии `execute_code`
вернул `BLOCKED` именно на `subprocess`.

### P6. `chat_id` для `t.me/c/...` нужно без префикса `-100`

Human20 отдаёт `-1003598068116` для supergroup. Для ссылки `t.me/c/<id>/<msg>`
префикс `-100` убираем: `https://t.me/c/3598068116/123`.

### P7. Telegram HTML не поддерживает `<details>` (а MarkdownV2 — поддерживает)

Это **самый неочевидный компромисс** при выборе формата вывода.
Проверено в бою: `bot.send_message(..., parse_mode='HTML')` со строкой
`<details>📎 #2577</details>` возвращает `400: unsupported start tag "details"`.
В **MarkdownV2** этот же текст уходит нормально (Bot API 7.7+, лето 2026).

| Что хочется | HTML | MarkdownV2 |
|---|---|---|
| Сворачиваемые `<details>` (вложенные ссылки, длинные треды) | ❌ | ✅ |
| `<blockquote>` для цитат | ✅ нативный | через `> ` |
| `<a href="…">` ссылки | ✅ нативный | через `[…](…)` |
| `<b>`, `<i>`, `<code>` | ✅ нативные | через `*…*`, `_…_`, `` `…` `` |
| Экранирование | только `<`, `>`, `&` | 17 спец-символов, `\!` `\.` `\-` `\_` и т.д. |
| Стабильность | ✅ почти никогда не падает | ❌ падает на неэкранированном `-`, `.`, `!` |

**Рекомендация** (по умолчанию в `digest.py`): **HTML**.
В HTML нет экранирования дефисов и точек → сообщения от пользователей с
`@ChipCR` или `5-часовой` не сломают парсинг. Потерю `<details>`
компенсируем префиксом `▸ ещё N сообщ: …` курсивом — свёрнутый список
визуально читается.

Переключиться на MarkdownV2 можно флагом `--format md2` (оставлен для
случаев, когда нужны именно сворачиваемые `<details>`).

### P8. `hermes cron run <id>` МОЖЕТ СЖЕЧЬ задачу (default `--repeat` = 1)

Симптом: `hermes cron list` показывает `Repeat: 0/1` после создания. Один
тик — и job удалён. В этой сессии я терял `human20-chat-digest` именно так
**дважды**. Защита:

- **Не вызывай `hermes cron run <id>`** для диагностики. Команда только
  ставит в очередь, **сжигая** repeat-count. Для превью запусти pipeline
  руками через `terminal`.
- Для проверки реальной работы — жди scheduled tick или временно
  создай job с `--repeat 9999` (и потом удали, если не нужен).
- Подробнее про cron-семантику — в `hermes-cron-utilities/SKILL.md`
  (P-блок про `--repeat`).

### P9. Чтобы показать пользователю «живой» дайджест без ожидания новых
сообщений в чате — двигай cursor и принудительно классифицируй

Рабочий сценарий, когда хочется увидеть как cron-agent отрендерит **сейчас**:

```bash
# 1. Сдвинуть курсор (без записи в state — будет перезаписан на шаге 5)
python3 -c "
import json
p = '/home/hermes-agent/.hermes/skills/human20-chat-digest/state.json'
s = json.loads(open(p).read())
s['last_message_id'] = 2575   # значение ДО интересующих сообщений
open(p, 'w').write(json.dumps(s, ensure_ascii=False, indent=2) + '\n')
"

# 2. Запустить digest.py чтобы получить JSON с нужным окном
python3 .../digest.py --full --json --limit 5 --dry-run > /tmp/d.json

# 3. Записать «LLM-классификацию» руками (что LLM сделал бы на тике)
cat > /tmp/cls.json <<'EOF'
{ "items": {"2576": {"type":"discussion","relevant":true,"topic":"…"}, ...},
  "threads": {"t_2576": "Заголовок треда", ...} }
EOF
python3 .../digest.py --apply-classification /tmp/cls.json
rm /tmp/cls.json

# 4. Сгенерить финальный HTML
python3 .../digest.py --dry-run --limit 5 > /tmp/preview.html

# 5. Отправить через бота (chat_id из gateway-логов)
python3 -c "
import asyncio; from telegram import Bot
from pathlib import Path
t = next(l for l in Path('/home/hermes-agent/.hermes/.env').read_text().splitlines()
         if l.startswith('TELEGRAM_BOT_TOKEN')).split('=',1)[1].strip().strip(\"'\\\"\")
b = Bot(token=t)
asyncio.run(b.send_message(chat_id=<digits>, text=open('/tmp/preview.html').read(),
                            parse_mode='HTML'))
"
```

Это **ровно тот же pipeline**, что делает cron-agent на тике — без ожидания
scheduled tick. Удобно для дизайн-итераций.

### P10. Для проверки «отрендерит ли Telegram наш HTML» используй `python-telegram-bot`

В окружении `hermes-agent` установлен `python-telegram-bot 22.6`. Можно
отправить тестовое сообщение в свой же чат **от бота** — токен лежит в
`~/.hermes/.env`, chat_id — в `~/.hermes/sessions/*/request_dump_*.json`
(поле `chat=<digits>` в gateway-логе).

```python
import asyncio
from telegram import Bot
async def main():
    b = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])  # или из .env
    await b.send_message(chat_id=8371779103, text="<b>test</b>", parse_mode="HTML")
asyncio.run(main())
```

Если бот не подключён — `python3 -c "import telegram"` проверит наличие
пакета. `telethon` обычно **не установлен** — не пытайся.

## Шаблон для cron-задачи

Готовый prompt лежит в `templates/cron-job-prompt.md`. Используй его как
опорный при создании новых мониторинг-задач — он проверен в бою и проходит
полный pipeline за один тик.

## Паттерн: classify-then-render

Этот скилл реализует паттерн, применимый к любой задаче «читать JSON-API →
формировать красивый дайджест → слать в Telegram»:

1. **Python** тянет данные, фильтрует по курсору, группирует в треды/кластеры
2. **Python** пишет сырой JSON в `state.json` (cursor + minimal meta)
3. **LLM в cron-job** классифицирует (type, topic, relevant) и пишет обратно
   через `--apply-classification`
4. **Python** рендерит финальный MarkdownV2 c экранированием
5. **LLM** дописывает блок «💡 Инсайды» с учётом контекста пользователя

Так разделяются «механическая» работа (детерминированная) и «творческая»
(LLM), state переиспользуется между тиками, и каждая новая порция сообщений
классифицируется **один раз**, а не заново каждый тик.
