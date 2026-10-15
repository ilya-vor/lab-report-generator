# -*- coding: utf-8 -*-
"""
Генератор BPMN 2.0 (As-Is) и визуализации для Лабораторной работы №1.
Бизнес-процесс: "Периодический контроль применения СИЗ на сварочном участке".
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch, Circle, Polygon

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------
# Геометрия макета
# ----------------------------------------------------------------------------
POOL_X, POOL_Y = 40, 60
LANE_LABEL_W = 150
LANE_H = 155
COL_W = 175
POOL_H = 5 * LANE_H
POOL_W = LANE_LABEL_W + 16 * COL_W

LANES = [
    "Мастер участка\n(сварочный участок)",
    "Сварщик\n(рабочее место)",
    "Служба охраны труда",
    "Начальник цеха\n(руководство)",
    "Видеонаблюдение /\nслужба безопасности",
]


def cx(col):
    return POOL_X + LANE_LABEL_W + col * COL_W + COL_W / 2


def cy(lane, offset=0):
    return POOL_Y + lane * LANE_H + LANE_H / 2 + offset


# id, type, name, lane, col, offset
NODES = [
    ("Start_1",          "start",  "Начало смены",                                        0, 0,  0),
    ("Task_Instruktazh", "task",   "Провести инструктаж и выдать сменное задание",         0, 1,  0),
    ("Task_Obrood",      "task",   "Обойти сварочный участок",                             0, 2,  0),
    ("Gw_NaMeste",       "xor",    "Сварщик на рабочем месте?",                            0, 3,  0),
    ("Task_Utochnit",    "task",   "Уточнить местонахождение сварщика",                    0, 3, -56),
    ("Task_Proverka",    "task",   "Визуально проверить СИЗ: маска, перчатки, обувь",      0, 4,  0),
    ("Gw_SIZ",           "xor",    "Все СИЗ надеты?",                                     0, 5,  0),
    ("Task_Zamechanie",  "task",   "Сделать устное замечание",                             0, 5, -56),
    ("Task_Jurnal",      "task",   "Зафиксировать результат в журнале обхода (Excel)",     0, 6,  0),
    ("Event_EndSmeny",   "timer",  "Конец смены",                                          0, 7,  0),
    ("Task_Otchet",      "task",   "Сформировать отчёт за смену (Excel)",                  0, 9,  0),
    ("Task_Peredat",     "task",   "Передать отчёт в службу охраны труда",                 0, 10, 0),

    ("Task_Nadet",       "task",   "Надеть / поправить СИЗ",                               1, 5,  0),

    ("Task_ProveritOT",  "task",   "Проверить и обобщить данные о нарушениях",             2, 11, 0),
    ("Task_InstrPovt",   "task",   "Провести повторный инструктаж по СИЗ",                 2, 13, 0),

    ("Task_Reshenie",    "task",   "Принять решение о мерах воздействия",                  3, 12, 0),
    ("Gw_Vzyskanie",     "xor",    "Требуется дисциплинарное взыскание?",                  3, 13, 0),
    ("Task_Vzyskanie",   "task",   "Оформить дисциплинарное взыскание",                    3, 14, 0),
    ("End_1",            "end",    "Отчёт сдан, смена закрыта",                            3, 15, 0),

    ("Task_Video",       "task",   "Просмотреть архив видеонаблюдения (плановая проверка)",4, 7,  0),
    ("Gw_Video",         "xor",    "Обнаружено нарушение на видео?",                       4, 8,  0),
    ("Task_FixVideo",    "task",   "Зафиксировать нарушение по видео",                     4, 9,  0),
    ("Task_VideoJurnal", "task",   "Добавить запись в журнал нарушений",                    4, 10, 0),
]

# id, source, target, label
FLOWS = [
    ("F1",  "Start_1",         "Task_Instruktazh", "",     False),
    ("F2",  "Task_Instruktazh", "Task_Obrood",      "",     False),
    ("F3",  "Task_Obrood",     "Gw_NaMeste",        "",     False),
    ("F4",  "Gw_NaMeste",      "Task_Proverka",     "да",   True),
    ("F5",  "Gw_NaMeste",      "Task_Utochnit",     "нет",  True),
    ("F6",  "Task_Utochnit",   "Task_Obrood",       "",     False),
    ("F7",  "Task_Proverka",   "Gw_SIZ",            "",     False),
    ("F8",  "Gw_SIZ",          "Task_Zamechanie",   "нет",  True),
    ("F9",  "Gw_SIZ",          "Task_Jurnal",       "да",   True),
    ("F10", "Task_Zamechanie", "Task_Jurnal",       "",     False),
    ("F11", "Task_Zamechanie", "Task_Nadet",        "",     False),
    ("F12", "Task_Nadet",      "Task_Proverka",     "",     False),
    ("F13", "Task_Jurnal",     "Task_Video",        "",     False),
    ("F14", "Task_Video",      "Gw_Video",          "",     False),
    ("F15", "Gw_Video",        "Task_FixVideo",     "да",   True),
    ("F16", "Gw_Video",        "Event_EndSmeny",    "нет",  True),
    ("F17", "Task_FixVideo",   "Task_VideoJurnal",  "",     False),
    ("F18", "Task_VideoJurnal","Event_EndSmeny",    "",     False),
    ("F19", "Event_EndSmeny",  "Task_Otchet",       "",     False),
    ("F20", "Task_Otchet",     "Task_Peredat",      "",     False),
    ("F21", "Task_Peredat",    "Task_ProveritOT",   "",     False),
    ("F22", "Task_ProveritOT", "Task_Reshenie",     "",     False),
    ("F23", "Task_Reshenie",   "Gw_Vzyskanie",      "",     False),
    ("F24", "Gw_Vzyskanie",    "Task_Vzyskanie",    "да",   True),
    ("F25", "Gw_Vzyskanie",    "Task_InstrPovt",    "нет",  True),
    ("F26", "Task_Vzyskanie",  "End_1",             "",     False),
    ("F27", "Task_InstrPovt",  "End_1",             "",     False),
]

# Проблемные зоны (для подсветки и легенды)
PROBLEM_STYLE = {
    "Task_Video":       ("#f8d7da", "#c0392b", "узкое место"),
    "Task_Jurnal":      ("#ffe8cc", "#e67e22", "мёртвая зона / ручной ввод"),
    "Task_Zamechanie":  ("#fff3b0", "#b7950b", "дублирование"),
    "Task_Proverka":    ("#fff3b0", "#b7950b", "дублирование"),
    "Task_Otchet":      ("#ffe8cc", "#e67e22", "мёртвая зона / ручной ввод"),
    "Task_Peredat":     ("#e2d9f3", "#7048a8", "неопределённость отв."),
    "Event_EndSmeny":   ("#d1ecf1", "#117a8b", "нет контроля в реальном времени"),
}

NODE_MAP = {n[0]: n for n in NODES}


def node_size(ntype):
    if ntype == "task":
        return 140, 72
    if ntype == "xor":
        return 44, 44
    return 34, 34


# ----------------------------------------------------------------------------
# Генерация BPMN 2.0 XML
# ----------------------------------------------------------------------------
def xml_escape(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def node_center(node):
    _, _, _, lane, col, off = node
    return cx(col), cy(lane, off)


def anchor_points(sid, tid):
    sx, sy = node_center(NODE_MAP[sid])
    tx, ty = node_center(NODE_MAP[tid])
    sw, sh = node_size(NODE_MAP[sid][1])
    tw, th = node_size(NODE_MAP[tid][1])
    dx, dy = tx - sx, ty - sy
    if abs(dx) >= abs(dy):
        if dx >= 0:
            return (sx + sw / 2, sy), (tx - tw / 2, ty)
        return (sx - sw / 2, sy), (tx + tw / 2, ty)
    if dy >= 0:
        return (sx, sy + sh / 2), (tx, ty - th / 2)
    return (sx, sy - sh / 2), (tx, ty + th / 2)


def generate_bpmn():
    lines = []
    A = lines.append
    A('<?xml version="1.0" encoding="UTF-8"?>')
    A('<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"')
    A('  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"')
    A('  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"')
    A('  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"')
    A('  xmlns:bioc="http://bpmn.io/schema/bpmn/biocolor/1.0"')
    A('  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    A('  id="Definitions_Lab1" targetNamespace="http://bpmn.io/schema/bpmn"')
    A('  exporter="Lab1 Generator" exporterVersion="1.0">')
    A('  <bpmn:collaboration id="Collaboration_1">')
    A('    <bpmn:participant id="Participant_1" processRef="Process_AsIs" />')
    A('  </bpmn:collaboration>')
    A('  <bpmn:process id="Process_AsIs" name="As-Is: контроль применения СИЗ" isExecutable="false">')

    # Lane set
    A('    <bpmn:laneSet id="LaneSet_1">')
    for i, name in enumerate(LANES):
        A('      <bpmn:lane id="Lane_%d" name="%s">' % (i, xml_escape(name.replace("\n", " "))))
        for n in NODES:
            if n[3] == i:
                A('        <bpmn:flowNodeRef>%s</bpmn:flowNodeRef>' % n[0])
        A('      </bpmn:lane>')
    A('    </bpmn:laneSet>')

    # Nodes
    for nid, ntype, name, lane, col, off in NODES:
        nm = xml_escape(name)
        if ntype == "task":
            A('    <bpmn:userTask id="%s" name="%s" />' % (nid, nm))
        elif ntype == "xor":
            A('    <bpmn:exclusiveGateway id="%s" name="%s" />' % (nid, nm))
        elif ntype == "start":
            A('    <bpmn:startEvent id="%s" name="%s" />' % (nid, nm))
        elif ntype == "end":
            A('    <bpmn:endEvent id="%s" name="%s" />' % (nid, nm))
        elif ntype == "timer":
            A('    <bpmn:intermediateCatchEvent id="%s" name="%s">' % (nid, nm))
            A('      <bpmn:timerEventDefinition id="Timer_%s" />' % nid)
            A('    </bpmn:intermediateCatchEvent>')

    # Flows
    for fid, src, tgt, label, cond in FLOWS:
        A('    <bpmn:sequenceFlow id="%s" sourceRef="%s" targetRef="%s"%s>' %
          (fid, src, tgt,
           '' if not label else ' name="%s"' % xml_escape(label)))
        if cond:
            A('      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">%s</bpmn:conditionExpression>' % ('true' if label == 'да' else 'false'))
        A('    </bpmn:sequenceFlow>')
    A('  </bpmn:process>')

    # ----- BPMN DI -----
    # В BPMN ось Y направлена вниз, а в макете matplotlib — вверх.
    # Зеркалим координаты по вертикали, чтобы порядок дорожек в Camunda
    # совпадал с картинкой отчёта.
    def flip_y(y):
        return 2 * POOL_Y + POOL_H - y

    A('  <bpmndi:BPMNDiagram id="BPMNDiagram_1">')
    A('    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Collaboration_1">')
    A('      <bpmndi:BPMNShape id="Participant_1_di" bpmnElement="Participant_1" isHorizontal="true">')
    A('        <dc:Bounds x="%d" y="%d" width="%d" height="%d" />' % (POOL_X, POOL_Y, POOL_W, POOL_H))
    A('      </bpmndi:BPMNShape>')
    for i in range(len(LANES)):
        ly = POOL_Y + (len(LANES) - 1 - i) * LANE_H
        A('      <bpmndi:BPMNShape id="Lane_%d_di" bpmnElement="Lane_%d" isHorizontal="true">' % (i, i))
        A('        <dc:Bounds x="%d" y="%d" width="%d" height="%d" />' % (POOL_X, ly, POOL_W, LANE_H))
        A('      </bpmndi:BPMNShape>')

    for nid, ntype, name, lane, col, off in NODES:
        x, y = node_center((nid, ntype, name, lane, col, off))
        y = flip_y(y)
        w, h = node_size(ntype)
        fill, stroke, _ = PROBLEM_STYLE.get(nid, (None, None, None))
        color = ''
        if fill:
            color = ' bioc:fill="%s" bioc:stroke="%s"' % (fill, stroke)
        A('      <bpmndi:BPMNShape id="%s_di" bpmnElement="%s"%s>' % (nid, nid, color))
        A('        <dc:Bounds x="%.0f" y="%.0f" width="%d" height="%d" />' % (x - w / 2, y - h / 2, w, h))
        A('      </bpmndi:BPMNShape>')

    for fid, src, tgt, label, cond in FLOWS:
        s, e = anchor_points(src, tgt)
        s = (s[0], flip_y(s[1]))
        e = (e[0], flip_y(e[1]))
        A('      <bpmndi:BPMNEdge id="%s_di" bpmnElement="%s">' % (fid, fid))
        A('        <di:waypoint x="%.0f" y="%.0f" />' % (s[0], s[1]))
        A('        <di:waypoint x="%.0f" y="%.0f" />' % (e[0], e[1]))
        A('      </bpmndi:BPMNEdge>')
    A('    </bpmndi:BPMNPlane>')
    A('  </bpmndi:BPMNDiagram>')
    A('</bpmn:definitions>')

    path = os.path.join(OUT_DIR, "As-Is_Контроль_СИЗ.bpmn")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


# ----------------------------------------------------------------------------
# Визуализация (swimlane)
# ----------------------------------------------------------------------------
def wrap(text, width=20):
    words = text.split()
    out, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return "\n".join(out)


def draw_diagram():
    fig_w = POOL_W / 100.0
    fig_h = (POOL_H + 195) / 100.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=100)
    ax.set_xlim(-40, POOL_W + 60)
    ax.set_ylim(-165, POOL_H + 55)
    ax.axis("off")

    # Pool border
    ax.add_patch(Rectangle((POOL_X, POOL_Y), POOL_W, POOL_H,
                           fill=False, edgecolor="#333333", linewidth=2, zorder=1))
    # Lanes
    for i, name in enumerate(LANES):
        ly = POOL_Y + i * LANE_H
        face = "#ffffff" if i % 2 == 0 else "#f4f6f8"
        ax.add_patch(Rectangle((POOL_X, ly), POOL_W, LANE_H,
                               facecolor=face, edgecolor="#999999", linewidth=1, zorder=0))
        ax.add_patch(Rectangle((POOL_X, ly), LANE_LABEL_W, LANE_H,
                               facecolor="#e8ecf1", edgecolor="#999999", linewidth=1, zorder=1))
        ax.text(POOL_X + LANE_LABEL_W / 2, ly + LANE_H / 2, name,
                ha="center", va="center", fontsize=8, rotation=90, zorder=2)

    # Flows first (below nodes)
    for fid, src, tgt, label, cond in FLOWS:
        s, e = anchor_points(src, tgt)
        color = "#444444"
        arr = FancyArrowPatch(s, e, arrowstyle="-|>", mutation_scale=12,
                              color=color, linewidth=1.1, zorder=3,
                              shrinkA=0, shrinkB=0)
        ax.add_patch(arr)
        if label:
            mx, my = (s[0] + e[0]) / 2, (s[1] + e[1]) / 2
            ax.text(mx, my, label, fontsize=6.8, color="#b00020" if label == "нет" else "#0b6b0b",
                    ha="center", va="center", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))

    # Nodes
    for nid, ntype, name, lane, col, off in NODES:
        x, y = cx(col), cy(lane, off)
        w, h = node_size(ntype)
        fill, edge, tag = PROBLEM_STYLE.get(nid, (None, None, None))
        if ntype == "task":
            fc = fill if fill else "#ffffff"
            ec = edge if edge else "#2c3e50"
            ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                         boxstyle="round,pad=0.02,rounding_size=8",
                         facecolor=fc, edgecolor=ec, linewidth=1.6, zorder=5))
            ax.text(x, y, wrap(name, 19), ha="center", va="center", fontsize=6.9, zorder=6)
        elif ntype == "xor":
            pts = [(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)]
            ax.add_patch(Polygon(pts, closed=True, facecolor="#fff8e1",
                                 edgecolor="#b8860b", linewidth=1.6, zorder=5))
            ax.text(x, y, "X", ha="center", va="center", fontsize=9.5, fontweight="bold", zorder=6)
            ax.text(x, y + h / 2 + 3, wrap(name, 21), ha="center", va="bottom", fontsize=6.4,
                    style="italic", color="#7a5c00", zorder=6)
        elif ntype in ("start", "end"):
            fc = "#d4edda" if ntype == "start" else "#f8d7da"
            ec = "#28a745" if ntype == "start" else "#c0392b"
            ax.add_patch(Circle((x, y), w / 2, facecolor=fc, edgecolor=ec, linewidth=2, zorder=5))
            ax.text(x, y - h / 2 - 10, wrap(name, 15), ha="center", va="top", fontsize=6.8, zorder=6)
        elif ntype == "timer":
            fc, ec = PROBLEM_STYLE.get(nid, ("#e3f2fd", "#1565c0"))[:2]
            ax.add_patch(Circle((x, y), w / 2, facecolor=fc, edgecolor=ec, linewidth=2, zorder=5))
            ax.plot([x, x], [y, y + w * 0.30], color=ec, linewidth=1.4, zorder=6)
            ax.plot([x, x + w * 0.24], [y, y], color=ec, linewidth=1.4, zorder=6)
            ax.text(x, y - h / 2 - 10, wrap(name, 13), ha="center", va="top", fontsize=6.8, zorder=6)

    # Legend
    lx, ly = POOL_X, -145
    ax.text(lx, ly + 34, "Проблемные зоны As-Is:", fontsize=8.5, fontweight="bold")
    legend = [
        ("#f8d7da", "#c0392b", "Узкое место"),
        ("#fff3b0", "#b7950b", "Дублирование функций"),
        ("#ffe8cc", "#e67e22", "«Мёртвая зона» / ручной перенос данных"),
        ("#e2d9f3", "#7048a8", "Неопределённость ответственности"),
        ("#d1ecf1", "#117a8b", "Отсутствие контроля в реальном времени"),
    ]
    for i, (fc, ec, txt) in enumerate(legend):
        xx = lx + i * 500
        ax.add_patch(Rectangle((xx, ly), 38, 20, facecolor=fc, edgecolor=ec, linewidth=1.5))
        ax.text(xx + 46, ly + 10, txt, fontsize=7.3, va="center")

    ax.set_title("Рисунок 1 — BPMN 2.0 «As-Is»: периодический контроль применения СИЗ на сварочном участке",
                 fontsize=11, fontweight="bold", pad=11)

    png = os.path.join(OUT_DIR, "As-Is_Контроль_СИЗ.png")
    svg = os.path.join(OUT_DIR, "As-Is_Контроль_СИЗ.svg")
    fig.savefig(png, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png, svg


if __name__ == "__main__":
    bpmn = generate_bpmn()
    png, svg = draw_diagram()
    print("BPMN:", bpmn)
    print("PNG :", png)
    print("SVG :", svg)
