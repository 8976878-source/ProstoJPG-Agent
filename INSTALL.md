# Установка ПростоJPG-Агент

Плагин работает на встроенном инструменте генерации изображений агента.
**Вход в ChatGPT, API-ключи и подписки не нужны.**

## Здесь, в Arena Agent Mode

Плагин уже установлен в этом воркспейсе: `/home/user/ProstoJPG-Agent`.
Просто приложите фото карточки и напишите:

> создай похожую карточку

## Новый чат в Arena

Плагин не сохраняется между чатами — он лежит в воркспейсе, а не в реестре Arena.
В новом чате с пустым `/home/user` выполните:

```bash
git clone --depth 1 https://github.com/8976878-source/ProstoJPG-Agent.git /home/user/ProstoJPG-Agent
```

Если папка уже есть — `bash update.sh`.

## Codex

```text
codex plugin marketplace add 8976878-source/ProstoJPG-Agent
codex plugin add prostojpg-free@prostojpg-free-marketplace
```

Локально, без GitHub:

```text
codex plugin marketplace add /абсолютный/путь/ProstoJPG-Agent
codex plugin add prostojpg-free@prostojpg-free-marketplace
```

Команды: `$prostojpg-free-1`, `$prostojpg-free-2`, `$prostojpg-free-3`.

## Claude Code

```text
claude plugin marketplace add 8976878-source/ProstoJPG-Agent
claude plugin install prostojpg-free@prostojpg-free-marketplace
```

Команды: `/prostojpg-free:prostojpg-free-1`, `-2`, `-3`.

## Любой другой агент (Cursor, Gemini CLI, свой бот)

Скопируйте `plugins/prostojpg-free/skills/*` в каталог навыков клиента или
передайте `SKILL.md` как системную инструкцию. Единственная зависимость —
Python 3.9+ и Pillow:

```bash
pip install "Pillow>=10.4"
python3 plugins/prostojpg-free/scripts/cards.py --help
```

## Проверка установки

```bash
python3 plugins/prostojpg-free/scripts/cards.py prepare --sources <ваш.zip> --job-dir job --mode 1
python3 plugins/prostojpg-free/scripts/cards.py info --job-dir job
```

## Обновление

| Клиент | Как обновить |
|---|---|
| Arena | написать в чате **«обнови»** — плагин обновится сам; вручную — `bash update.sh` |
| Claude Code | `claude plugin marketplace update prostojpg-free-marketplace` → `claude plugin update prostojpg-free@prostojpg-free-marketplace` → `/reload-plugins` или новый чат |
| Codex | `codex plugin marketplace upgrade prostojpg-free-marketplace` → `codex plugin add prostojpg-free@prostojpg-free-marketplace` |

Версию установленного плагина показывает `python3 plugins/prostojpg-free/scripts/cards.py version`.
В Claude Code — `/plugin list`, в Codex — `codex plugin list`.

Автообновление в Claude Code выключено для сторонних маркетплейсов по умолчанию:
включается в `/plugin` → Marketplaces → «Enable auto-update».
