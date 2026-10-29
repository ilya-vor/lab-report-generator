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
from matplotlib.path import Path
from matplotlib.patches import (Circle, Ellipse, FancyArrowPatch,
                               FancyBboxPatch, PathPatch, Rectangle)

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
    label_ha: str = "center"  # прижатие подписи: left/center/right
    label_va: str = "bottom"
    fs: float = 6.8
    lw: float = 1.0
    arrow: bool = True
    # Наконечник: ``arrow`` (стрелка), ``triangle`` (пустой треугольник,
    # обобщение UML), ``diamond``/``diamond_open`` (агрегация и композиция),
    # ``none`` (линия без наконечника). Пусто = ``arrow``.
    head: str = ""


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


def _cloud_circles(box):
    """Набор окружностей, из которых собирается облако.

    Внутренние окружности закрывают полость в центре: иначе объединение
    даёт «дырку» прямо под текстом.
    """
    hw, hh = box.w / 2, box.h / 2
    rel = [
        (-hw * 0.55, hh * 0.18, hh * 0.62), (-hw * 0.18, hh * 0.52, hh * 0.60),
        (hw * 0.22, hh * 0.46, hh * 0.52), (hw * 0.58, hh * 0.10, hh * 0.50),
        (-hw * 0.62, -hh * 0.30, hh * 0.50), (-hw * 0.15, -hh * 0.55, hh * 0.55),
        (hw * 0.30, -hh * 0.46, hh * 0.48), (hw * 0.62, -hh * 0.26, hh * 0.42),
        (0.0, hh * 0.16, hh * 0.56), (0.0, -hh * 0.22, hh * 0.56),
    ]
    return [(box.x + dx, box.y + dy, r) for dx, dy, r in rel]


def _draw_cloud(ax, box):
    """Облако внешней среды: сплошная заливка и один внешний контур.

    Облако - объединение окружностей. Если рисовать окружности по
    отдельности, внутренние дуги просвечивают через текст, а контур по
    изолинии поля расстояний рвётся на плоских участках. Поэтому
    объединение считается через shapely, а при его отсутствии работает
    запасной вариант по изолинии.
    """
    circles = _cloud_circles(box)
    try:
        from shapely.geometry import Point
        from shapely.ops import unary_union
        merged = unary_union([Point(cx, cy).buffer(r, quad_segs=64)
                              for cx, cy, r in circles])
        polys = [merged] if merged.geom_type == "Polygon" else list(merged.geoms)
        verts, codes = [], []
        for poly in polys:
            for ring in [poly.exterior] + list(poly.interiors):
                pts = list(ring.coords)
                verts.extend(pts)
                codes.extend([Path.MOVETO] + [Path.LINETO] * (len(pts) - 2)
                             + [Path.CLOSEPOLY])
        ax.add_patch(PathPatch(Path(verts, codes), facecolor=box.fill,
                               edgecolor=box.edge, lw=box.lw,
                               joinstyle="round", zorder=3))
    except ImportError:  # pragma: no cover - запасной путь без shapely
        import numpy as np

        hw, hh = box.w / 2, box.h / 2
        xs = np.linspace(box.x - hw - 4, box.x + hw + 4, 900)
        ys = np.linspace(box.y - hh - 4, box.y + hh + 4, 560)
        gx, gy = np.meshgrid(xs, ys)
        dist = np.stack([np.hypot(gx - cx, gy - cy) - r
                         for cx, cy, r in circles])
        low = dist.min(axis=0)
        k = 20.0
        field = low - np.log(np.exp(-k * (dist - low)).sum(axis=0)) / k
        ax.contourf(gx, gy, field, levels=[-1e6, 0.5], colors=[box.fill],
                    zorder=3)
        ax.contour(gx, gy, field, levels=[0.2], colors=[box.edge],
                   linewidths=box.lw, zorder=4)

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


