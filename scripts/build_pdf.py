#!/usr/bin/env python3
"""PDF-навигатор: схема слева, формулы справа (стиль как у ChatGPT, формулы из банка)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content.cards_1_2_3 import CARDS  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
pdfmetrics.registerFont(TTFont("DejaVu", FONT))
pdfmetrics.registerFont(TTFont("DejaVuBold", FONT_B))

BLUE = HexColor("#2F6FED")
BLUE_SOFT = HexColor("#DCE9FF")
INK = HexColor("#1A1A1A")
MUTED = HexColor("#555555")
LINE = HexColor("#C8D6F0")
BG = HexColor("#F7F9FC")
ACCENT = HexColor("#0B3A82")


def wrap_draw(c: canvas.Canvas, fig: str, x: float, y: float, w: float, h: float) -> None:
    c.saveState()
    c.setStrokeColor(BLUE)
    c.setFillColor(BLUE_SOFT)
    c.setLineWidth(1.6)
    cx, cy = x + w / 2, y + h / 2

    if fig == "right_triangle":
        pts = [x + 8, y + 10, x + w - 8, y + 10, x + 8, y + h - 12]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.drawPath(_poly(pts), fill=1, stroke=1)
        c.rect(x + 8, y + 10, 10, 10, stroke=1, fill=0)
        _label(c, "C", x + 4, y + h - 18)
        _label(c, "B", x + 2, y + 0)
        _label(c, "A", x + w - 14, y + 0)
        _label(c, "a", x - 2, cy - 2)
        _label(c, "b", cx - 4, y - 2)
        _label(c, "c", cx + 10, cy + 8)

    elif fig == "right_alt":
        pts = [x + 8, y + 10, x + w - 8, y + 10, x + 8, y + h - 12]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.drawPath(_poly(pts), fill=1, stroke=1)
        # height from C to AB roughly
        c.setDash(2, 2)
        c.line(x + 8, y + h - 12, x + w * 0.42, y + 10)
        c.setDash()
        _label(c, "C", x + 4, y + h - 18)
        _label(c, "H", x + w * 0.42 - 4, y - 2)
        _label(c, "A", x + w - 14, y + 0)
        _label(c, "B", x + 2, y + 0)

    elif fig == "isosceles":
        pts = [x + w / 2, y + h - 10, x + 10, y + 12, x + w - 10, y + 12]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.drawPath(_poly(pts), fill=1, stroke=1)
        c.setDash(2, 2)
        c.line(x + w / 2, y + h - 10, x + w / 2, y + 12)
        c.setDash()
        _label(c, "C", x + w / 2 - 4, y + h - 8)
        _label(c, "A", x + 4, y + 0)
        _label(c, "B", x + w - 12, y + 0)
        _label(c, "a", x + 18, cy + 6)
        _label(c, "a", x + w - 28, cy + 6)
        _label(c, "b", cx - 4, y - 2)

    elif fig == "triangle_area":
        pts = [x + w / 2, y + h - 10, x + 10, y + 12, x + w - 10, y + 12]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.drawPath(_poly(pts), fill=1, stroke=1)
        c.setDash(2, 2)
        c.line(x + w / 2, y + h - 10, x + w / 2, y + 12)
        c.setDash()
        _label(c, "C", x + w / 2 - 4, y + h - 8)
        _label(c, "A", x + 4, y + 0)
        _label(c, "B", x + w - 12, y + 0)
        _label(c, "a", x + 16, cy)
        _label(c, "b", x + w - 26, cy)
        _label(c, "h", x + w / 2 + 4, cy - 4)

    elif fig == "parallelogram":
        pts = [x + 18, y + 14, x + w - 8, y + 14, x + w - 22, y + h - 12, x + 4, y + h - 12]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.drawPath(_poly(pts), fill=1, stroke=1)
        c.setDash(2, 2)
        c.line(x + 4, y + h - 12, x + 4, y + 14)
        c.setDash()
        _label(c, "h", x - 2, cy)
        _label(c, "a", cx - 4, y + 2)

    elif fig == "rectangle":
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.rect(x + 10, y + 18, w - 22, h - 36, stroke=1, fill=1)
        c.line(x + 10, y + 18, x + w - 12, y + h - 18)
        _label(c, "a", cx - 4, y + 4)
        _label(c, "b", x + w - 10, cy)
        _label(c, "d", cx + 2, cy + 6)

    elif fig == "rhombus":
        pts = [cx, y + h - 10, x + w - 8, cy, cx, y + 10, x + 8, cy]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.drawPath(_poly(pts), fill=1, stroke=1)
        c.setDash(2, 2)
        c.line(cx, y + h - 10, cx, y + 10)
        c.line(x + 8, cy, x + w - 8, cy)
        c.setDash()
        _label(c, "d1", cx + 3, cy + 8)
        _label(c, "d2", cx - 8, y + 2)
        _label(c, "a", x + 14, cy + 12)

    elif fig == "square":
        side = min(w, h) * 0.62
        sx, sy = cx - side / 2, cy - side / 2
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.rect(sx, sy, side, side, stroke=1, fill=1)
        c.line(sx, sy, sx + side, sy + side)
        _label(c, "a", sx + side / 2 - 4, sy - 10)
        _label(c, "d", sx + side * 0.45, sy + side * 0.55)

    elif fig == "equilateral":
        pts = [cx, y + h - 8, x + 8, y + 14, x + w - 8, y + 14]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.drawPath(_poly(pts), fill=1, stroke=1)
        c.setDash(2, 2)
        c.line(cx, y + h - 8, cx, y + 14)
        c.setDash()
        _label(c, "60°", cx - 8, y + h - 22)
        _label(c, "a", cx - 4, y + 2)
        _label(c, "h", cx + 4, cy)

    elif fig == "quad":
        pts = [(x + 12, y + 16), (x + w - 10, y + 12), (x + w - 16, y + h - 14), (x + 18, y + h - 18)]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.drawPath(_poly(pts), fill=1, stroke=1)
        c.setDash(2, 2)
        c.line(pts[0][0], pts[0][1], pts[2][0], pts[2][1])
        c.line(pts[1][0], pts[1][1], pts[3][0], pts[3][1])
        c.setDash()
        _label(c, "d", cx, cy)

    elif fig == "algebra":
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.roundRect(x + 8, y + h * 0.55, w - 16, h * 0.32, 4, stroke=1, fill=1)
        c.roundRect(x + 8, y + 12, w - 16, h * 0.32, 4, stroke=1, fill=1)
        _label(c, "(a+b)²", x + 14, y + h * 0.62)
        _label(c, "√a·√b", x + 16, y + 18)

    elif fig == "hexagon":
        R = min(w, h) * 0.36
        pts = [
            (cx + R * math.cos(math.radians(i * 60)), cy + R * math.sin(math.radians(i * 60)))
            for i in range(6)
        ]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.drawPath(_poly(pts), fill=1, stroke=1)
        c.line(cx, cy, pts[0][0], pts[0][1])
        c.line(cx, cy, pts[1][0], pts[1][1])
        c.setFillColor(BLUE)
        c.circle(cx, cy, 2.2, stroke=0, fill=1)
        _label(c, "O", cx - 10, cy - 12)
        _label(c, "a", (pts[0][0] + pts[1][0]) / 2 + 2, (pts[0][1] + pts[1][1]) / 2)

    elif fig == "trapezoid":
        pts = [x + 22, y + h - 12, x + w - 22, y + h - 12, x + w - 8, y + 12, x + 8, y + 12]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.9))
        c.drawPath(_poly(pts), fill=1, stroke=1)
        c.setDash(2, 2)
        c.line(x + 22, y + h - 12, x + 22, y + 12)
        c.setDash()
        _label(c, "a", cx - 4, y + h - 8)
        _label(c, "b", cx - 4, y + 0)
        _label(c, "h", x + 10, cy)

    elif fig in {"circle_angles", "tangent_chord", "incircle", "circumcircle"}:
        r = min(w, h) * 0.36
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.55))
        c.circle(cx, cy, r, stroke=1, fill=1)
        if fig == "circle_angles":
            c.circle(cx, cy, 2.2, stroke=0, fill=1)
            c.setFillColor(BLUE)
            c.circle(cx, cy, 2.2, stroke=0, fill=1)
            c.setStrokeColor(BLUE)
            c.line(cx, cy, cx + r * 0.85, cy + r * 0.45)
            c.line(cx, cy, cx - r * 0.2, cy + r * 0.9)
            _label(c, "O", cx + 4, cy - 10)
        elif fig == "tangent_chord":
            c.line(x + 6, cy + r * 0.7, x + w - 6, cy + r * 0.7)
            c.line(cx, cy, cx, cy + r * 0.7)
            _label(c, "R⊥", cx + 4, cy + 8)
        elif fig == "incircle":
            pts = [x + w / 2, y + h - 6, x + 8, y + 10, x + w - 8, y + 10]
            c.setStrokeColor(BLUE)
            c.drawPath(_poly(pts), fill=0, stroke=1)
        else:
            pts = [x + w / 2, y + h - 8, x + 10, y + 14, x + w - 10, y + 14]
            c.drawPath(_poly(pts), fill=0, stroke=1)
            _label(c, "R", cx + 6, cy)

    elif fig == "vector":
        c.setStrokeColor(BLUE)
        c.setLineWidth(2)
        c.line(x + 16, y + 18, x + w - 14, y + h - 16)
        _arrow(c, x + w - 14, y + h - 16, x + w - 28, y + h - 28)
        _label(c, "a⃗", cx, cy + 8)
        c.setLineWidth(1)
        c.line(x + 16, y + 18, x + w - 20, y + 18)
        c.line(x + 16, y + 18, x + 16, y + h - 20)
        _label(c, "x", x + w - 18, y + 6)
        _label(c, "y", x + 4, y + h - 18)

    elif fig == "cube":
        _box3d(c, x + 12, y + 16, w - 24, h - 28, 14)

    elif fig == "box":
        _box3d(c, x + 10, y + 14, w - 22, h - 26, 18)
        _label(c, "a", x + 20, y + 4)
        _label(c, "b", x + w - 28, y + 18)
        _label(c, "c", x + 2, cy)

    elif fig == "prism":
        _box3d(c, x + 14, y + 14, w - 28, h - 24, 12)
        _label(c, "H", x + 2, cy)

    elif fig == "oblique":
        x0, y0 = x + 14, y + 16
        bw, bh, dx, shear = w - 40, h - 36, 12, 16
        base = [(x0, y0), (x0 + bw, y0), (x0 + bw + dx, y0 + 8), (x0 + dx, y0 + 8)]
        top = [(p[0] + shear, p[1] + bh) for p in base]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.85))
        c.drawPath(_poly([base[0], base[1], top[1], top[0]]), fill=1, stroke=1)
        c.drawPath(_poly(top), fill=1, stroke=1)
        c.drawPath(_poly([base[1], base[2], top[2], top[1]]), fill=1, stroke=1)
        c.setDash(2, 2)
        c.line(base[0][0], base[0][1], top[0][0], top[0][1])
        c.line(base[3][0], base[3][1], top[3][0], top[3][1])
        c.setDash()
        _label(c, "L", x0 - 2, y0 + bh * 0.45)
        _label(c, "α", x0 + 10, y0 + 2)

    elif fig == "pyramid":
        apex = (cx, y + h - 8)
        base = [(x + 12, y + 16), (x + w - 12, y + 16), (x + w - 22, y + 34), (x + 22, y + 34)]
        c.setFillColor(Color(0.82, 0.90, 1, alpha=0.7))
        c.drawPath(_poly([apex, base[0], base[1]]), fill=1, stroke=1)
        c.drawPath(_poly(base), fill=0, stroke=1)
        c.setDash(2, 2)
        c.line(apex[0], apex[1], cx, y + 25)
        c.setDash()
        _label(c, "S", apex[0] - 4, apex[1] + 2)
        _label(c, "H", cx + 4, cy)

    elif fig == "cylinder":
        c.ellipse(x + 18, y + h - 28, x + w - 18, y + h - 10, stroke=1, fill=1)
        c.ellipse(x + 18, y + 10, x + w - 18, y + 28, stroke=1, fill=1)
        c.line(x + 18, y + h - 19, x + 18, y + 19)
        c.line(x + w - 18, y + h - 19, x + w - 18, y + 19)
        _label(c, "H", x + 2, cy)
        _label(c, "r", cx - 4, y + h - 8)

    elif fig == "cone":
        c.ellipse(x + 16, y + 12, x + w - 16, y + 30, stroke=1, fill=1)
        c.line(cx, y + h - 10, x + 16, y + 21)
        c.line(cx, y + h - 10, x + w - 16, y + 21)
        _label(c, "l", x + w - 22, cy + 8)
        _label(c, "H", cx + 4, cy)

    elif fig == "sphere":
        c.circle(cx, cy, min(w, h) * 0.34, stroke=1, fill=1)
        c.ellipse(cx - min(w, h) * 0.34, cy - 7, cx + min(w, h) * 0.34, cy + 7, stroke=1, fill=0)
        _label(c, "R", cx + 8, cy + 8)

    elif fig == "composite":
        _box3d(c, x + 8, y + 12, w * 0.55, h * 0.45, 10)
        _box3d(c, x + w * 0.38, y + h * 0.38, w * 0.45, h * 0.42, 10)

    elif fig == "combo":
        c.ellipse(x + 20, y + h - 26, x + w - 20, y + h - 10, stroke=1, fill=0)
        c.ellipse(x + 20, y + 12, x + w - 20, y + 28, stroke=1, fill=0)
        c.line(x + 20, y + h - 18, x + 20, y + 20)
        c.line(x + w - 20, y + h - 18, x + w - 20, y + 20)
        c.circle(cx, cy, min(w, h) * 0.22, stroke=1, fill=1)

    else:
        c.rect(x + 8, y + 8, w - 16, h - 16, stroke=1, fill=1)

    c.restoreState()


def _poly(pts):
    """pts: [(x,y), ...] or flat [x,y,x,y,...]."""
    from reportlab.pdfgen.pathobject import PDFPathObject

    if pts and not isinstance(pts[0], (tuple, list)):
        pts = list(zip(pts[0::2], pts[1::2]))
    path = PDFPathObject()
    path.moveTo(pts[0][0], pts[0][1])
    for pt in pts[1:]:
        path.lineTo(pt[0], pt[1])
    path.close()
    return path


def _label(c, text, x, y):
    c.setFillColor(ACCENT)
    c.setFont("DejaVu", 8)
    c.drawString(x, y, text)


def _arrow(c, x, y, xb, yb):
    c.line(xb, yb, x, y)
    c.line(x, y, x - 6, y - 2)
    c.line(x, y, x - 2, y - 6)


def _box3d(c, x, y, w, h, d):
    front = [x, y, x + w, y, x + w, y + h, x, y + h]
    c.setFillColor(Color(0.82, 0.90, 1, alpha=0.85))
    c.drawPath(_poly([(front[0], front[1]), (front[2], front[3]), (front[4], front[5]), (front[6], front[7])]), fill=1, stroke=1)
    top = [(x, y + h), (x + d, y + h + d * 0.55), (x + w + d, y + h + d * 0.55), (x + w, y + h)]
    c.drawPath(_poly(top), fill=1, stroke=1)
    side = [(x + w, y), (x + w + d, y + d * 0.55), (x + w + d, y + h + d * 0.55), (x + w, y + h)]
    c.drawPath(_poly(side), fill=1, stroke=1)


def _formula_items(card: dict) -> list[dict]:
    """Поддержка старого списка строк и нового {f, if}."""
    items = []
    for f in card["formulas"]:
        if isinstance(f, dict):
            items.append({"f": f.get("f", ""), "if": f.get("if", "")})
        else:
            items.append({"f": str(f), "if": ""})
    return items


def _card_story(card: dict):
    styles = {
        "title": ParagraphStyle("t", fontName="DejaVuBold", fontSize=10, textColor=ACCENT, leading=12),
        "body": ParagraphStyle("b", fontName="DejaVu", fontSize=7.8, textColor=INK, leading=9.8),
        "lab": ParagraphStyle("l", fontName="DejaVuBold", fontSize=8, textColor=BLUE, leading=10),
        "formula": ParagraphStyle("ff", fontName="DejaVuBold", fontSize=8, textColor=ACCENT, leading=10),
        "iff": ParagraphStyle("iff", fontName="DejaVu", fontSize=7.3, textColor=MUTED, leading=9.2),
        "muted": ParagraphStyle("m", fontName="DejaVu", fontSize=7.2, textColor=MUTED, leading=9),
    }
    story = [
        Paragraph(card["title"], styles["title"]),
        Paragraph(f"Подтип: {card.get('subtype','')}", styles["muted"]),
        Paragraph("<b>Тема карточки:</b> " + card["when"], styles["body"]),
        Paragraph("<b>Какую формулу брать:</b>", styles["lab"]),
    ]
    for item in _formula_items(card):
        if item["if"]:
            story.append(Paragraph(f"ЕСЛИ: {item['if']}", styles["iff"]))
            story.append(Paragraph(f"→ {item['f']}", styles["formula"]))
        else:
            story.append(Paragraph(f"→ {item['f']}", styles["formula"]))
    story.extend(
        [
            Paragraph("<b>Буквы:</b> " + card["letters"], styles["body"]),
            Paragraph("<b>Ход:</b> " + card["steps"], styles["body"]),
            Paragraph("<b>Ловушка:</b> " + card["trap"], styles["muted"]),
        ]
    )
    return story


def estimate_card_h(card: dict, text_w: float) -> float:
    """Высота с запасом под пары ЕСЛИ/формула."""
    items = _formula_items(card)
    n_lines = 7
    for item in items:
        n_lines += 2 if item["if"] else 1
        n_lines += max(0, (len(item["if"]) - 55) // 55)
        n_lines += max(0, (len(item["f"]) - 55) // 55)
    n_lines += max(1, (len(card["when"]) + 55) // 55)
    n_lines += max(1, (len(card["steps"]) + 55) // 55)
    n_lines += max(1, (len(card["trap"]) + 55) // 55)
    return max(62 * mm, min(200 * mm, 16 * mm + n_lines * 3.55 * mm))


def draw_card(c: canvas.Canvas, card: dict, x: float, y: float, w: float, h: float) -> None:
    c.saveState()
    # clip everything inside card
    p = c.beginPath()
    p.roundRect(x, y, w, h, 6)
    c.clipPath(p, stroke=0)

    c.setFillColor(white)
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)

    fig_w = 40 * mm
    pad = 3.5 * mm
    wrap_draw(c, card["figure"], x + pad, y + pad, fig_w - pad, h - 2 * pad)

    c.setStrokeColor(LINE)
    c.line(x + fig_w, y + 3 * mm, x + fig_w, y + h - 3 * mm)

    tx = x + fig_w + 3 * mm
    tw = w - fig_w - 6 * mm
    frame = Frame(
        tx,
        y + 2 * mm,
        tw,
        h - 4 * mm,
        showBoundary=0,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    frame.addFromList(_card_story(card), c)
    c.restoreState()


def build(out: Path) -> None:
    c = canvas.Canvas(str(out), pagesize=A4)
    W, H = A4
    margin = 14 * mm

    # cover
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    _nav(c)
    c.bookmarkPage("toc", fit="XYZ", top=H - 20 * mm, zoom=None)
    c.addOutlineEntry("Оглавление", "toc", 0, 0)
    c.setFillColor(ACCENT)
    c.setFont("DejaVuBold", 22)
    c.drawString(margin, H - 35 * mm, "ЕГЭ · Навигатор формул")
    c.setFont("DejaVu", 12)
    c.setFillColor(INK)
    c.drawString(margin, H - 45 * mm, "№1 Планиметрия · №2 Векторы · №3 Стереометрия")
    c.setFont("DejaVu", 10)
    lines = [
        "Как пользоваться:",
        "1) Открыл задачу на Решу ЕГЭ",
        "2) Узнал подтип (прямоугольный / трапеция / цилиндр…)",
        "3) Нажми название в оглавлении или кнопку сверху",
        "4) Читаешь ЕСЛИ … → берёшь формулу",
        "5) Подставил — решил",
        "",
        "У каждой формулы своё ЕСЛИ: при каких данных её брать.",
        "Формулы из всех 643 решений банка Решу ЕГЭ (№1–3).",
    ]
    yy = H - 60 * mm
    for line in lines:
        c.drawString(margin, yy, line)
        yy -= 6 * mm

    # TOC — каждая фигура отдельной строкой
    c.setFont("DejaVuBold", 11)
    c.drawString(margin, yy - 2 * mm, "Оглавление — нажми название:")
    yy -= 8 * mm
    c.setFont("DejaVu", 8)
    col_x = [margin, margin + 92 * mm]
    col = 0
    row_y = yy
    for i, card in enumerate(CARDS):
        title = card["title"]
        c.setFillColor(ACCENT)
        c.drawString(col_x[col], row_y, title)
        tw = c.stringWidth(title, "DejaVu", 8)
        c.linkRect(
            title,
            f"card-{i}",
            (col_x[col], row_y - 1 * mm, col_x[col] + tw, row_y + 3.2 * mm),
            relative=0,
            thickness=0,
        )
        if col == 0:
            col = 1
        else:
            col = 0
            row_y -= 4.2 * mm
        if row_y < 18 * mm:
            break
    _footer(c, 1)
    c.showPage()

    page = 2
    top = H - 18 * mm
    y = top
    _nav(c)
    current_section = None
    outlined = set()
    gap = 3.5 * mm
    text_w = W - 2 * margin - 46 * mm

    for i, card in enumerate(CARDS):
        card_h = estimate_card_h(card, text_w)
        header = 0
        if card["section"] != current_section:
            header = 16 * mm if card.get("section_note") else 12 * mm
        if y - card_h - header < margin + 10 * mm:
            _footer(c, page)
            c.showPage()
            page += 1
            _nav(c)
            y = top
            current_section = None
            header = 16 * mm if card.get("section_note") else 12 * mm

        if card["section"] != current_section:
            current_section = card["section"]
            if card["section"] not in outlined:
                c.bookmarkPage(f"sec-{i}", fit="XYZ", top=y, zoom=None)
                c.addOutlineEntry(card["section"], f"sec-{i}", 0, 0)
                outlined.add(card["section"])
            c.setFillColor(ACCENT)
            c.setFont("DejaVuBold", 14)
            c.drawString(margin, y - 6 * mm, current_section)
            y -= 10 * mm
            if card.get("section_note"):
                c.setFillColor(MUTED)
                c.setFont("DejaVu", 8.5)
                c.drawString(margin, y, card["section_note"][:110])
                y -= 6 * mm

        c.bookmarkPage(f"card-{i}", fit="XYZ", top=y, zoom=None)
        c.addOutlineEntry(card["title"], f"card-{i}", 1, 0)
        draw_card(c, card, margin, y - card_h, W - 2 * margin, card_h)
        y -= card_h + gap

    _footer(c, page)
    c.save()
    print(f"PDF: {out}  pages~{page}  cards={len(CARDS)}")


def _nav_targets():
    """Кнопки сверху: подпись и ключ закладки первой карточки раздела."""
    wanted = (
        ("Как посчитать", "Счёт"),
        ("№1. Планиметрия", "№1"),
        ("№2. Векторы", "№2"),
        ("№3. Стереометрия", "№3"),
    )
    first = {}
    for i, card in enumerate(CARDS):
        first.setdefault(card["section"], f"card-{i}")
    by_title = {}
    for i, card in enumerate(CARDS):
        by_title.setdefault(card["title"], f"card-{i}")
    items = [("Оглавление", "toc")]
    for section, label in wanted:
        if section in first:
            items.append((label, first[section]))
    if "Полное квадратное уравнение" in by_title:
        items.append(("ax²", by_title["Полное квадратное уравнение"]))
    if "Вписано · пирамида, конус, основание" in by_title:
        items.append(("Впис", by_title["Вписано · пирамида, конус, основание"]))
    return items


def _nav(c):
    """Полоска кнопок. Ссылки ведут на закладки, их можно объявить позже."""
    W, H = A4
    c.saveState()
    c.setFillColor(HexColor("#E7EEF9"))
    c.rect(0, H - 12 * mm, W, 12 * mm, stroke=0, fill=1)
    x = 8 * mm
    base = H - 9.2 * mm
    c.setFont("DejaVu", 8)
    for label, key in _nav_targets():
        width = c.stringWidth(label, "DejaVu", 8) + 7 * mm
        c.setFillColor(ACCENT)
        c.roundRect(x, base, width, 6 * mm, 2, stroke=0, fill=1)
        c.setFillColor(white)
        c.drawString(x + 3.5 * mm, base + 1.7 * mm, label)
        c.linkRect(
            label,
            key,
            (x, base, x + width, base + 6 * mm),
            relative=0,
            thickness=0,
        )
        x += width + 2 * mm
    c.restoreState()


def _footer(c, page):
    W, H = A4
    c.setFillColor(MUTED)
    c.setFont("DejaVu", 8)
    c.drawString(14 * mm, 8 * mm, "ЕГЭ · навигатор формул · из решений Решу ЕГЭ")
    c.drawRightString(W - 14 * mm, 8 * mm, str(page))


if __name__ == "__main__":
    out = ROOT / "out" / "ege_navigator_1_2_3.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    build(out)
