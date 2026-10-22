# -*- coding: utf-8 -*-
"""Отрисовка структурных схем (контур управления, функциональная структура).

Зачем свой рендер, если есть drawio: схема должна собираться из кода рядом с
текстом отчёта и пересобираться одной командой (правка текста блока = правка
одной строки).

Единицы координат - типографские пункты (1 pt = 1/72 дюйма). Рисунок сразу
проектируется в натуральную величину: ширина ``CANVAS_W`` = 482 pt = 17 см,
то есть кегль на схеме равен кеглю в готовом отчёте (не надо гадать, будет ли
читаться после вставки в DOCX).

Пример:

    from labkit.schemes import Box, Link, render
    boxes = [Box("subj", "Субъект управления", x=240, y=250),
             Box("proc", "Процесс", x=240, y=100)]
    links = [Link("subj", "proc", "управляющее воздействие")]
    render(boxes, links, "out/scheme.png", height=330)
"""
import os
from dataclasses import dataclass, field

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (Circle, Ellipse, FancyArrowPatch,
                               FancyBboxPatch, Rectangle)

# 17 см в пунктах: ширина картинки в отчёте
CANVAS_W = 17.0 / 2.54 * 72.0
FONT = "Times New Roman"
DPI = 300

COLORS = {
    "ink": "#2c3e50",       # контур блоков
    "text": "#1b1b1b",
    "muted": "#6b7a8c",     # обратная связь
    "accent": "#1f4e79",    # информационные потоки
    "fill": "#ffffff",
    "fill_subj": "#e8eef6",  # субъект управления
    "fill_obj": "#eaf3ea",   # объект управления
    "fill_db": "#e6edf3",
    "fill_env": "#f7f4e8",
    "fill_ext": "#f2f2f2",
}


@dataclass
class Box:
    """Блок схемы.

    kind: ``box`` (процесс/модуль), ``db`` (цилиндр БД), ``cloud`` (внешняя
    среда), ``text`` (подпись без рамки, например вход/выход процесса).
    """
    id: str
    text: str
    x: float
    y: float
    w: float = 130.0
    h: float = 44.0
    kind: str = "box"
    title: str = ""        # имя элемента (рисуется жирным над текстом)
    fill: str = COLORS["fill"]
    edge: str = COLORS["ink"]
    fs: float = 7.4
    bold: bool = False
    lw: float = 1.0
    wrap: int = 0          # 0 = не переносить (в тексте уже есть \n)


@dataclass
class Link:
    """Стрелка между блоками.

    kind: ``flow`` (прямая связь), ``feedback`` (обратная связь, штриховая),
    ``data`` (информационный поток, синяя).
    via: промежуточные точки (ломаная), иначе стрелка прямая.
    s_side/t_side: к какой стороне блока крепиться (``l``/``r``/``t``/``b``),
    пусто = автоматически, по направлению стрелки.
    """
    src: str
    dst: str
    label: str = ""
    kind: str = "flow"
    via: tuple = ()
    label_at: float = 0.5   # доля длины ломаной, где ставить подпись
    label_dx: float = 0.0
    label_dy: float = 5.0
    s_side: str = ""
    t_side: str = ""
    s_off: float = 0.0      # сдвиг точки крепления вдоль стороны блока
    t_off: float = 0.0
    fs: float = 6.8
    lw: float = 1.0
    arrow: bool = True


# ---------------------------------------------------------------------------
# Геометрия
# ---------------------------------------------------------------------------
def _sides(box):
    return {
        "l": (box.x - box.w / 2, box.y),
        "r": (box.x + box.w / 2, box.y),
        "t": (box.x, box.y + box.h / 2),
        "b": (box.x, box.y - box.h / 2),
    }


def _anchor(box, toward, side=""):
    """Точка на границе блока в направлении точки ``toward``."""
    if side:
        return _sides(box)[side]
    cx, cy = box.x, box.y
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    hw, hh = box.w / 2, box.h / 2
    # пересечение луча из центра с прямоугольником
    tx = hw / abs(dx) if dx else float("inf")
    ty = hh / abs(dy) if dy else float("inf")
    t = min(tx, ty)
    return cx + dx * t, cy + dy * t


def _polyline_point(pts, frac):
    """Точка на ломаной по доле её длины."""
    segs = []
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        d = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        segs.append((a, b, d))
        total += d
    if total == 0:
        return pts[0]
    want = total * frac
    for a, b, d in segs:
        if want <= d or d == 0:
            k = 0.0 if d == 0 else want / d
            return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        want -= d
    return pts[-1]


