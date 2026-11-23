# Установка ProstoJPG Free

Плагин работает на встроенном инструменте генерации изображений агента.
**Вход в ChatGPT, API-ключи и подписки не нужны.**

## Здесь, в Arena Agent Mode

Плагин уже установлен в этом воркспейсе: `/home/user/ProstoJPG-Free`.
Просто приложите фото карточки и напишите:

> создай похожую карточку

## Codex

```text
codex plugin marketplace add <owner>/ProstoJPG-Free
codex plugin add prostojpg-free@prostojpg-free-marketplace
```

Локально, без GitHub:

```text
codex plugin marketplace add /абсолютный/путь/ProstoJPG-Free
codex plugin add prostojpg-free@prostojpg-free-marketplace
```

Команды: `$prostojpg-free-1`, `$prostojpg-free-2`, `$prostojpg-free-3`.

## Claude Code

```text
claude plugin marketplace add <owner>/ProstoJPG-Free
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

Повторите команды установки (для Git-marketplace при необходимости
`codex plugin marketplace upgrade`) и откройте новый чат.
