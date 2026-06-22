# Hermes Docs Index

Прямые ссылки на разделы официальной документации [https://hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs). Обновляй при обнаружении новых разделов.

## Корневые разделы

| Раздел | URL |
|---|---|
| Главная (Getting Started) | `https://hermes-agent.nousresearch.com/docs` |
| User Guide | `https://hermes-agent.nousresearch.com/docs/user-guide/` |
| Developer Guide | `https://hermes-agent.nousresearch.com/docs/developer-guide/` |
| API Reference | `https://hermes-agent.nousresearch.com/docs/api-reference/` |
| Skills | `https://hermes-agent.nousresearch.com/docs/skills/` |
| CLI | `https://hermes-agent.nousresearch.com/docs/cli/` |

## User Guide — основные фичи

| Фича | URL |
|---|---|
| Fallback providers | `https://hermes-agent.nousresearch.com/docs/user-guide/features/fallback-providers` |
| Memory | `https://hermes-agent.nousresearch.com/docs/user-guide/features/memory` |
| Skills | `https://hermes-agent.nousresearch.com/docs/user-guide/features/skills` |
| Cron | `https://hermes-agent.nousresearch.com/docs/user-guide/features/cron` |
| Webhooks | `https://hermes-agent.nousresearch.com/docs/user-guide/features/webhooks` |
| Plugins | `https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins` |
| Multi-profile | `https://hermes-agent.nousresearch.com/docs/user-guide/features/profiles` |
| Kanban | `https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban` |

## CLI — команды и флаги

| Команда | URL |
|---|---|
| `hermes` (root) | `https://hermes-agent.nousresearch.com/docs/cli/` |
| `hermes config` | `https://hermes-agent.nousresearch.com/docs/cli/config` |
| `hermes model` | `https://hermes-agent.nousresearch.com/docs/cli/model` |
| `hermes fallback` | `https://hermes-agent.nousresearch.com/docs/cli/fallback` |
| `hermes skills` | `https://hermes-agent.nousresearch.com/docs/cli/skills` |
| `hermes cron` | `https://hermes-agent.nousresearch.com/docs/cli/cron` |
| `hermes memory` | `https://hermes-agent.nousresearch.com/docs/cli/memory` |
| `hermes secrets` | `https://hermes-agent.nousresearch.com/docs/cli/secrets` |
| `hermes chat` | `https://hermes-agent.nousresearch.com/docs/cli/chat` |
| `hermes gateway` | `https://hermes-agent.nousresearch.com/docs/cli/gateway` |

## Skills — формат и жизненный цикл

| Тема | URL |
|---|---|
| Skill format | `https://hermes-agent.nousresearch.com/docs/skills/format` |
| Skill frontmatter | `https://hermes-agent.nousresearch.com/docs/skills/frontmatter` |
| Installing skills | `https://hermes-agent.nousresearch.com/docs/skills/installing` |
| Skill development | `https://hermes-agent.nousresearch.com/docs/skills/development` |
| Bundled skills | `https://hermes-agent.nousresearch.com/docs/skills/bundled` |

## Developer Guide — расширение

| Тема | URL |
|---|---|
| Plugins ABC | `https://hermes-agent.nousresearch.com/docs/developer-guide/plugins` |
| ContextEngine | `https://hermes-agent.nousresearch.com/docs/developer-guide/context-engine` |
| MemoryProvider | `https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider` |
| Tool providers | `https://hermes-agent.nousresearch.com/docs/developer-guide/tool-providers` |

## API Reference

| API | URL |
|---|---|
| REST API | `https://hermes-agent.nousresearch.com/docs/api/rest` |
| WebSocket | `https://hermes-agent.nousresearch.com/docs/api/websocket` |
| Gateway | `https://hermes-agent.nousresearch.com/docs/api/gateway` |

## Когда URL не работает

Если ссылка 404 или редиректит, есть три fallback'а:

1. **Попробуй обрезать path до родителя.** Например, `/docs/user-guide/features/fallback-providers` → `/docs/user-guide/features/`.
2. **Ищи через поиск на сайте:** `https://hermes-agent.nousresearch.com/docs?q=<keyword>`.
3. **Загляни в GitHub `NousResearch/hermes-agent`**, ветка `main`, папка `docs/` — это источник, оттуда собирается сайт.

## Связанные ресурсы

- Skill `hermes-agent` — workflow и общий обзор.
- Skill `hermes-docs-local` — локальные доки, адаптированные под проект.
- GitHub: `https://github.com/NousResearch/hermes-agent` (исходник офф доков + код).
