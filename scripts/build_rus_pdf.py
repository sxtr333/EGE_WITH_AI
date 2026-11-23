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


def merge_all(catalog: list[dict], counts: dict[int, int]) -> Path:
    """Один PDF: обложка, затем задания 1–27, у каждого своя закладка."""
    from pypdf import PdfReader, PdfWriter

    st = styles()
    pieces = []
    for task in catalog:
        path = OUT / f"t{task['task']:02d}.pdf"
        reader = PdfReader(str(path))
        pieces.append((task, reader, len(reader.pages)))

    # Сначала считаем, с какой страницы начнётся каждый тип. Обложка — страница 1.
    starts = []
    page = 2
    for task, _reader, n_pages in pieces:
        starts.append(page)
        page += n_pages

    cover = OUT / "_cover.pdf"
    story = [
        para("ЕГЭ. Русский язык", st["h"]),
        Spacer(1, 2 * mm),
        para("Все задания 1–27 в одном файле. Закладка слева открывает нужный тип.", st["sub"]),
        Spacer(1, 4 * mm),
    ]
    for (task, _reader, n_pages), start in zip(pieces, starts):
        n = counts.get(task["task"], 0)
        story.append(
            para(
                f"{task['task']:02d}. {task['title']} — {n} задач, страница {start}",
                st["body"],
            )
        )
    doc = BaseDocTemplate(
        str(cover),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="ЕГЭ русский, задания 1–27",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="c", showBoundary=0)
    doc.addPageTemplates([PageTemplate(id="cover", frames=[frame])])
    doc.build(story)

    writer = PdfWriter()
    writer.add_page(PdfReader(str(cover)).pages[0])
    writer.add_outline_item(title="Содержание", page_number=0)
    for (task, reader, _n), start in zip(pieces, starts):
        for pdf_page in reader.pages:
            writer.add_page(pdf_page)
        writer.add_outline_item(title=f"{task['task']:02d}. {task['title']}", page_number=start - 1)
    writer.add_metadata({"/Title": "ЕГЭ. Русский язык. Задания 1–27"})

    out = OUT / "ege_russkij_1-27.pdf"
    with out.open("wb") as fh:
        writer.write(fh)
    cover.unlink(missing_ok=True)
    return out


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--merge-only", action="store_true", help="Склеить уже собранные t01–t27")
    args = parser.parse_args()

    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [
        "ЕГЭ по русскому языку. Все типы в одном файле: ege_russkij_1-27.pdf.",
        "Отдельный PDF на каждый тип тоже лежит рядом: t01.pdf … t27.pdf.",
        "",
    ]
    counts: dict[int, int] = {}
    for task in catalog:
        src = DATA / f"t{task['task']:02d}.json"
        problems = json.loads(src.read_text(encoding="utf-8"))
        counts[task["task"]] = len(problems)
        path = OUT / f"t{task['task']:02d}.pdf"
        if not args.merge_only:
            build_one(task, problems, path)
            print(f"{path.name} {len(problems)} {path.stat().st_size}")
        lines.append(f"{task['task']:02d}. {task['title']} — {len(problems)} задач — {path.name}")
    merged = merge_all(catalog, counts)
    lines.append("")
    lines.append(f"Общий файл: {merged.name}")
    (OUT / "index.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(merged, merged.stat().st_size)


if __name__ == "__main__":
    main()
