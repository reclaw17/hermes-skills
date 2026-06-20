---
name: human20-chat-digest
description: Периодический дайджест чата курса Human 2.0. Читает get_workshop_chat_json / get_changed_since через human20-helper и формирует краткую сводку новых сообщений (N сообщений, K авторов, цитаты).
version: 0.1.0
author: reclaw17
license: MIT
metadata:
  hermes:
    tags: [human20, digest, telegram, cron]
    related: [human20-helper]
---

# human20-chat-digest

Надстройка над [`human20-helper`](../human20-helper/SKILL.md) — собирает новые
сообщения из чата курса Human 2.0 и формирует короткий дайджест.

Используется:

- как `cron`-задача каждые 30 минут с доставкой в чат;
- вручную через CLI: `python3 digest.py --dry-run` или `--since-message-id <id>`;
- как библиотека: `from digest import build_digest`.

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
- Токен `HUMAN20_BEARER_TOKEN` берётся из окружения или из
  `~/.hermes/.env` автоматически — никаких захардкоженных секретов.
- `state.json` хранит только ID последнего сообщения, никаких текстов.

## Использование

```bash
# разово, посмотреть что есть (без записи state.json)
python3 digest.py --dry-run

# с лимитом (по умолчанию 200)
python3 digest.py --limit 500 --dry-run

# сбросить курсор (прочитать всё заново)
python3 digest.py --reset --dry-run

# из cron: отдать JSON в stdout
python3 digest.py --json
```

## Cron (пример)

```bash
hermes cron create 30m \
  --prompt "Запусти human20-chat-digest и пришли результат в этот чат" \
  --skills human20-chat-digest,human20-helper \
  --deliver origin
```

## Структура

```
human20-chat-digest/
├── SKILL.md          ← этот файл
├── README.md         ← описание для GitHub
├── digest.py         ← основной скрипт
├── state.json        ← курсор (last_message_id), создаётся автоматически
└── tests/
    └── test_digest.py
```

## Зависимости

- Python 3.10+
- `human20-helper` скилл установлен (нужен `human20_mcp_client.py`)
- `HUMAN20_BEARER_TOKEN` в `~/.hermes/.env`