#!/usr/bin/env bash
# Обновление ПростоJPG-Агент. Нужен git и сеть.
set -euo pipefail
cd "$(dirname "$0")"
python3 plugins/prostojpg-free/scripts/cards.py update
