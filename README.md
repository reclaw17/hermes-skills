# hermes-skills

Коллекция скиллов для [Hermes Agent](https://hermes-agent.nousresearch.com/) от reclaw17.

Каждый скилл — самодостаточный, читается через `hermes skills install <url>` или
вручную кладётся в `~/.hermes/skills/<name>/`.

## Скиллы

| Скилл | Назначение |
|---|---|
| [`human20-skills/`](./human20-skills/) | Надстройки над [Human 2.0](https://human20.app/) — дайджест чата курса и др. |

## human20-chat-digest

Периодический дайджест чата курса Human 2.0:

- читает `get_workshop_chat_json` через Human20 MCP;
- хранит курсор (`message_id`) в локальном `state.json`;
- работает с `cron` каждые 30 минут, доставка в любой чат Hermes.

➡️ [Документация](./human20-skills/SKILL.md)

## Установка

```bash
# Скилл целиком
git clone https://github.com/reclaw17/hermes-skills.git
cp -r hermes-skills/human20-skills/human20-chat-digest ~/.hermes/skills/
hermes skills reload
```

## Лицензия

MIT
