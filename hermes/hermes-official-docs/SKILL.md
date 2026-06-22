---
name: hermes-official-docs
description: При любом вопросе про Hermes (CLI, конфиг, fallback, провайдеры, hot-reload, формат скилла, пути ~/.hermes/) — сначала официальная документация https://hermes-agent.nousresearch.com/docs, потом локальные доки через skill `hermes-docs-local`, потом skill `hermes-agent`. Офф доки — canonical source of truth.
---

# Hermes Official Docs — правило навигации по документации

**Source of truth:** https://hermes-agent.nousresearch.com/docs

Это правило определяет порядок поиска ответов на любые Hermes-специфичные вопросы. Skill `hermes-agent` даёт **workflow-guidance**, офф доки дают **точные флаги/пути/поведение**.

## Когда применять

Перед ЛЮБЫМ ответом пользователю про:
- Hermes CLI (флаги, subcommands, аргументы)
- Конфиг `~/.hermes/config.yaml` (секции, ключи, значения)
- Fallback chain (`hermes fallback add/list/remove`)
- Model providers и провайдер-специфичное поведение
- Hot-reload (что перезагружается на лету, что нет)
- Skill format (`SKILL.md` frontmatter, `references/`, `scripts/`, `templates/`)
- Пути в `~/.hermes/` (skills, scripts, .env, cache)
- Безопасность (secrets, sandbox, what `hermes` blocks)
- Плагины и расширения

## Иерархия источников (от важного к менее важному)

### 1. 🥇 Офф доки — `https://hermes-agent.nousresearch.com/docs`

**Всегда первым.** Это canonical reference. Если что-то работает не как ты ожидаешь — RTFM, а не угадывай.

Быстрый доступ через `web_extract`:
```python
web_extract(urls=["https://hermes-agent.nousresearch.com/docs/<path>"])
```

См. `references/docs-index.md` для прямых ссылок на разделы.

### 2. 🥈 Локальные доки через skill `hermes-docs-local`

Если офф доки недоступны (нет сети) или нужен более глубокий разбор, грузи skill `hermes-docs-local`. В нём — структурированная документация по Hermes, адаптированная под наш проект.

```bash
# Загрузить локальные доки
skill_view(name="hermes-docs-local")
```

**Когда использовать:**
- Нужны примеры команд в контексте нашего проекта
- Офф доки не отвечают на конкретный вопрос
- Нужна связка с нашими custom skills

### 3. 🥉 Skill `hermes-agent`

Грузи **только** для workflow-guidance: какие skills существуют, в каком порядке их применять, что подходит для какой задачи.

```bash
skill_view(name="hermes-agent")
```

**НЕ использовать `hermes-agent` для:**
- Точных флагов CLI (всегда проверяй в доках)
- Точных путей в `~/.hermes/`
- Точного поведения hot-reload
- Любых утверждений формата «X работает так-то» — это надо подтвердить в доках

### 4. ❓ Спросить пользователя

Если ни один источник не дал ответа — **не выдумывай**. Спроси. Особенно если речь про:
- Деструктивные операции (reset, --force, --hard)
- Чужие credentials / secrets
- Изменения в публичных репо

## Как проверять перед публикацией skill / конфига

1. Открыть офф доки по теме.
2. Сверить написанное в skill с тем, что в доках.
3. Если расхождение — доки правы, skill чини.
4. Только после сверки — публикация.

## Pitfalls

1. **«Я работал с Hermes, я знаю» — нет, проверь в доках.** Hermes активно развивается, флаги и поведение меняются. То, что работало в 0.15, может быть deprecated в 0.16.

2. **Офф доки могут отставать от main-ветки.** Если docs явно старые (видишь «coming soon» или пустые разделы) — ищи в `references/docs-index.md` ссылку на GitHub `NousResearch/hermes-agent` для свежей версии.

3. **`hermes-agent` skill ≠ офф доки.** Skill даёт high-level workflow, доки — точные команды. Не путай.

4. **Не доверяй примерам в чужих скиллах/issue-трекерах** про Hermes — они могут быть устаревшими.

5. **Если офф доки и skill расходятся** — офф доки правы. Зафиксируй расхождение, открой issue если можешь.

## Verification

Перед тем как отвечать пользователю про Hermes:
1. ☐ Загрузил офф доки (или `references/docs-index.md` если нет сети).
2. ☐ Сверил с локальными доками через `hermes-docs-local` (если тема нестандартная).
3. ☐ Проверил через skill `hermes-agent` если нужны workflow-подсказки.
4. ☐ Готов процитировать раздел доки, на который опираешься.

## Связанные skill'ы

- `hermes-agent` — основной skill про Hermes (workflow + CLI overview)
- `hermes-docs-local` — локальные доки, адаптированные под проект
- `hermes-skills-subsystem` — диагностика skills lock.json / install
- `pre-publish-sanity-check` — обязательно прогонять перед публикацией скиллов/конфигов

## Файлы

- `references/docs-index.md` — каталог прямых ссылок на разделы офф доков (CLI, fallback, providers, hot-reload, skill format, etc.). Обновляй при обнаружении новых разделов.