# ---------------------------------------------------------------------------
# Отрисовка блоков
# ---------------------------------------------------------------------------
def _draw_db(ax, box):
    """Цилиндр БД: корпус + верхний эллипс."""
    hw, hh = box.w / 2, box.h / 2
    ry = min(box.h * 0.14, 9.0)
    left, right = box.x - hw, box.x + hw
    bottom, top = box.y - hh, box.y + hh
    ax.add_patch(Rectangle((left, bottom + ry), box.w, box.h - 2 * ry,
                           facecolor=box.fill, edgecolor="none", zorder=3))
    ax.plot([left, left], [bottom + ry, top - ry], color=box.edge,
            lw=box.lw, zorder=4)
    ax.plot([right, right], [bottom + ry, top - ry], color=box.edge,
            lw=box.lw, zorder=4)
    for yy in (top - ry, bottom + ry):
        ax.add_patch(Ellipse((box.x, yy), box.w, 2 * ry, facecolor=box.fill,
                             edgecolor=box.edge, lw=box.lw, zorder=4))
    ax.text(box.x, box.y - ry * 0.2, _label(box), ha="center", va="center",
            fontsize=box.fs, family=FONT, color=COLORS["text"],
            zorder=5, linespacing=1.15,
            fontweight="bold" if box.bold else "normal")


def _draw_cloud(ax, box):
    """Облако внешней среды: союз окружностей, нарисованный в два прохода."""
    hw, hh = box.w / 2, box.h / 2
    circles = [
        (-hw * 0.55, hh * 0.18, hh * 0.62), (-hw * 0.18, hh * 0.52, hh * 0.60),
        (hw * 0.22, hh * 0.46, hh * 0.52), (hw * 0.58, hh * 0.10, hh * 0.50),
        (-hw * 0.62, -hh * 0.30, hh * 0.50), (-hw * 0.15, -hh * 0.55, hh * 0.55),
        (hw * 0.30, -hh * 0.46, hh * 0.48), (hw * 0.62, -hh * 0.26, hh * 0.42),
    ]
    for dx, dy, r in circles:
        ax.add_patch(Circle((box.x + dx, box.y + dy), r, facecolor=box.fill,
                            edgecolor=box.edge, lw=box.lw, zorder=3))
    for dx, dy, r in circles:
        ax.add_patch(Circle((box.x + dx, box.y + dy), r * 0.965,
                            facecolor=box.fill, edgecolor="none", zorder=4))
    ax.text(box.x, box.y, _label(box), ha="center", va="center",
            fontsize=box.fs, family=FONT, color=COLORS["text"], zorder=6,
            linespacing=1.2)


def _label(box):
    if box.wrap:
        from labkit.schemes import wrap_text
        return wrap_text(box.text, box.wrap)
    return box.text


def wrap_text(text, width):
    """Перенос по словам: не больше ``width`` символов в строке."""
    out = []
    for raw in text.split("\n"):
        if len(raw) <= width:
            out.append(raw)
            continue
        cur = ""
        for word in raw.split():
            if not cur:
                cur = word
            elif len(cur) + 1 + len(word) <= width:
                cur += " " + word
            else:
                out.append(cur)
                cur = word
        if cur:
            out.append(cur)
    return "\n".join(out)


def _draw_box(ax, box):
    hw, hh = box.w / 2, box.h / 2
    ax.add_patch(FancyBboxPatch(
        (box.x - hw, box.y - hh), box.w, box.h,
        boxstyle="round,pad=0,rounding_size=4",
        facecolor=box.fill, edgecolor=box.edge, lw=box.lw, zorder=3))
    text = _label(box)
    if box.title:
        ax.text(box.x, box.y + hh - 11, box.title, ha="center", va="center",
                fontsize=box.fs + 0.4, family=FONT, color=COLORS["text"],
                zorder=4, fontweight="bold")
        ax.text(box.x, box.y - 6, text, ha="center", va="center",
                fontsize=box.fs, family=FONT, color=COLORS["text"],
                zorder=4, linespacing=1.2,
                fontweight="bold" if box.bold else "normal")
        return
    ax.text(box.x, box.y, text, ha="center", va="center",
            fontsize=box.fs, family=FONT, color=COLORS["text"], zorder=4,
            linespacing=1.2,
            fontweight="bold" if box.bold else "normal")


