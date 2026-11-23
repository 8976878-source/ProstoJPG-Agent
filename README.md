# ПростоJPG Free от ПростоСеллера

Создавайте карточки товаров для Wildberries и Ozon по загруженным фото.
Промпты уже встроены. **Без входа в ChatGPT, без API-ключей и без подписок** —
генерация идёт встроенным инструментом генерации изображений того агента, в
котором вы работаете.

## Чем отличается от ProstoJPG 2.0

| | ProstoJPG 2.0 | **ProstoJPG Free** |
|---|---|---|
| Генерация | Codex + вход через ChatGPT | инструмент генерации самого агента |
| Логин / ключ / подписка | нужен аккаунт ChatGPT | **не нужны** |
| Где работает | Codex / Claude Code | Arena, Codex, Claude Code, Cursor, любой агент с генерацией картинок |
| Браузерное расширение | нужно для скачивания фото | **не нужно** — фото прикладываются в чат |
| Обработка файлов | локальные скрипты | локальные скрипты (те же правила) |

Качество и «узнаваемость товара» зависят от генератора вашего клиента: чем
сильнее модель изображений, тем ближе результат к оригинальной карточке.

## Быстрый старт

1. Приложите в чат исходные фото карточки (можно ZIP, папку или файл).
2. Выберите режим и напишите команду.

| Режим | Команда в Arena | В Codex | В Claude Code | Что делает |
|---|---|---|---|---|
| 1 | «создай похожую карточку» | `$prostojpg-free-1` | `/prostojpg-free:prostojpg-free-1` | похожая карточка, товар узнаваем |
| 2 | «замени товар на моём фото и смени лицо» | `$prostojpg-free-2` | `/prostojpg-free:prostojpg-free-2` | исходник + ваш товар + новое лицо |
| 3 | «замени товар, лицо не меняй» | `$prostojpg-free-3` | `/prostojpg-free:prostojpg-free-3` | исходник + ваш товар, лицо прежнее |

Артикул и собственный промпт не нужны.

## Правила результата

- Пропорции каждого фото — как у оригинала.
- Короткая сторона не меньше 1200 px; недостающее добивается белыми полями без
  обрезки товара.
- Готовые фото — отдельными файлами, без ZIP.
- Видео не генерируются.
- Исходники и результаты остаются у вас; плагин не ходит ни в какие платные API.

## Установка

Полная инструкция — [INSTALL.md](INSTALL.md). Здесь, в Arena, плагин уже стоит:
`/home/user/ProstoJPG-Free`. Для Codex и Claude Code:

```text
codex plugin marketplace add 8976878-source/ProstoJPG-Free
codex plugin add prostojpg-free@prostojpg-free-marketplace
```

```text
claude plugin marketplace add 8976878-source/ProstoJPG-Free
claude plugin install prostojpg-free@prostojpg-free-marketplace
```

Зависимость для сборки фото: Python 3.9+ и `pip install "Pillow>=10.4"`.

## Структура

```
.agents/plugins/marketplace.json        marketplace для Codex
.claude-plugin/marketplace.json          marketplace для Claude Code
plugins/prostojpg-free/
  .claude-plugin/plugin.json
  skills/prostojpg-free-1..3/SKILL.md    навыки трёх режимов
  scripts/cards.py                       prepare / export / info (без сети)
  scripts/requirements.txt               Pillow
references/generation.md                 правила обработки и диагностика
downloads/*.zip                          готовые архивы плагина
```

Версия 1.0.0. Лицензия: MIT (см. LICENSE).
