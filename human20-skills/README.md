# human20-chat-digest

Периодический дайджест чата курса [Human 2.0](https://human20.app).

Надстройка над [`human20-helper`](https://github.com/reclaw17/hermes-skills/tree/main/human20-skills/human20-helper) — собирает новые сообщения из чата курса и формирует короткую сводку для Telegram / cron-доставки.

## Что делает

- Ходит в `get_workshop_chat_json` через Human20 MCP.
- Фильтрует сообщения с `message_id > last_message_id`.
- Возвращает JSON: `count`, `authors`, `items[]` (id / date / username / preview).
- Хранит курсор в `state.json` (рядом со скриптом), `chmod 600`.

## Что **не** делает

- Не отправляет сообщения в Human20.
- Не использует `send_user_message` / `preview_user_message`.
- Не хранит тексты сообщений локально — только `message_id`.

## Использование

```bash
python3 digest.py --dry-run          # посмотреть, что есть (state не меняется)
python3 digest.py --reset --dry-run  # сбросить курсор
python3 digest.py --limit 500        # поднять лимит
python3 digest.py --json             # вывести JSON вместо текста
```

## Cron

```bash
hermes cron create 30m \
  --prompt "Запусти human20-chat-digest и пришли результат в этот чат" \
  --skills human20-chat-digest,human20-helper \
  --deliver origin
```

## Требования

- Python 3.10+
- Установленный скилл `human20-helper`
- `HUMAN20_BEARER_TOKEN` в `~/.hermes/.env`

## Лицензия

MIT