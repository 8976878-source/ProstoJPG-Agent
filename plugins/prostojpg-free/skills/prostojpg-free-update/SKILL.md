---
name: prostojpg-free-update
description: ProstoJPG Free — обновить плагин до последней версии с GitHub. Использовать для «обнови», «обновить плагин», «проверь обновления», «update plugin». Скачивает свежую версию и показывает, какая была и какая стала.
---

# ProstoJPG Free — Обновление

## Когда срабатывает

Пользователь написал «обнови», «обнови плагин», «проверь обновления», «update».

## Шаги

1. Не спрашивайте подтверждение — это явная команда. Сразу выполните:
   `python3 plugins/prostojpg-free/scripts/cards.py update`
   (путь относительно корня плагина — папки, где лежит `.claude-plugin/plugin.json`).
2. Скрипт скачает `main`, сделает fast-forward merge и напечатает одну из строк:
   `Обновлено: 1.0.5 -> 1.0.6` или `Уже последняя версия: 1.0.6`.
3. Если плагин установлен клиентом с менеджером плагинов (Claude Code, Codex),
   установленная копия обновляется отдельно — дайте пользователю команды:
   - Claude Code: `/plugin marketplace update prostojpg-free-marketplace`,
     затем `/plugin update prostojpg-free@prostojpg-free-marketplace`
   - Codex: `codex plugin marketplace upgrade prostojpg-free-marketplace`,
     затем `codex plugin add prostojpg-free@prostojpg-free-marketplace`
4. Предложите открыть новый чат или выполнить `/reload-plugins`, чтобы
   подхватились новые навыки.

## Ограничения

- Сеть используется только здесь и только по явной команде «обнови».
  Генерация карточек по-прежнему никуда не ходит.
- Не обновляйте плагин молча, без команды пользователя.
- Если папка без `.git` — не выдумывайте, скажите переустановить:
  `git clone --depth 1 https://github.com/8976878-source/ProstoJPG-Free.git`