# ---------------------------------------------------------------------------
# Отрисовка связей
# ---------------------------------------------------------------------------
_LINK_STYLE = {
    "flow": dict(color=COLORS["ink"], linestyle="solid", lw=1.0),
    "feedback": dict(color=COLORS["muted"], linestyle=(0, (4.5, 2.5)), lw=1.0),
    "data": dict(color=COLORS["accent"], linestyle="solid", lw=1.0),
}


def _offset_anchor(pt, side, off):
    if not off:
        return pt
    if side in ("t", "b"):
        return pt[0] + off, pt[1]
    return pt[0], pt[1] + off


def _draw_link(ax, link, boxes):
    a, b = boxes[link.src], boxes[link.dst]
    via = list(link.via)
    first_target = via[0] if via else (b.x, b.y)
    last_source = via[-1] if via else (a.x, a.y)
    start = _offset_anchor(_anchor(a, first_target, link.s_side),
                           link.s_side, link.s_off)
    end = _offset_anchor(_anchor(b, last_source, link.t_side),
                         link.t_side, link.t_off)
    pts = [start] + via + [end]

    st = _LINK_STYLE.get(link.kind, _LINK_STYLE["flow"])
    color = st["color"]
    ls = st["linestyle"]
    lw = link.lw or st["lw"]

    for p, q in zip(pts[:-2], pts[1:-1]):
        ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=lw,
                linestyle=ls, zorder=2)
    if link.arrow:
        ax.add_patch(FancyArrowPatch(
            pts[-2], pts[-1], arrowstyle="-|>", mutation_scale=9,
            color=color, lw=lw, linestyle="solid", shrinkA=0, shrinkB=0,
            zorder=2))
    else:
        p, q = pts[-2], pts[-1]
        ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=lw,
                linestyle=ls, zorder=2)

    if link.label:
        px, py = _polyline_point(pts, link.label_at)
        ax.text(px + link.label_dx, py + link.label_dy, link.label,
                ha="center", va="bottom", fontsize=link.fs, family=FONT,
                color=color, zorder=7, linespacing=1.15,
                bbox=dict(boxstyle="round,pad=0.14", fc="white", ec="none",
                          alpha=0.92))


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------
def render(boxes, links, path_png, height=330.0, legend=None, width=None,
           svg=True, pad=2.0):
    """Рисует схему и сохраняет PNG (и SVG рядом).

    boxes/links - списки :class:`Box` и :class:`Link`; ``height`` - высота
    холста в пунктах; ``legend`` - список ``(подпись, kind)`` для легенды
    внизу слева.
    """
    canvas_w = width or CANVAS_W
    legend_h = 0.0
    if legend:
        legend_h = 14.0 + 11.0 * len(legend)
    total_h = height + legend_h

    fig = plt.figure(figsize=(canvas_w / 72.0, total_h / 72.0), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, canvas_w)
    ax.set_ylim(0, total_h)
    ax.set_aspect("equal")
    ax.axis("off")

    by_id = {b.id: b for b in boxes}
    for link in links:
        _draw_link(ax, link, by_id)

    for box in boxes:
        if box.kind == "text":
            ax.text(box.x, box.y, _label(box), ha="center", va="center",
                    fontsize=box.fs, family=FONT, color=COLORS["text"],
                    zorder=4, linespacing=1.2,
                    fontweight="bold" if box.bold else "normal")
        elif box.kind == "db":
            _draw_db(ax, box)
        elif box.kind == "cloud":
            _draw_cloud(ax, box)
        else:
            _draw_box(ax, box)

    if legend:
        y = 6.0
        for text, kind in reversed(legend):
            st = _LINK_STYLE.get(kind, _LINK_STYLE["flow"])
            ax.add_patch(FancyArrowPatch((8, y + 3.5), (34, y + 3.5),
                                         arrowstyle="-|>", mutation_scale=8,
                                         color=st["color"], lw=1.0,
                                         linestyle=st["linestyle"]))
            ax.text(40, y + 3.5, text, fontsize=6.8, family=FONT,
                    va="center", color=COLORS["text"])
            y += 11.0

    path_png = os.path.abspath(path_png)
    os.makedirs(os.path.dirname(path_png), exist_ok=True)
    fig.savefig(path_png, dpi=DPI, facecolor="white")
    out_svg = None
    if svg:
        out_svg = os.path.splitext(path_png)[0] + ".svg"
        fig.savefig(out_svg, facecolor="white")
    plt.close(fig)
    return path_png, out_svg
