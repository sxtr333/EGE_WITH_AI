#!/usr/bin/env python3
"""Скачать все задачи категории Решу ЕГЭ вместе с решениями и alt-формулами."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://math-ege.sdamgia.ru"


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


def extract_problem(div) -> dict:
    link = div.select_one("span.prob_nums a")
    pid = link.get_text(strip=True) if link else None
    body = div.select_one("div.pbody")
    sol = div.select_one(f"#sol{pid}") if pid else None
    answer_div = div.select_one("div.answer")
    solution = node_text(sol)
    formulas = [clean(f) for f in re.findall(r"⟦(.*?)⟧", solution)]
    return {
        "id": pid,
        "condition": node_text(body),
        "solution": solution,
        "formulas_raw": formulas,
        "answer": clean(answer_div.get_text(" ", strip=True)) if answer_div else "",
        "url": f"{BASE}/problem?id={pid}" if pid else "",
    }


def fetch_category(category_id: str) -> list[dict]:
    url = f"{BASE}/test?filter=all&category_id={category_id}&print=true"
    response = requests.get(
        url,
        timeout=120,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ege-navigator/0.1)"},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    return [extract_problem(div) for div in soup.select("div.prob_maindiv")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("category_id", help="например 79 для прямоугольного треугольника")
    parser.add_argument("--name", default="", help="имя файла, например pryamougolnyy")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
    )
    args = parser.parse_args()

    problems = fetch_category(args.category_id)
    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.name or f"cat{args.category_id}"
    out_json = args.out / f"{stem}.json"
    out_json.write_text(json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [f"# category {args.category_id} · {len(problems)} задач", ""]
    for p in problems:
        lines.append("=" * 60)
        lines.append(f"ID {p['id']}")
        lines.append(f"УСЛОВИЕ: {p['condition']}")
        lines.append("ФОРМУЛЫ:")
        for f in p["formulas_raw"]:
            lines.append(f"  • {f}")
        lines.append(f"РЕШЕНИЕ: {p['solution'][:1200]}")
        lines.append("")
    out_txt = args.out / f"{stem}_for_analysis.txt"
    out_txt.write_text("\n".join(lines), encoding="utf-8")

    print(f"saved {len(problems)} problems")
    print(out_json)
    print(out_txt)


if __name__ == "__main__":
    main()