def _draw_head(ax, p, q, head, color, lw):
    """Наконечник UML-связи в точке ``q`` (линия идёт из ``p``)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    dist = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / dist, dy / dist
    if head == "triangle":
        ax.add_patch(FancyArrowPatch(
            p, q, arrowstyle="-|>", mutation_scale=10, facecolor="white",
            edgecolor=color, lw=lw, shrinkA=0, shrinkB=0, zorder=3))
        return
    # ромб рисуется маркером, поэтому сдвигается внутрь линии на полразмера
    size = 5.6
    cx, cy = q[0] - ux * size * 0.75, q[1] - uy * size * 0.75
    fc = color if head == "diamond" else "white"
    ax.plot([cx], [cy], marker="D", markersize=size,
            markerfacecolor=fc, markeredgecolor=color, markeredgewidth=lw,
            zorder=3)


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
    head = link.head or ("arrow" if link.arrow else "none")
    p, q = pts[-2], pts[-1]
    if head in ("diamond", "diamond_open"):
        ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=lw,
                linestyle=ls, zorder=2)
        _draw_head(ax, p, q, head, color, lw)
    elif head == "triangle":
        ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=lw,
                linestyle=ls, zorder=2)
        _draw_head(ax, p, q, head, color, lw)
    elif head == "arrow":
        ax.add_patch(FancyArrowPatch(
            p, q, arrowstyle="-|>", mutation_scale=9,
            color=color, lw=lw, linestyle="solid", shrinkA=0, shrinkB=0,
            zorder=2))
    else:
        ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=lw,
                linestyle=ls, zorder=2)

    if link.label:
        px, py = _polyline_point(pts, link.label_at)
        ax.text(px + link.label_dx, py + link.label_dy, link.label,
                ha=link.label_ha, va=link.label_va, fontsize=link.fs, family=FONT,
                color=color, zorder=7, linespacing=1.15,
                bbox=dict(boxstyle="round,pad=0.14", fc="white", ec="none",
                          alpha=0.92))


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------
@dataclass
class UmlClass:
    """Класс UML-диаграммы: имя, стереотип, атрибуты.

    Высота блока считается по числу атрибутов, поэтому ``y`` задаёт центр
    блока, а совпадение с другими блоками можно проверять по сетке.
    """
    id: str
    name: str
    attrs: tuple = ()
    x: float = 0.0
    y: float = 0.0
    w: float = 104.0
    code: str = ""        # латинское имя класса (курсивом под названием)
    fs: float = 6.2
    fill: str = COLORS["fill"]


def _uml_box(cls, header_h, line_h):
    head = header_h + (9.0 if cls.code else 0.0)
    h = head + max(len(cls.attrs), 1) * line_h + 4.0
    return Box(cls.id, "", cls.x, cls.y, cls.w, h)


def _draw_uml_class(ax, box, cls, header_h, line_h):
    hw, hh = box.w / 2, box.h / 2
    ax.add_patch(FancyBboxPatch(
        (box.x - hw, box.y - hh), box.w, box.h,
        boxstyle="round,pad=0,rounding_size=2",
        facecolor=cls.fill, edgecolor=COLORS["ink"], lw=1.0, zorder=3))
    head_h = header_h + (9.0 if cls.code else 0.0)
    sep = box.y + hh - head_h
    ax.plot([box.x - hw, box.x + hw], [sep, sep], color=COLORS["ink"],
            lw=0.8, zorder=4)
    if cls.code:
        ax.text(box.x, sep + header_h / 2 + 4.0, cls.name, ha="center",
                va="center", fontsize=cls.fs + 0.8, family=FONT,
                fontweight="bold", color=COLORS["text"], zorder=4)
        ax.text(box.x, sep + header_h / 2 - 4.6, cls.code, ha="center",
                va="center", fontsize=cls.fs - 0.4, family=FONT,
                style="italic", color=COLORS["muted"], zorder=4)
    else:
        ax.text(box.x, sep + header_h / 2, cls.name, ha="center",
                va="center", fontsize=cls.fs + 0.8, family=FONT,
                fontweight="bold", color=COLORS["text"], zorder=4)
    for i, attr in enumerate(cls.attrs):
        yy = sep - line_h / 2 - 1.0 - i * line_h
        ax.text(box.x - hw + 4.0, yy, attr, ha="left", va="center",
                fontsize=cls.fs, family=FONT, color=COLORS["text"], zorder=4)


def render_classes(classes, links, path_png, height=330.0, width=None,
                   svg=True, header_h=14.0, line_h=9.6):
    """Рисует UML-диаграмму классов (онтологию в нотации UML).

    ``classes`` - список :class:`UmlClass`, ``links`` - :class:`Link` между
    ними; наконечники задаются полем ``head`` (``triangle`` - обобщение,
    ``diamond``/``diamond_open`` - композиция и агрегация). Высота блока
    считается по числу атрибутов, поэтому ``y`` - центр блока.
    """
    canvas_w = width or CANVAS_W
    boxes = [_uml_box(c, header_h, line_h) for c in classes]
    by_id = {b.id: b for b in boxes}

    fig = plt.figure(figsize=(canvas_w / 72.0, height / 72.0), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, canvas_w)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    ax.axis("off")

    for link in links:
        _draw_link(ax, link, by_id)
    for cls, box in zip(classes, boxes):
        _draw_uml_class(ax, box, cls, header_h, line_h)

    path_png = os.path.abspath(path_png)
    os.makedirs(os.path.dirname(path_png), exist_ok=True)
    fig.savefig(path_png, dpi=DPI, facecolor="white")
    out_svg = None
    if svg:
        out_svg = os.path.splitext(path_png)[0] + ".svg"
        fig.savefig(out_svg, facecolor="white")
    plt.close(fig)
    return path_png, out_svg


def render_ishikawa(effect, branches, path_png, width=None, height=212.0,
                    svg=True, head_w=76.0, head_h=58.0,
                    fs_cause=7.0, fs_cat=8.6, fs_effect=8.0,
                    dx=32.0, dy=76.0, text_w=52.0):
    """Рисует диаграмму Исикавы («рыбий скелет») с подветвями.

    ``effect`` - следствие в «голове»; ``branches`` - список
    ``(категория, частные причины)``, где частные причины заданы списком
    строк (или одной строкой). Кости верхнего уровня чередуются сверху и
    снизу от «позвоночника», частные причины рисуются короткими
    горизонтальными штрихами вдоль кости.

    Пример:

        render_ishikawa("Задержка 4-8 ч",
                        [("Персонал", ["один сотрудник", "нет резерва"]),
                         ("Технологии", ["нет онлайн-детекции"])],
                        "out/ishikawa.png")
    """
    canvas_w = width or CANVAS_W
    fig = plt.figure(figsize=(canvas_w / 72.0, height / 72.0), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, canvas_w)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    ax.axis("off")

    spine_y = height / 2.0
    head_cx = canvas_w - head_w / 2.0 - 2.0
    spine_x0 = 24.0
    spine_x1 = head_cx - head_w / 2.0

    n = len(branches)
    seg = (spine_x1 - spine_x0 - 34.0) / max(n, 1)

    # «Голова»: следствие
    ax.add_patch(FancyBboxPatch(
        (head_cx - head_w / 2, spine_y - head_h / 2), head_w, head_h,
        boxstyle="round,pad=0,rounding_size=4",
        facecolor=COLORS["fill_env"], edgecolor=COLORS["ink"], lw=1.2,
        zorder=5))
    ax.text(head_cx, spine_y, wrap_text(effect, max(10, int((head_w - 8) / (0.5 * fs_effect)))),
            ha="center", va="center",
            fontsize=fs_effect, family=FONT, fontweight="bold",
            color=COLORS["text"], zorder=6, linespacing=1.3)

    # «Позвоночник» со стрелкой в голову
    ax.add_patch(FancyArrowPatch((spine_x0, spine_y), (spine_x1 - 1, spine_y),
                                 arrowstyle="-|>", mutation_scale=10,
                                 color=COLORS["ink"], lw=1.5, zorder=2))

    for i, (cat, causes) in enumerate(branches):
        if isinstance(causes, str):
            causes = [causes]
        above = (i % 2 == 0)
        sign = 1 if above else -1
        x = spine_x0 + seg * (i + 0.5) + 8.0
        tx, ty = x + dx, spine_y + sign * dy

        # кость первого уровня и подпись категории у её конца
        ax.plot([x, tx], [spine_y, ty], color=COLORS["ink"], lw=1.0,
                zorder=3, solid_capstyle="round")
        ax.text(tx, ty + (2.5 if above else -2.5), cat, ha="center",
                va="bottom" if above else "top", fontsize=fs_cat,
                family=FONT, fontweight="bold", color=COLORS["accent"],
                zorder=6)

        # частные причины: короткие штрихи вдоль кости
        mirror = tx > spine_x1 - text_w - 24.0
        k = len(causes)
        max_chars = max(8, int(text_w / (0.5 * fs_cause)))
        for j, cause in enumerate(causes):
            cause = wrap_text(cause, max_chars)
            t = 0.5 if k == 1 else 0.22 + 0.58 * j / (k - 1)
            bx, by = x + t * dx, spine_y + sign * t * dy
            tick = 13.0
            ax.plot([bx, bx + (-tick if mirror else tick)], [by, by],
                    color=COLORS["ink"], lw=0.7, zorder=3)
            ax.text(bx + (-tick - 2 if mirror else tick + 2), by, cause,
                    ha="right" if mirror else "left", va="center",
                    fontsize=fs_cause, family=FONT, color=COLORS["text"],
                    linespacing=1.15, zorder=6)

    path_png = os.path.abspath(path_png)
    os.makedirs(os.path.dirname(path_png), exist_ok=True)
    fig.savefig(path_png, dpi=DPI, facecolor="white")
    out_svg = None
    if svg:
        out_svg = os.path.splitext(path_png)[0] + ".svg"
        fig.savefig(out_svg, facecolor="white")
    plt.close(fig)
    return path_png, out_svg


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
