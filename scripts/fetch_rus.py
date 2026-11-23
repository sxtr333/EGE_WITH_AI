#!/usr/bin/env python3
"""Скачать задания ЕГЭ по русскому языку, типы 1–27, с печатной страницы Решу ЕГЭ.

Каталог: https://rus-ege.sdamgia.ru/prob_catalog
Полный список задач категории — только print=true.
Старый блок «Задания Д» в вариант 1–27 не входит.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString

BASE = "https://rus-ege.sdamgia.ru"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "rus"


def clean_inline(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u00ad", "").replace("\u2060", "")
    return re.sub(r"[ \t]+", " ", text).strip()


def clean_block(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u00ad", "").replace("\u2060", "")
    text = text.replace("\r", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    out: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if not blank and out:
                out.append("")
            blank = True
            continue
        blank = False
        out.append(line)
    return "\n".join(out).strip()


def node_text(node) -> str:
    if node is None:
        return ""
    clone = BeautifulSoup(str(node), "lxml")
    root = clone.body or clone
    for br in root.find_all("br"):
        br.replace_with("\n")
    for li in root.find_all("li"):
        li.insert_before(NavigableString("\n• "))
    for table in root.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [clean_inline(td.get_text(" ", strip=True)) for td in tr.find_all(["th", "td"])]
            line = " | ".join(c for c in cells if c)
            if line:
                rows.append(line)
        table.replace_with(NavigableString("\n" + "\n".join(rows) + "\n"))
    for img in root.find_all("img"):
        alt = clean_inline(img.get("alt") or "")
        src = img.get("src") or ""
        if alt and "formula" not in src and len(alt) < 200:
            img.replace_with(NavigableString(" " + alt + " "))
        elif "get_file" in src or "formula" in src:
            img.replace_with(NavigableString(" [рисунок] "))
        else:
            img.decompose()
    return clean_block(root.get_text("\n"))


def figure_urls(node) -> list[str]:
    if node is None:
        return []
    urls = []
    for img in node.select("img"):
        src = img.get("src") or ""
        if "get_file" in src or "/formula/" in src:
            urls.append(requests.compat.urljoin(BASE + "/", src))
    return urls


def condition_of(div) -> tuple[str, list[str]]:
    """Текст задачи без повторяющегося справочника «что проверяется».

    На печатной странице у задачи два слоя: длинный блок правила и короткое
    условие. Короткий div.pbody и div.probtext — это задание. Таблица
    «УСЛОВИЕ» внутри правила — учебный пример, его не берём.
    """
    parts: list[str] = []
    seen: set[str] = set()
    figs: list[str] = []

    def add(text: str) -> None:
        text = text.strip()
        if text and text not in seen:
            seen.add(text)
            parts.append(text)

    pt = div.select_one(".probtext")
    if pt:
        add(node_text(pt))
        figs.extend(figure_urls(pt))

    short_bodies = []
    for body in div.select("div.pbody"):
        btext = node_text(body)
        if btext and len(btext) <= 2500:
            short_bodies.append(body)
            add(btext)
            figs.extend(figure_urls(body))

    if not parts:
        for col in div.select("div.col_content"):
            host = col.find_parent("div", class_="pbody")
            if host is not None and len(node_text(host)) > 2500:
                continue
            wrap = col.parent
            name_el = wrap.select_one(".col_name") if wrap else None
            name = clean_inline(name_el.get_text(" ", strip=True)).upper() if name_el else ""
            if "ОТВЕТ" in name and "УСЛОВ" not in name:
                continue
            add(node_text(col))
            figs.extend(figure_urls(col))

    if not parts:
        bodies = div.select("div.pbody")
        if bodies:
            body = max(bodies, key=lambda b: len(node_text(b)))
            add(node_text(body))
            figs.extend(figure_urls(body))

    uniq = []
    for u in figs:
        if u not in uniq:
            uniq.append(u)
    return "\n\n".join(parts), uniq


def parse_catalog(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")

    def cat_id(node) -> str | None:
        a = node.find("a", href=re.compile(r"category_id=\d+"))
        if not a:
            return None
        m = re.search(r"category_id=(\d+)", a.get("href", ""))
        return m.group(1) if m else None

    def direct_name(cat) -> str:
        name_el = None
        for el in cat.find_all(class_="cat_name"):
            if el.find_parent(class_="cat_category") is cat:
                name_el = el
                break
        if name_el is None:
            return ""
        return clean_inline(name_el.get_text(" ", strip=True))

    def count_of(cat) -> int:
        for el in cat.find_all(class_="cat_count"):
            if el.find_parent(class_="cat_category") is cat:
                m = re.search(r"(\d+)", el.get_text(" ", strip=True).replace("\xa0", ""))
                return int(m.group(1)) if m else 0
        return 0

    def children_div(cat):
        for ch in cat.find_all(class_="cat_children"):
            if ch.find_parent(class_="cat_category") is cat:
                return ch
        return None

    def walk(cat) -> dict:
        kids = []
        box = children_div(cat)
        if box:
            for sub in box.find_all(class_="cat_category", recursive=False):
                kids.append(walk(sub))
        return {
            "id": cat_id(cat),
            "name": direct_name(cat),
            "count": count_of(cat),
            "children": kids,
        }

    roots = []
    for cat in soup.select("div.cat_category"):
        if cat.find_parent(class_="cat_category"):
            continue
        roots.append(walk(cat))

    tasks = []
    for node in roots:
        m = re.match(r"^(?:Т\s+)?(\d{1,2})\s*\.", node["name"])
        if not m or "Задания Д" in node["name"]:
            continue
        number = int(m.group(1))
        if not 1 <= number <= 27:
            continue
        leaves = []

        def collect(n: dict) -> None:
            kids = n["children"]
            if kids:
                for c in kids:
                    collect(c)
                return
            if n["id"] and (n["count"] or 0) > 0:
                leaves.append({"id": n["id"], "name": n["name"], "count": n["count"]})

        collect(node)
        # один и тот же id не качаем дважды
        uniq = []
        seen = set()
        for leaf in leaves:
            if leaf["id"] in seen:
                continue
            seen.add(leaf["id"])
            uniq.append(leaf)
        tasks.append(
            {
                "task": number,
                "title": re.sub(r"^(?:Т\s+)?\d{1,2}\s*\.\s*", "", node["name"]).strip(),
                "name": node["name"],
                "parent_id": node["id"],
                "leaves": uniq,
            }
        )
    tasks.sort(key=lambda t: t["task"])
    return tasks


def fetch_html(session: requests.Session, url: str) -> str:
    last = None
    for attempt in range(4):
        try:
            r = session.get(url, timeout=180)
            r.raise_for_status()
            return r.text
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 + attempt * 3)
    raise RuntimeError(f"{url}: {last}")


def parse_problems(html: str, category_id: str, category_name: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    problems = []
    for div in soup.select("div.prob_maindiv"):
        link = div.select_one("span.prob_nums a")
        pid = link.get_text(strip=True) if link else ""
        if not pid:
            continue
        condition, figs = condition_of(div)
        sol = div.select_one("div.solution") or div.select_one(f"#sol{pid}")
        answer_div = div.select_one("div.answer")
        problems.append(
            {
                "id": pid,
                "category_id": category_id,
                "category": category_name,
                "condition": condition,
                "solution": node_text(sol),
                "answer": clean_inline(answer_div.get_text(" ", strip=True)) if answer_div else "",
                "figure_urls": figs,
                "url": f"{BASE}/problem?id={pid}",
            }
        )
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default="", help="например 1,4,27. Пусто — все 1–27")
    args = parser.parse_args()
    wanted = {int(x) for x in args.tasks.split(",") if x.strip()} if args.tasks else set(range(1, 28))

    OUT.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT / "categories"
    raw_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (compatible; ege-rus/1.0)"

    catalog_html = fetch_html(session, f"{BASE}/prob_catalog")
    tasks = [t for t in parse_catalog(catalog_html) if t["task"] in wanted]
    (OUT / "catalog.json").write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"tasks {len(tasks)} categories {sum(len(t['leaves']) for t in tasks)}")

    for task in tasks:
        merged = []
        seen: set[str] = set()
        long_fallback = 0
        for leaf in task["leaves"]:
            path = raw_dir / f"c{leaf['id']}.json"
            if path.exists() and path.stat().st_size > 2:
                problems = json.loads(path.read_text(encoding="utf-8"))
                print(f"  task {task['task']} cat {leaf['id']} cached {len(problems)}")
            else:
                url = f"{BASE}/test?filter=all&category_id={leaf['id']}&print=true"
                html = fetch_html(session, url)
                problems = parse_problems(html, leaf["id"], leaf["name"])
                path.write_text(json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  task {task['task']} cat {leaf['id']} got {len(problems)} expected {leaf['count']}")
                time.sleep(0.4)
            for p in problems:
                if len(p.get("condition") or "") > 8000:
                    long_fallback += 1
                if p["id"] in seen:
                    continue
                seen.add(p["id"])
                merged.append(p)
        out = OUT / f"t{task['task']:02d}.json"
        out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        empty = sum(1 for p in merged if not p.get("condition"))
        print(
            f"task {task['task']:02d} {task['title'][:40]}: {len(merged)} unique, "
            f"empty {empty}, long {long_fallback} -> {out.name}"
        )


if __name__ == "__main__":
    main()
