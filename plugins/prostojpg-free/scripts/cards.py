#!/usr/bin/env python3
"""ПростоJPG-Агент — локальная подготовка и сборка карточек товара.

Скрипт НЕ обращается к сети и НЕ вызывает никаких AI-API и не требует логинов.
Он только:
  prepare — собирает исходники (ZIP / папка / файл), считает пропорции и целевые
            размеры, сохраняет задание job.json со встроенными промптами;
  export  — приводит готовые изображения от генератора агента к нужным пропорциям,
            добивает короткую сторону до >= min-side белыми полями (без обрезки
            товара) и сохраняет итоговые файлы отдельно, без ZIP;
  info    — печатает состояние задания.

Зависимости: Python 3.9+ и Pillow.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.stderr.write("Ошибка: не установлен Pillow. Выполните: pip install 'Pillow>=10.4'\n")
    raise SystemExit(2)

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"}

# Встроенные промпты. Пользователю их писать не нужно.
PROMPTS = {
    "1": (
        "Create a similar photo. Slightly change the camera angle and some visual "
        "details while keeping the product recognizable. Improve the image quality. "
        "If the source photo contains text blocks, slightly adjust their colors and "
        "shapes while preserving the wording and readability. If a person is present "
        "in the source photo, change their face and hairstyle so they look like a "
        "different person, while keeping the overall look and style recognizable."
    ),
    "2": (
        "Take the composition, background, lighting and text blocks of the source "
        "card photo. Replace the product shown in it with the product from the "
        "provided reference photo of my own product: keep its exact shape, color, "
        "material, logo and proportions unchanged, adapt it naturally to the pose, "
        "perspective, shadows and reflections of the scene. Also change the person's "
        "face and hairstyle so they look like a different person while keeping the "
        "overall look, clothing and style recognizable."
    ),
    "3": (
        "Take the composition, background, lighting and text blocks of the source "
        "card photo. Replace the product shown in it with the product from the "
        "provided reference photo of my own product: keep its exact shape, color, "
        "material, logo and proportions unchanged, adapt it naturally to the pose, "
        "perspective, shadows and reflections of the scene. Keep the person's face, "
        "facial features, hairstyle and identity exactly as in the source photo."
    ),
}

MODE_TITLE = {
    "1": "Создать похожие карточки",
    "2": "Исходная карточка + мой товар + замена лица",
    "3": "Исходная карточка + мой товар, лицо не меняем",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def natural_key(path: Path):
    import re

    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", path.name)]


def collect_images(sources: Path, work: Path) -> tuple[list[Path], list[str]]:
    """Возвращает (изображения, заметки). ZIP распаковывается в work/extracted."""
    notes: list[str] = []
    found: list[Path] = []

    def scan_dir(root: Path) -> None:
        for p in sorted(root.rglob("*"), key=natural_key):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext in IMAGE_EXT:
                found.append(p)
            elif ext in VIDEO_EXT:
                notes.append(f"пропущено видео: {p.name}")

    if sources.is_dir():
        scan_dir(sources)
    elif sources.suffix.lower() == ".zip":
        extracted = work / "extracted"
        extracted.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(sources) as zf:
            for info in zf.infolist():
                name = info.filename
                if name.endswith("/"):
                    continue
                # защита от zip-slip
                target = (extracted / name).resolve()
                if not str(target).startswith(str(extracted.resolve())):
                    notes.append(f"пропущен подозрительный путь в ZIP: {name}")
                    continue
                zf.extract(info, extracted)
        scan_dir(extracted)
    elif sources.is_file() and sources.suffix.lower() in IMAGE_EXT:
        found = [sources]
    elif sources.is_file():
        raise SystemExit(f"Ошибка: {sources} не является изображением, папкой или ZIP.")
    else:
        raise SystemExit(f"Ошибка: путь не найден: {sources}")

    # EXIF-ориентация учитывается при расчёте пропорций
    return found, notes


def image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as im:
        im = _apply_exif(im)
        return im.size


def _apply_exif(im: Image.Image) -> Image.Image:
    try:
        from PIL import ImageOps

        return ImageOps.exif_transpose(im)
    except Exception:
        return im


def target_size(width: int, height: int, min_side: int, max_side: int) -> tuple[int, int]:
    """Пропорции сохраняются; короткая сторона >= min_side; длинная <= max_side."""
    short = min(width, height)
    long = max(width, height)
    scale = max(1.0, min_side / short) if short else 1.0
    if long * scale > max_side:
        scale = max_side / long
    w = max(min_side, round(width * scale))
    h = max(min_side, round(height * scale))
    # при кэпе по длинной стороне короткая может оказаться ниже нормы — тогда
    # жертвуем кэпом, а не требованием минимальной короткой стороны
    if min(w, h) < min_side:
        k = min_side / min(w, h)
        w, h = round(w * k), round(h * k)
    return w, h


def cmd_prepare(args: argparse.Namespace) -> int:
    sources = Path(args.sources).expanduser()
    job_dir = Path(args.job_dir).expanduser()
    job_dir.mkdir(parents=True, exist_ok=True)
    src_dir = job_dir / "src"
    gen_dir = job_dir / "generated"
    out_dir = job_dir / "out"
    for d in (src_dir, gen_dir, out_dir):
        d.mkdir(parents=True, exist_ok=True)

    images, notes = collect_images(sources, job_dir)
    if not images:
        raise SystemExit("Ошибка: во входных данных не найдено ни одного изображения.")

    product = None
    if args.product:
        p = Path(args.product).expanduser()
        if not p.is_file():
            raise SystemExit(f"Ошибка: референс своего товара не найден: {p}")
        product = src_dir / f"product{p.suffix.lower()}"
        shutil.copy2(p, product)

    items = []
    for i, path in enumerate(images, start=1):
        item_id = f"{i:02d}"
        ext = path.suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
            ext = ".png"
        stored = src_dir / f"{item_id}{ext}"
        shutil.copy2(path, stored)
        w, h = image_size(stored)
        tw, th = target_size(w, h, args.min_side, args.max_side)
        prompt = PROMPTS[str(args.mode)]
        if str(args.mode) in {"2", "3"} and product is not None:
            prompt = (
                prompt
                + " Use the attached reference photo of my product as the product "
                "reference; the other attached photo is the source card."
            )
        items.append(
            {
                "id": item_id,
                "name": path.name,
                "source": str(stored.relative_to(job_dir)),
                "source_file": str(path),
                "source_size": [w, h],
                "target_size": [tw, th],
                "aspect": round(w / h, 6),
                "prompt": prompt,
                "generated": None,
                "output": None,
            }
        )

    job = {
        "app": "ПростоJPG-Агент",
        "version": "1.0.0",
        "mode": str(args.mode),
        "mode_title": MODE_TITLE[str(args.mode)],
        "min_side": args.min_side,
        "max_side": args.max_side,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "product_reference": str(product.relative_to(job_dir)) if product else None,
        "notes": notes,
        "items": items,
    }
    (job_dir / "job.json").write_text(
        json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    (job_dir / "gallery.html").write_text(render_gallery(job), encoding="utf-8")

    log(f"Задание: {job_dir}")
    log(f"Режим: {MODE_TITLE[str(args.mode)]} (mode {args.mode})")
    log(f"Исходников: {len(items)}")
    if product:
        log(f"Референс своего товара: {product.name}")
    for it in items:
        w, h = it["source_size"]
        tw, th = it["target_size"]
        log(f"  {it['id']}  {it['name']}  {w}x{h} -> {tw}x{th}")
    for n in notes:
        log(f"  ! {n}")
    log("")
    log("Дальше: сгенерируйте изображения инструментом генерации агента по промпту")
    log("из job.json (поле prompt) и положите результаты в " + str(gen_dir))
    log("с именами 01.png, 02.png, ... Затем: cards.py export --job-dir " + str(job_dir))
    return 0


def render_gallery(job: dict) -> str:
    rows = []
    for it in job["items"]:
        rows.append(
            f"<figure><img src='{it['source']}' style='max-width:240px'>"
            f"<figcaption>{it['id']} · {it['name']}<br>"
            f"{it['source_size'][0]}×{it['source_size'][1]} → "
            f"{it['target_size'][0]}×{it['target_size'][1]}</figcaption></figure>"
        )
    css = (
        "body{font:14px/1.5 system-ui,sans-serif;margin:24px;background:#fff;color:#111}"
        "figure{display:inline-block;margin:0 16px 16px 0;vertical-align:top}"
        "img{border-radius:8px;border:1px solid #ddd;background:#fafafa}"
        "figcaption{font-size:12px;color:#555;max-width:240px}"
        "h1{font-size:18px}"
    )
    return (
        "<!doctype html><meta charset='utf-8'><title>ПростоJPG-Агент — исходники</title>"
        f"<style>{css}</style><h1>ПростоJPG-Агент · {job['mode_title']}</h1>"
        + "".join(rows)
    )


def find_generated(job_dir: Path, item: dict, index: int) -> Path | None:
    """Ищем результат генерации по id, затем по порядку файлов."""
    gen_dir = job_dir / "generated"
    if not gen_dir.is_dir():
        return None
    files = sorted(
        [p for p in gen_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXT],
        key=natural_key,
    )
    for p in files:
        if p.stem == item["id"] or p.stem.startswith(item["id"] + "_"):
            return p
    # запасной вариант — по позиции
    if index < len(files) and len(files) == 1:
        return files[0]
    return None


def fit_and_save(src: Path, dst: Path, target: tuple[int, int], min_side: int) -> tuple[int, int]:
    """Пропорции как у оригинала, белые поля вместо обрезки, короткая сторона >= min_side."""
    tw, th = target
    target_aspect = tw / th
    with Image.open(src) as im:
        im = _apply_exif(im)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            canvas = Image.new("RGB", im.size, (255, 255, 255))
            canvas.paste(im, mask=im.split()[-1])
            im = canvas
        else:
            im = im.convert("RGB")
        w, h = im.size
        aspect = w / h
        # 1) приводим к целевым пропорциям только белыми полями
        if abs(aspect - target_aspect) > 0.005:
            if aspect > target_aspect:  # шире нужного -> поля сверху/снизу
                new_h = max(h, round(w / target_aspect))
                new_w = w
            else:
                new_w = max(w, round(h * target_aspect))
                new_h = h
            canvas = Image.new("RGB", (new_w, new_h), (255, 255, 255))
            canvas.paste(im, ((new_w - w) // 2, (new_h - h) // 2))
            im = canvas
        # 2) масштабируем так, чтобы повторить целевой размер и короткую сторону
        w, h = im.size
        scale = max(tw / w, th / h)
        if min(w, h) * scale < min_side:
            scale = max(scale, min_side / min(w, h))
        nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
        if (nw, nh) != (w, h):
            im = im.resize((nw, nh), Image.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.suffix.lower() in {".jpg", ".jpeg"}:
            im.save(dst, "JPEG", quality=92, optimize=True, progressive=True)
        else:
            im.save(dst, "PNG", optimize=True)
        return im.size


def cmd_export(args: argparse.Namespace) -> int:
    job_dir = Path(args.job_dir).expanduser()
    job_path = job_dir / "job.json"
    if not job_path.is_file():
        raise SystemExit(f"Ошибка: нет задания {job_path}. Сначала выполните prepare.")
    job = json.loads(job_path.read_text(encoding="utf-8"))
    out_dir = Path(args.output_dir).expanduser() if args.output_dir else job_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    made, missing = [], []
    for idx, item in enumerate(job["items"]):
        gen = find_generated(job_dir, item, idx)
        if gen is None:
            missing.append(item["id"])
            continue
        item["generated"] = str(gen.relative_to(job_dir))
        dst = out_dir / f"card-{item['id']}.jpg"
        size = fit_and_save(gen, dst, tuple(item["target_size"]), job["min_side"])
        item["output"] = str(dst)
        item["output_size"] = list(size)
        made.append((item["id"], dst.name, size))

    job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")

    log(f"Готово файлов: {len(made)} → {out_dir}")
    ok = True
    for item_id, name, (w, h) in made:
        short = min(w, h)
        flag = "OK" if short >= job["min_side"] else "МАЛО"
        if short < job["min_side"]:
            ok = False
        log(f"  {name}  {w}x{h}  короткая сторона {short} px — {flag}")
    if missing:
        log("  Нет сгенерированных файлов для: " + ", ".join(missing))
    if not made:
        raise SystemExit("Ошибка: в папке generated пусто — генерировать пока нечего.")
    return 0 if ok else 1


def cmd_info(args: argparse.Namespace) -> int:
    job_path = Path(args.job_dir).expanduser() / "job.json"
    if not job_path.is_file():
        raise SystemExit(f"Ошибка: нет задания {job_path}")
    job = json.loads(job_path.read_text(encoding="utf-8"))
    log(f"{job['app']} {job['version']} · {job['mode_title']}")
    log(f"Создано: {job['created']} · минимум короткой стороны: {job['min_side']} px")
    for it in job["items"]:
        log(
            f"  {it['id']} {it['name']} · {it['source_size'][0]}x{it['source_size'][1]}"
            f" -> {it['target_size'][0]}x{it['target_size'][1]}"
            f" · generated={it.get('generated')} · output={it.get('output')}"
        )
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    manifest = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"
    try:
        version = json.loads(manifest.read_text(encoding="utf-8")).get("version", "?")
    except (OSError, ValueError):
        version = "?"
    log(f"ПростоJPG-Агент {version}")
    return 0


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _plugin_version(root: Path) -> str:
    try:
        data = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        return str(data.get("version", "?"))
    except (OSError, ValueError):
        return "?"


def cmd_update(args: argparse.Namespace) -> int:
    """Обновляет плагин из GitHub по явной команде пользователя («обнови»)."""
    root = _plugin_root()
    before = _plugin_version(root)
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("Это копия без git — обновить нельзя.")
        log("Переустановите: git clone --depth 1 "
            "https://github.com/8976878-source/ProstoJPG-Agent.git")
        return 1

    try:
        subprocess.run(["git", "-C", top, "fetch", "--quiet", "origin", "main"], check=True)
        subprocess.run(["git", "-C", top, "merge", "--ff-only", "--quiet", "origin/main"], check=True)
    except subprocess.CalledProcessError as exc:
        log(f"Не удалось обновиться: {exc}")
        return 1

    after = _plugin_version(root)
    if before == after:
        log(f"Уже последняя версия: {after}")
    else:
        log(f"Обновили: {before} -> {after}")
    return 0


FEEDBACK_STATE = Path.home() / ".prostojpg-free" / "feedback.json"


def _load_state(path: Path) -> dict:
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except ValueError:
            pass
    return {}


def _save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_feedback(args: argparse.Namespace) -> int:
    """Просьба об отзыве — не чаще раза в день и до момента, пока отзыв не оставлен."""
    state_path = Path(args.state).expanduser() if args.state else FEEDBACK_STATE
    state = _load_state(state_path)

    if args.done:
        state["done"] = True
        _save_state(state_path, state)
        log("DONE: больше не спрашиваем")
        return 0

    if state.get("done"):
        log("SKIP_DONE: отзыв уже получен")
        return 0

    today = datetime.now().date().isoformat()
    if state.get("last_asked") == today:
        log("SKIP_TODAY: сегодня уже спрашивали")
        return 0

    state["last_asked"] = today
    _save_state(state_path, state)
    log("ASK")
    return 0


STAR_STATE = Path.home() / ".prostojpg-free" / "star.json"


def cmd_star(args: argparse.Namespace) -> int:
    """Просьба о звезде — после каждой карточки, пока пользователь не подтвердит."""
    state_path = Path(args.state).expanduser() if args.state else STAR_STATE
    state = _load_state(state_path)

    if args.done:
        state["done"] = True
        _save_state(state_path, state)
        log("DONE: звезду больше не предлагаем")
        return 0

    if state.get("done"):
        log("SKIP_DONE: звезда уже поставлена")
        return 0

    log("ASK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cards.py",
        description="ПростоJPG-Агент: подготовка исходников и сборка готовых карточек. "
        "Без сети, без AI-API, без логинов.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("prepare", help="собрать задание из ZIP/папки/файла")
    pr.add_argument("--sources", required=True, help="ZIP с фото, папка или файл изображения")
    pr.add_argument("--job-dir", default="job", help="куда положить задание (по умолчанию ./job)")
    pr.add_argument("--mode", default="1", choices=["1", "2", "3"], help="режим карточки")
    pr.add_argument("--product", help="фото своего товара (режимы 2 и 3)")
    pr.add_argument("--min-side", type=int, default=1200, help="минимум короткой стороны, px")
    pr.add_argument("--max-side", type=int, default=4000, help="максимум длинной стороны, px")
    pr.set_defaults(func=cmd_prepare)

    ex = sub.add_parser("export", help="собрать готовые фото из generated/")
    ex.add_argument("--job-dir", default="job")
    ex.add_argument("--output-dir", default=None, help="куда сохранить готовые файлы")
    ex.set_defaults(func=cmd_export)

    inf = sub.add_parser("info", help="показать состояние задания")
    inf.add_argument("--job-dir", default="job")
    inf.set_defaults(func=cmd_info)
    ver = sub.add_parser("version", help="показать версию плагина")
    ver.set_defaults(func=cmd_version)

    upd = sub.add_parser("update", help="обновить плагин из GitHub (только по команде пользователя)")
    upd.set_defaults(func=cmd_update)

    fb = sub.add_parser("feedback", help="напоминание про отзыв в Chrome Web Store (не чаще раза в день)")
    fb.add_argument("--done", action="store_true", help="отзыв оставлен — больше не спрашивать")
    fb.add_argument("--state", default=None, help="путь к файлу состояния (для теста)")
    fb.set_defaults(func=cmd_feedback)

    st = sub.add_parser("star", help="напоминание о звезде на GitHub (после карточки)")
    st.add_argument("--done", action="store_true", help="звезда поставлена — больше не предлагать")
    st.add_argument("--state", default=None, help="путь к файлу состояния (для теста)")
    st.set_defaults(func=cmd_star)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
