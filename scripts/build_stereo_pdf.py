#!/usr/bin/env python3
"""PDF со всеми задачами №3 (стереометрия) и решениями — чтобы отдать в ChatGPT."""

from __future__ import annotations

import json
import re
import sys
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_vectors_pdf import P, SvgBox, humanize  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw_live"
FIGS = ROOT / "data" / "figures"
OUT = ROOT / "out" / "ege_task3_stereo.pdf"

# Порядок как в каталоге Решу ЕГЭ, задание 3.
GROUPS = [
    ("t3_c192", "Куб"),
    ("t3_c193", "Прямоугольный параллелепипед"),
    ("t3_c180", "Элементы составных многогранников"),
    ("t3_c148", "Площадь поверхности составного многогранника"),
    ("t3_c140", "Объём составного многогранника"),
    ("t3_c178", "Призма"),
    ("t3_c177", "Пирамида"),
    ("t3_c197", "Комбинации тел"),
    ("t3_c194", "Цилиндр"),
    ("t3_c144", "Конус"),
    ("t3_c151", "Шар"),
]

INK = HexColor("#1C2430")
ACCENT = HexColor("#0B3A82")
MUTED = HexColor("#5C6B80")


def build() -> None:
    styles = {
        "h1": ParagraphStyle("h1", fontName="DejaVuBold", fontSize=16, textColor=ACCENT, leading=20, alignment=TA_LEFT),
        "h2": ParagraphStyle("h2", fontName="DejaVuBold", fontSize=13, textColor=ACCENT, leading=16, spaceBefore=10, spaceAfter=4),
        "intro": ParagraphStyle("intro", fontName="DejaVu", fontSize=10, textColor=INK, leading=14, spaceAfter=4),
        "h": ParagraphStyle("h", fontName="DejaVuBold", fontSize=12, textColor=ACCENT, leading=15, spaceBefore=8, spaceAfter=3),
        "lab": ParagraphStyle("lab", fontName="DejaVuBold", fontSize=9, textColor=ACCENT, leading=12, spaceBefore=4),
        "body": ParagraphStyle("body", fontName="DejaVu", fontSize=10, textColor=INK, leading=13.5),
        "muted": ParagraphStyle("muted", fontName="DejaVu", fontSize=8, textColor=MUTED, leading=10),
    }

    loaded = []
    for stem, title in GROUPS:
        problems = json.loads((RAW / f"{stem}.json").read_text(encoding="utf-8"))
        loaded.append((stem, title, problems))
    total = sum(len(ps) for _, _, ps in loaded)

    story = [
        P("ЕГЭ, профиль. Задание №3. Стереометрия", styles["h1"]),
        Spacer(1, 3 * mm),
        P(
            f"Полный банк задания №3: {total} задач, 11 подтипов. "
            "У каждой задачи есть условие, чертёж (если он был на сайте), решение и ответ. "
            "Источник: Решу ЕГЭ, math-ege.sdamgia.ru.",
            styles["intro"],
        ),
        P(
            "Формулы записаны текстом: √( ), ^2, дробь (числитель)/(знаменатель). "
            "Подтипы идут в том же порядке, что в каталоге.",
            styles["intro"],
        ),
    ]
    for _, title, problems in loaded:
        story.append(P(f"{title} — {len(problems)} задач", styles["intro"]))

    drawn = 0
    failed = 0
    n = 0
    for stem, title, problems in loaded:
        story.append(P(title, styles["h2"]))
        story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceBefore=1, spaceAfter=4))
        for pr in problems:
            n += 1
            story.append(P(f"{n}. {title}. Задача {pr['id']}", styles["h"]))
            story.append(P(pr.get("url") or "", styles["muted"]))
            story.append(P("Условие", styles["lab"]))
            story.append(P(humanize(pr.get("condition") or ""), styles["body"]))
            fig = FIGS / stem / f"{pr['id']}.svg"
            if fig.exists():
                try:
                    story.append(Spacer(1, 2 * mm))
                    story.append(SvgBox(fig, max_w=150 * mm, max_h=85 * mm))
                    drawn += 1
                except Exception:
                    failed += 1
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
        canvas.drawString(16 * mm, 10 * mm, "Задание 3 · стереометрия · с решениями")
        canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, str(doc.page))
        canvas.restoreState()

    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title="ЕГЭ задание 3. Стереометрия, все задачи с решениями",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
    doc.build(story)
    print(f"PDF {OUT} problems={n} figures={drawn} failed={failed}")


if __name__ == "__main__":
    build()
