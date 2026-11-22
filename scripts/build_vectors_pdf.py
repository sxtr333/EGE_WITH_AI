#!/usr/bin/env python3
"""PDF со всеми задачами №2 (векторы) и решениями — чтобы отдать в ChatGPT."""

from __future__ import annotations

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics import renderPDF
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
    Flowable,
)
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw_live" / "t2_c182.json"
FIGS = ROOT / "data" / "figures" / "t2_c182"
OUT = ROOT / "out" / "ege_task2_vectors.pdf"

pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

INK = HexColor("#1C2430")
ACCENT = HexColor("#0B3A82")
MUTED = HexColor("#5C6B80")


def humanize(text: str) -> str:
    text = text.replace("⟦", " ").replace("⟧", " ")
    text = text.replace("rule_info", "").replace("rule_body", "")
    text = re.sub(r"\\overrightarrow\s*([A-Za-z]+)", r"\1⃗", text)
    text = re.sub(r"\\vec\s*([A-Za-z])", r"\1⃗", text)
    text = text.replace("\\times", "·")
    text = text.replace("\\widehat", "∠")
    text = text.replace("\\overset", "")
    text = text.replace("\\mathop", "")
    text = text.replace("левая круглая скобка", "(")
    text = text.replace("правая круглая скобка", ")")
    text = re.sub(
        r"корень из:\s*начало аргумента:\s*(.*?)\s*конец аргумента",
        r"√(\1)",
        text,
    )
    text = text.replace("начало аргумента:", "")
    text = text.replace("конец аргумента", "")
    frac = re.compile(
        r"дробь:\s*числитель:\s*((?:(?!дробь:).)*?)\s*знаменатель:\s*((?:(?!дробь:).)*?)\s*конец дроби",
        re.S,
    )
    for _ in range(6):
        new = frac.sub(r"(\1)/(\2)", text)
        if new == text:
            break
        text = new
    text = text.replace("в квадрате", "^2")
    text = re.sub(r"в степени\s*\(\s*([^)]+?)\s*\)", r"^(\1)", text)
    text = re.sub(r"косинус", "cos", text, flags=re.I)
    text = re.sub(r"синус", "sin", text, flags=re.I)
    text = text.replace("градусов", "°")
    text = text.replace(" плюс ", " + ")
    text = text.replace(" минус ", " − ")
    text = text.replace(" умножить на ", " · ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = text.replace("Решение .", "Решение.")
    return text.strip()


class SvgBox(Flowable):
    def __init__(self, path: Path, max_w: float = 150 * mm, max_h: float = 70 * mm):
        super().__init__()
        self.drawing = svg2rlg(str(path))
        scale = min(max_w / self.drawing.width, max_h / self.drawing.height)
        self.scale = scale
        self.drawWidth = self.drawing.width * scale
        self.drawHeight = self.drawing.height * scale

    def wrap(self, aw, ah):
        return self.drawWidth, self.drawHeight

    def draw(self):
        self.canv.saveState()
        self.canv.scale(self.scale, self.scale)
        renderPDF.draw(self.drawing, self.canv, 0, 0)
        self.canv.restoreState()


def P(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def build() -> None:
    problems = json.loads(DATA.read_text(encoding="utf-8"))
    styles = {
        "h1": ParagraphStyle("h1", fontName="DejaVuBold", fontSize=16, textColor=ACCENT, leading=20, alignment=TA_LEFT),
        "intro": ParagraphStyle("intro", fontName="DejaVu", fontSize=10, textColor=INK, leading=14, spaceAfter=6),
        "h": ParagraphStyle("h", fontName="DejaVuBold", fontSize=12, textColor=ACCENT, leading=15, spaceBefore=8, spaceAfter=3),
        "lab": ParagraphStyle("lab", fontName="DejaVuBold", fontSize=9, textColor=ACCENT, leading=12, spaceBefore=4),
        "body": ParagraphStyle("body", fontName="DejaVu", fontSize=10, textColor=INK, leading=13.5),
        "muted": ParagraphStyle("muted", fontName="DejaVu", fontSize=8, textColor=MUTED, leading=10),
    }

    story = [
        P("ЕГЭ, профиль. Задание №2. Векторы", styles["h1"]),
        Spacer(1, 3 * mm),
        P(
            f"Полный банк подтипа «Векторы и операции с ними»: {len(problems)} задач. "
            "У каждой задачи есть условие, чертёж (если он был на сайте), решение и ответ. "
            "Источник: Решу ЕГЭ, math-ege.sdamgia.ru, категория 182.",
            styles["intro"],
        ),
        P(
            "Формулы записаны текстом, как на сайте: √( ), ^2, дробь (числитель)/(знаменатель), "
            "стрелка над буквой — вектор.",
            styles["intro"],
        ),
    ]

    drawn = 0
    for i, pr in enumerate(problems, 1):
        story.append(P(f"{i}. Задача {pr['id']}", styles["h"]))
        story.append(P(pr.get("url") or "", styles["muted"]))
        story.append(P("Условие", styles["lab"]))
        story.append(P(humanize(pr.get("condition") or ""), styles["body"]))
        fig = FIGS / f"{pr['id']}.svg"
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
        canvas.drawString(16 * mm, 10 * mm, "Задание 2 · векторы · с решениями")
        canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, str(doc.page))
        canvas.restoreState()

    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title="ЕГЭ задание 2. Векторы, все задачи с решениями",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
    doc.build(story)
    print(f"PDF {OUT} problems={len(problems)} figures={drawn}")


if __name__ == "__main__":
    build()
