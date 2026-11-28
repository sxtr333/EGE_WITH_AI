#!/usr/bin/env python3
"""PDF со всеми задачами №5 и решениями."""

from __future__ import annotations

import json
import re
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Spacer,
)

from build_vectors_pdf import P, SvgBox, humanize

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "data" / "raw_live" / "t5_c185.json",
    ROOT / "data" / "raw_live" / "t5_c265.json",
)
FIGS = ROOT / "data" / "figures"
OUT = ROOT / "out" / "ege_task5_complex.pdf"

INK = HexColor("#1C2430")
ACCENT = HexColor("#0B3A82")
MUTED = HexColor("#5C6B80")


def build() -> None:
    problems = []
    for path in SOURCES:
        for item in json.loads(path.read_text(encoding="utf-8")):
            item["_file"] = path.stem
            problems.append(item)

    styles = {
        "h1": ParagraphStyle("h1", fontName="DejaVuBold", fontSize=16, textColor=ACCENT, leading=20, alignment=TA_LEFT),
        "intro": ParagraphStyle("intro", fontName="DejaVu", fontSize=10, textColor=INK, leading=14, spaceAfter=6),
        "h": ParagraphStyle("h", fontName="DejaVuBold", fontSize=12, textColor=ACCENT, leading=15, spaceBefore=8, spaceAfter=3),
        "lab": ParagraphStyle("lab", fontName="DejaVuBold", fontSize=9, textColor=ACCENT, leading=12, spaceBefore=4),
        "body": ParagraphStyle("body", fontName="DejaVu", fontSize=10, textColor=INK, leading=13.5),
        "muted": ParagraphStyle("muted", fontName="DejaVu", fontSize=8, textColor=MUTED, leading=10),
    }

    story = [
        P("ЕГЭ, профиль. Задание №5. Вероятности сложных событий", styles["h1"]),
        Spacer(1, 3 * mm),
        P(
            f"Полный банк: {len(problems)} задач. "
            "Категория 185 «Теоремы о вероятностях событий» — 65, "
            "категория 265 «Новые задания банка MathЕГЭ» — 5. "
            "У каждой задачи есть условие, рисунок (если он был на сайте), решение и ответ.",
            styles["intro"],
        ),
    ]

    drawn = 0
    for i, pr in enumerate(problems, 1):
        story.append(P(f"{i}. Задача {pr['id']}", styles["h"]))
        story.append(P(pr.get("url") or "", styles["muted"]))
        story.append(P("Условие", styles["lab"]))
        story.append(P(humanize(pr.get("condition") or ""), styles["body"]))
        fig = FIGS / pr["_file"] / f"{pr['id']}.svg"
        if fig.exists():
            story.append(Spacer(1, 2 * mm))
            story.append(SvgBox(fig))
            drawn += 1
        solution = humanize(pr.get("solution") or "")
        solution = re.sub(r"^Решение\.?\s*", "", solution)
        story.append(P("Решение", styles["lab"]))
        story.append(P(solution, styles["body"]))
        ans = humanize(pr.get("answer") or "")
        if ans and "ответ" not in solution.lower():
            story.append(P(ans if ans.lower().startswith("ответ") else "Ответ: " + ans, styles["lab"]))
        story.append(Spacer(1, 2 * mm))
        story.append(HRFlowable(width="100%", thickness=0.4, color=HexColor("#D5DDE8"), spaceBefore=2, spaceAfter=2))

    OUT.parent.mkdir(parents=True, exist_ok=True)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("DejaVu", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(16 * mm, 10 * mm, "Задание 5 · сложные события · с решениями")
        canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, str(doc.page))
        canvas.restoreState()

    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title="ЕГЭ задание 5. Вероятности сложных событий, все задачи с решениями",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
    doc.build(story)
    print(f"PDF {OUT} problems={len(problems)} figures={drawn}")


if __name__ == "__main__":
    build()
