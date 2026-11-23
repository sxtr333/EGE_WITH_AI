#!/usr/bin/env python3
"""Собрать по одному PDF на каждый тип заданий 1–27 ЕГЭ по русскому языку."""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Spacer,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "rus"
OUT = ROOT / "out" / "rus"

pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

INK = HexColor("#1C2430")
ACCENT = HexColor("#0B3A82")
MUTED = HexColor("#5C6B80")


def styles() -> dict:
    return {
        "h": ParagraphStyle("h", fontName="DejaVuBold", fontSize=16, textColor=ACCENT, leading=20, alignment=TA_LEFT),
        "sub": ParagraphStyle("sub", fontName="DejaVu", fontSize=9, textColor=MUTED, leading=12),
        "pid": ParagraphStyle("pid", fontName="DejaVuBold", fontSize=11, textColor=ACCENT, leading=14, spaceBefore=2),
        "lab": ParagraphStyle("lab", fontName="DejaVuBold", fontSize=9, textColor=INK, leading=12, spaceBefore=4),
        "body": ParagraphStyle("body", fontName="DejaVu", fontSize=9, textColor=INK, leading=12),
        "ans": ParagraphStyle("ans", fontName="DejaVuBold", fontSize=10, textColor=INK, leading=13),
    }


def para(text: str, style) -> Paragraph:
    text = text or ""
    text = escape(text)
    text = text.replace("\n", "<br/>")
    return Paragraph(text, style)


def build_one(task: dict, problems: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    st = styles()
    story = [
        para(f"ЕГЭ. Русский язык. Задание {task['task']}", st["h"]),
        Spacer(1, 2 * mm),
        para(task["title"], st["sub"]),
        para(f"Задач: {len(problems)}. Источник: Решу ЕГЭ, категории этого типа, без повторов по номеру.", st["sub"]),
        Spacer(1, 4 * mm),
    ]
    for i, p in enumerate(problems, 1):
        story.append(HRFlowable(width="100%", thickness=0.4, color=HexColor("#D5DDE8"), spaceBefore=2, spaceAfter=3))
        story.append(para(f"{i}. № {p['id']}  ·  {p.get('category') or ''}", st["pid"]))
        story.append(para("Условие", st["lab"]))
        story.append(para(p.get("condition") or "Условие на странице пустое.", st["body"]))
        if p.get("answer"):
            story.append(para("Ответ", st["lab"]))
            story.append(para(p["answer"], st["ans"]))
        if p.get("solution"):
            story.append(para("Решение", st["lab"]))
            story.append(para(p["solution"], st["body"]))
        if p.get("figure_urls"):
            story.append(para("На сайте у условия есть рисунок: " + ", ".join(p["figure_urls"]), st["sub"]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("DejaVu", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(16 * mm, 10 * mm, f"Русский язык · задание {task['task']} · {task['title'][:80]}")
        canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, str(doc.page))
        canvas.restoreState()

    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"ЕГЭ русский, задание {task['task']}",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="n", showBoundary=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
    doc.build(story)


def main() -> None:
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    lines = ["ЕГЭ по русскому языку. Отдельный PDF на каждый тип задания 1–27.", ""]
    for task in catalog:
        src = DATA / f"t{task['task']:02d}.json"
        problems = json.loads(src.read_text(encoding="utf-8"))
        path = OUT / f"t{task['task']:02d}.pdf"
        build_one(task, problems, path)
        lines.append(f"{task['task']:02d}. {task['title']} — {len(problems)} задач — {path.name}")
        print(f"{path.name} {len(problems)} {path.stat().st_size}")
    (OUT / "index.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT / "index.txt")


if __name__ == "__main__":
    main()
