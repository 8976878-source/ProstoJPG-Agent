#!/usr/bin/env bash
# Обновление ProstoJPG Free из GitHub. Нужен git и сеть.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .git ]; then
  echo "Это копия без .git — обновить нельзя."
  echo "Переустановите: git clone --depth 1 https://github.com/8976878-source/ProstoJPG-Free.git"
  exit 1
fi

git fetch --quiet origin main
git merge --ff-only --quiet origin/main
echo "Обновлено: $(python3 plugins/prostojpg-free/scripts/cards.py version)"
