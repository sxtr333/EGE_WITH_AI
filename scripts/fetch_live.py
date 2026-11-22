#!/usr/bin/env python3
"""
Живой сбор подтипа с Решу ЕГЭ (без ручного Save As).

Берёт print-страницу категории:
  https://math-ege.sdamgia.ru/test?filter=all&category_id=ID&print=true

Достаёт:
  - условие, решение, alt-тексты формул
  - картинки чертежей (/get_file?id=...) в data/figures/<category>/

Пример:
  .venv/bin/python scripts/fetch_live.py 113 --name vpisanные
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://math-ege.sdamgia.ru"
ROOT = Path(__file__).resolve().parents[1]


def clean(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u00ad", "")
    return re.sub(r"\s+", " ", text).strip()


def node_text(node) -> str:
    if node is None:
        return ""
    parts: list[str] = []
    for el in node.descendants:
        name = getattr(el, "name", None)
        if name == "img":
            alt = (el.get("alt") or "").strip()
            if alt:
                parts.append("⟦" + clean(alt) + "⟧")
        elif isinstance(el, str):
            parent = el.parent.name if el.parent else ""
            if parent in {"script", "style"}:
                continue
            t = el.strip()
            if t:
                parts.append(t)
    return clean(" ".join(parts))


def abs_url(src: str | None) -> str | None:
    if not src:
        return None
    return urljoin(BASE + "/", src)


def fetch_category(category_id: str, session: requests.Session) -> tuple[str, list[dict]]:
    url = f"{BASE}/test?filter=all&category_id={category_id}&print=true"
    r = session.get(url, timeout=120)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    problems = []
    for div in soup.select("div.prob_maindiv"):
        link = div.select_one("span.prob_nums a")
        pid = link.get_text(strip=True) if link else None
        body = div.select_one("div.pbody")
        sol = div.select_one(f"#sol{pid}") if pid else None
        answer_div = div.select_one("div.answer")
        solution = node_text(sol)
        fig = None
        if body:
            img = body.select_one('img[src*="get_file"]')
            if img:
                fig = abs_url(img.get("src"))
        problems.append(
            {
                "id": pid,
                "condition": node_text(body),
                "solution": solution,
                "formulas_raw": [clean(f) for f in re.findall(r"⟦(.*?)⟧", solution)],
                "answer": clean(answer_div.get_text(" ", strip=True)) if answer_div else "",
                "figure_url": fig,
                "url": f"{BASE}/problem?id={pid}" if pid else "",
            }
        )
    return r.text, problems


def download_figures(problems: list[dict], out_dir: Path, session: requests.Session) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in problems:
        url = p.get("figure_url")
        if not url:
            continue
        ext = ".png"
        path = out_dir / f"{p['id']}{ext}"
        if path.exists() and path.stat().st_size > 0:
            p["figure_path"] = str(path)
            continue
        try:
            resp = session.get(url, timeout=60)
            resp.raise_for_status()
            ctype = resp.headers.get("content-type", "")
            if "jpeg" in ctype or "jpg" in ctype:
                path = out_dir / f"{p['id']}.jpg"
            elif "svg" in ctype:
                path = out_dir / f"{p['id']}.svg"
            elif "gif" in ctype:
                path = out_dir / f"{p['id']}.gif"
            path.write_bytes(resp.content)
            p["figure_path"] = str(path)
            n += 1
            time.sleep(0.15)
        except Exception as e:  # noqa: BLE001
            p["figure_error"] = str(e)
    return n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("category_id")
    parser.add_argument("--name", default="")
    parser.add_argument("--no-images", action="store_true")
    args = parser.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (compatible; ege-navigator/0.2)"

    html, problems = fetch_category(args.category_id, session)
    stem = args.name or f"cat{args.category_id}"
    raw_dir = ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"{stem}.html").write_text(html, encoding="utf-8")

    figs = 0
    if not args.no_images:
        figs = download_figures(problems, ROOT / "data" / "figures" / stem, session)

    out_json = raw_dir / f"{stem}.json"
    out_json.write_text(json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [f"# {stem} · category {args.category_id} · {len(problems)} задач", ""]
    for p in problems:
        lines += [
            "=" * 60,
            f"ID {p['id']}",
            f"FIGURE: {p.get('figure_path') or p.get('figure_url') or '-'}",
            f"УСЛОВИЕ: {p['condition']}",
            "ФОРМУЛЫ:",
        ]
        lines += [f"  • {f}" for f in p.get("formulas_raw") or []]
        lines += [f"РЕШЕНИЕ: {p['solution'][:1800]}", ""]
    out_txt = raw_dir / f"{stem}_analysis.txt"
    out_txt.write_text("\n".join(lines), encoding="utf-8")

    print(f"problems: {len(problems)}")
    print(f"with figures urls: {sum(1 for p in problems if p.get('figure_url'))}")
    print(f"downloaded figures: {figs}")
    print(out_json)
    print(out_txt)


if __name__ == "__main__":
    main()
