# hermes-skills

Коллекция скиллов для [Hermes Agent](https://hermes-agent.nousresearch.com/) от reclaw17.

Устанавливаются через `hermes skills install <url>` или копированием в `~/.hermes/skills/<name>/`.

## Скиллы

| Категория | Скилл | Назначение |
|---|---|---|
| `human20-skills/` | [human20-chat-digest](./human20-skills/human20-chat-digest/SKILL.md) | Периодический дайджест чата курса Human 2.0 через Human20 MCP |
| `github/` | [github-sync-agent-work](./github/github-sync-agent-work/SKILL.md) | Двусторонняя синхронизация файлов между `agent-work` и GitHub через `gh api` (без `git clone`) |

## Структура репо

```
hermes-skills/
├── human20-skills/            # скиллы для Human 2.0
│   └── human20-chat-digest/
├── github/                    # скиллы для работы с GitHub
│   └── github-sync-agent-work/
└── README.md
```

## Установка

### Через `hermes skills install` (рекомендуется)

```bash
hermes skills install https://github.com/reclaw17/hermes-skills
hermes skills reload
```

### Вручную

```bash
git clone https://github.com/reclaw17/hermes-skills.git

# Скопировать нужный скилл целиком
cp -r hermes-skills/<category>/<skill-name> ~/.hermes/skills/

hermes skills reload
```

## Как добавить свой скилл

1. Создай папку `<category>/<skill-name>/` — категория это тематическая группа (`github/`, `human20-skills/`, и т.д.).
2. Положи туда `SKILL.md` с YAML-фронтматтером (`name`, `description`).
3. Если нужны вспомогательные файлы:
   - `scripts/` — исполняемые скрипты
   - `references/` — длинные документы, на которые ссылается SKILL.md
   - `templates/` — шаблоны файлов
4. Добавь строку в таблицу «Скиллы» в этом README.
5. Открой PR.

Шаблон `SKILL.md`:

```markdown
---
name: my-skill
description: Краткое описание (1-2 строки, что делает и когда использовать).
---

# Заголовок скилла

## Когда использовать
…

## Команды / шаги
…
```

## Лицензия

MIT
