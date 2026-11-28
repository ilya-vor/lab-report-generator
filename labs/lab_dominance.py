# -*- coding: utf-8 -*-
"""Лабораторная работа №2, дисциплина «Принятие решений в условиях
неопределённости».

Тема: стохастическое доминирование. Дневные доходности трёх акций
фармацевтических компаний (Bayer, Merck & Co, Sanofi) сравниваются по
критериям первого и второго порядков.

Эмпирические законы взяты из лабораторной работы №1: это интервальные
вариационные ряды, которые здесь трактуются как дискретные случайные
величины - значениями служат середины интервалов x_j, вероятностями -
относительные частоты p_j. Поэтому функция распределения ступенчата, а
интеграл разности функций распределения линеен на каждом участке.

Все числа в тексте считаются при сборке.

Запуск:  python build.py --lab risk2
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

from labkit.docxgen import Report, ReportMeta
from labkit.schemes import DPI, FONT

from labs import dominance, risk_data, risk_measures

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(HERE, "out")

PAGE_TITLE = "СТОХАСТИЧЕСКОЕ\nДОМИНИРОВАНИЕ"
SHORT_TITLE = ("Стохастическое доминирование на примере акций "
               "фармацевтических компаний")
FRAME_TITLE = "Стохастическое доминирование"
OUT_NAME = "Воробьев_И_С_отчет_по_2_ЛР_Стохастическое_доминирование.docx"

TICKERS = risk_data.TICKERS
LABELS = {"BAYN.DE": "Bayer", "MRK": "Merck", "SAN.PA": "Sanofi"}
COLOR = {"BAYN.DE": "#1f4e79", "MRK": "#b06a2c", "SAN.PA": "#2e7d32"}

# Порядок изложения: подписи подразделов и пары бумаг.
SUBTITLES = {
    ("BAYN.DE", "MRK"): "Сравнение Bayer с Merck",
    ("MRK", "SAN.PA"): "Сравнение Sanofi с Merck",
    ("BAYN.DE", "SAN.PA"): "Сравнение Sanofi с Bayer",
}
ORDER = [("BAYN.DE", "MRK"), ("MRK", "SAN.PA"), ("BAYN.DE", "SAN.PA")]


# ---------------------------------------------------------------------------
# Форматирование чисел в русской записи
# ---------------------------------------------------------------------------
def ru(value, digits=2):
    """Число с запятой в дробной части и пробелом между разрядами."""
    text = ("{:,.%df}" % digits).format(value)
    text = text.replace(",", "\u00a0").replace(".", ",")
    return text.replace("-", "\u2212")


def pct(value, digits=2):
    """Доля, переведённая в проценты."""
    return ru(value * 100.0, digits)


def plural(number, one, few, many):
    """Склонение существительного при числительном."""
    if number % 10 == 1 and number % 100 != 11:
        return "%d %s" % (number, one)
    if 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        return "%d %s" % (number, few)
    return "%d %s" % (number, many)


def _lower(fa, fb, a, b):
    """Какая из двух кривых ниже в данной точке."""
    if abs(fa - fb) < 1e-9:
        return "кривые сливаются"
    return "ниже проходит кривая %s" % LABELS[a if fa < fb else b]


def axis_pct(value, _pos=None):
    return ("%.0f" % value).replace("-", "\u2212") + " %"


def axis_frac(value, _pos=None):
    return ("%.2f" % value).replace(".", ",").replace("-", "\u2212")


def axis_unit(value, _pos=None):
    return ("%.1f" % value).replace(".", ",").replace("-", "\u2212")


def _style_axes(ax, ticks, ylabel, yformatter=axis_frac):
    ax.set_xlim(-10.0, 12.0)
    ax.set_xlabel("дневная доходность, %", fontsize=7.5, family=FONT,
                  color="#1b1b1b")
    ax.set_ylabel(ylabel, fontsize=7.5, family=FONT, color="#1b1b1b")
    ax.set_xticks(list(ticks))
    ax.set_xticklabels([axis_pct(v) for v in ticks],
                       fontsize=7, family=FONT)
    ax.grid(True, color="#e3e7ec", lw=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=7)
    ax.yaxis.set_major_formatter(FuncFormatter(yformatter))
    for label in ax.get_yticklabels():
        label.set_fontfamily(FONT)


def _cdf_points(dist):
    """Точки для ступенчатого графика функции распределения."""
    xs = [dist.x[0] - 3.0] + list(dist.x) + [dist.x[-1] + 3.0]
    ys = [0.0] + list(dist.cum) + [1.0]
    return [x * 100.0 for x in xs], ys


# ---------------------------------------------------------------------------
# Рисунок 1: три функции распределения
# ---------------------------------------------------------------------------
def chart_all(dists, number=1):
    fig, ax = plt.subplots(figsize=(16.5 / 2.54, 6.2 / 2.54), dpi=DPI)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.90, bottom=0.16)
    for ticker in TICKERS:
        dist = dists[ticker]
        xs, ys = _cdf_points(dist)
        ax.step(xs, ys, where="post", color=COLOR[ticker], lw=1.2,
                label=LABELS[ticker])
        ax.plot([x * 100.0 for x in dist.x], dist.cum, "o", ms=2.4,
                color=COLOR[ticker])
    ax.set_ylim(-0.03, 1.05)
    ax.legend(fontsize=8, frameon=False, loc="upper left",
              prop={"family": FONT, "size": 8})
    _style_axes(ax, range(-10, 13, 2), "F(x)", yformatter=axis_unit)
    ax.yaxis.set_major_locator(MultipleLocator(0.2))
    path = os.path.join(OUT_DIR, "dom_fig%d.png" % number)
    os.makedirs(OUT_DIR, exist_ok=True)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Рисунок пары: две функции распределения
# ---------------------------------------------------------------------------
def chart_cdf(a, b, dists, number):
    fig, ax = plt.subplots(figsize=(16.5 / 2.54, 5.0 / 2.54), dpi=DPI)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.92, bottom=0.17)
    for ticker, style in ((a, "-"), (b, "--")):
        dist = dists[ticker]
        xs, ys = _cdf_points(dist)
        ax.step(xs, ys, where="post", color=COLOR[ticker], lw=1.2,
                ls=style, label=LABELS[ticker])
        ax.plot([x * 100.0 for x in dist.x], dist.cum, "o", ms=2.4,
                color=COLOR[ticker])
    ax.set_ylim(-0.03, 1.05)
    ax.legend(fontsize=8, frameon=False, loc="upper left",
              prop={"family": FONT, "size": 8})
    _style_axes(ax, range(-10, 13, 2), "F(x)", yformatter=axis_unit)
    ax.yaxis.set_major_locator(MultipleLocator(0.2))
    path = os.path.join(OUT_DIR, "dom_fig%d.png" % number)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Рисунок пары: разность функций распределения
# ---------------------------------------------------------------------------
def chart_diff(a, b, result, number):
    fig, ax = plt.subplots(figsize=(16.5 / 2.54, 4.6 / 2.54), dpi=DPI)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.92, bottom=0.17)
    xs = [x * 100.0 for x in result["grid"]]
    diffs = [v * 100.0 for v in result["d1"]]
    ax.axhline(0.0, color="#5b6770", lw=0.8)
    ax.fill_between(xs, diffs, 0.0, where=[v >= 0 for v in diffs],
                    step="post", color=COLOR[a], alpha=0.20)
    ax.fill_between(xs, diffs, 0.0, where=[v < 0 for v in diffs],
                    step="post", color=COLOR[b], alpha=0.20)
    ax.step(xs, diffs, where="post", color="#1b1b1b", lw=0.9)

    roots = result["second"]["crossings"]
    if roots:
        point = roots[-1] * 100.0
        ax.axvline(point, color="#a33", lw=0.9, ls=(0, (4, 3)), zorder=1)
        ax.annotate("∫(F₁ − F₂)dx = 0 при x ≈ %s\u00a0%%" % ru(point, 2),
                    xy=(point, 0.97), xycoords=("data", "axes fraction"),
                    xytext=(-4, -2), ha="right", va="top",
                    textcoords="offset points", fontsize=7,
                    family=FONT, color="#a33")
    lo, hi = ax.get_ylim()
    ax.set_ylim(lo - 0.04 * (hi - lo), hi + 0.14 * (hi - lo))
    _style_axes(ax, range(-10, 13, 2), "F₁(x) − F₂(x), п.п.")
    path = os.path.join(OUT_DIR, "dom_fig%d.png" % number)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Кусочно-заданная запись функции распределения
# ---------------------------------------------------------------------------
def cdf_formula(ticker, dist):
    """Строки аналитической записи ступенчатой функции распределения."""
    name = "F_%s(x)" % LABELS[ticker]
    lines = ["%s = 0, при x < %s\u00a0%%;" % (name, pct(dist.x[0]))]
    for j in range(len(dist.x)):
        low = pct(dist.x[j])
        prob = ru(dist.cum[j], 4)
        if j + 1 < len(dist.x):
            lines.append("%s = %s, при %s\u00a0%% ≤ x < %s\u00a0%%;"
                         % (name, prob, low, pct(dist.x[j + 1])))
        else:
            lines.append("%s = 1, при x ≥ %s\u00a0%%." % (name, low))
    return lines


def integral_formula(ticker_a, ticker_b, terms, per_line=3, size=10):
    """Кусочно-линейная запись интеграла разности функций распределения."""
    head = ("∫_{−∞}^{t} [F_%s(x) − F_%s(x)] dx ="
            % (LABELS[ticker_a], LABELS[ticker_b]))
    items = []
    for u, coef in terms:
        sign = "−" if coef < 0 else "+"
        shift = ("t + %s" % pct(-u)) if u < 0 else ("t − %s" % pct(u))
        items.append("%s %s·(%s)₊" % (sign, ru(abs(coef), 4), shift))
    lines = []
    chunk = []
    for i, item in enumerate(items):
        chunk.append(item)
        if len(chunk) == per_line or i == len(items) - 1:
            lines.append(" ".join(chunk))
            chunk = []
    return [head] + lines


# ---------------------------------------------------------------------------
# Текст отчёта
# ---------------------------------------------------------------------------
def build_content(rep, dates, data, result, dists, comparisons):
    stats = {t: result[t]["profile"] for t in TICKERS}
    n = stats[TICKERS[0]]["n"]

    def label(ticker):
        return LABELS[ticker]

    def compare(a, b):
        return comparisons[(a, b)]

    def g(t, key):
        """Значение интеграла разности в точке t (в п.п.)."""
        return sum(coef * (t - u) for u, coef in key["terms"] if t > u)

    by_mean = sorted(TICKERS, key=lambda t: stats[t]["mean"], reverse=True)
    by_std = sorted(TICKERS, key=lambda t: stats[t]["std"])
    by_var = sorted(TICKERS, key=lambda t: stats[t]["var_"][0.99])

    # ------------------------------------------------------------------
    rep.h1("Введение")
    rep.p("Работа посвящена сравнению трёх объектов инвестирования по "
          "критериям стохастического доминирования. В отличие от сводных "
          "характеристик (средней доходности, дисперсии, VaR), эти критерии "
          "учитывают весь закон распределения: если одна бумага доминирует "
          "другую, выбор между ними не зависит от функции полезности "
          "инвестора, лишь бы она возрастала.")

    # ------------------------------------------------------------------
    rep.h2("Цель работы")
    rep.p("Цель работы - изучить критерии стохастического доминирования "
          "первого и второго порядков и применить их к выбору объекта "
          "инвестирования среди акций трёх фармацевтических компаний, "
          "законы распределения доходностей которых построены в "
          "лабораторной работе №1.")
    rep.p("Для достижения цели решаются следующие задачи:")
    rep.numbers([
        "построить эмпирические функции распределения дневных доходностей "
        "и записать их аналитически;",
        "проверить попарно критерий доминирования первого порядка;",
        "построить разности функций распределения и их интегралы, "
        "проверить критерий доминирования второго порядка;",
        "сформулировать выводы о выборе бумаги для разных профилей "
        "инвестора.",
    ])

    # ------------------------------------------------------------------
    rep.h2("Вариант задания")
    rep.p("Вариант 3: Bayer (BAYN.DE), Merck & Co (MRK) и Sanofi (SAN.PA). "
          "Период наблюдений - с %s по %s. Сравнение выполняется попарно: "
          "Bayer и Merck, Sanofi и Merck, Sanofi и Bayer. Для каждой пары "
          "строятся функции распределения доходностей, их разности и "
          "интегралы этих разностей."
          % (dates[0].strftime("%d.%m.%Y"),
             dates[-1].strftime("%d.%m.%Y")))

    # ------------------------------------------------------------------
    rep.h2("Исходные данные")
    rep.p("Используются данные лабораторной работы №1: скорректированные "
          "цены закрытия за два года, приведённые к общим торговым дням "
          "трёх бирж. Дневная доходность считается как "
          "X_t = (P_t − P_(t−1)) / P_(t−1) и выражается в долях; в "
          "таблицах и на графиках она переведена в проценты. Каждая бумага "
          "имеет n = %d наблюдений." % n)

    rows = []
    for ticker in TICKERS:
        s = stats[ticker]
        rows.append((
            "%s (%s)" % (label(ticker), ticker),
            pct(s["mean"], 3),
            pct(s["std"], 3),
            pct(s["var_"][0.99], 2),
            pct(dists[ticker].F(0.0), 2),
            pct(dists[ticker].F(-0.03), 2),
        ))
    rep.table(
        ("Акция", "E(X), %", "Std, %", "VaR(0,99), %",
         "P(X ≤ 0), %", "P(X ≤ −3), %"),
        rows, (3.0, 2.3, 2.3, 2.9, 2.8, 3.0), size=10, keep_together=True,
        caption="Таблица 1. Характеристики дневных доходностей, %")

    rep.p("Наибольшая средняя доходность у %s (%s\u00a0%%), наименьшая - у "
          "%s (%s\u00a0%%). По волатильности порядок такой: %s. При этом "
          "наименьший уровень потерь, который не превышается с "
          "вероятностью 0,99, даёт %s (%s\u00a0%%), а наибольший - %s "
          "(%s\u00a0%%). Разброс доходностей и вероятности падения убывают "
          "от Bayer к Sanofi, поэтому выбор нельзя сделать по одной "
          "характеристике."
          % (label(by_mean[0]), pct(stats[by_mean[0]]["mean"], 3),
             label(by_mean[-1]), pct(stats[by_mean[-1]]["mean"], 3),
             ", ".join("%s (%s\u00a0%%)"
                       % (label(t), pct(stats[t]["std"], 3))
                       for t in by_std),
             label(by_var[0]), pct(stats[by_var[0]]["var_"][0.99], 2),
             label(by_var[-1]), pct(stats[by_var[-1]]["var_"][0.99], 2)))

    rep.p("Законы распределения доходностей взяты из лабораторной работы "
          "№1: это интервальные вариационные ряды с k = %d интервалами "
          "равной длины. Закон задаётся дискретной случайной величиной: "
          "её значениями служат середины интервалов x_j, а вероятностями - "
          "относительные частоты p_j = n_j / N. В таблицах 2-4 приведены "
          "полученные законы и значения функции распределения F(x_j), "
          "накопленные к каждой середине интервала."
          % result[TICKERS[0]]["series"]["k"])

    for i, ticker in enumerate(TICKERS, 2):
        dist = dists[ticker]
        rows = []
        for x, p, f in zip(dist.x, dist.p, dist.cum):
            rows.append((pct(x, 2), ru(p, 4), ru(f, 4)))
        rep.table(
            ("x_j, %", "p_j", "F(x_j)"),
            rows, (3.4, 3.4, 3.4), size=10, keep_together=True,
            caption="Таблица %d. Закон распределения дневной доходности %s"
                    % (i, label(ticker)))

    # ------------------------------------------------------------------
    rep.h1("Ход работы", page_break=False)
    rep.p("Функция распределения дискретной величины - ступенчатая "
          "функция: она постоянна между соседними значениями и делает "
          "скачок величиной p_j в точке x_j:")
    rep.formula("F(x)\u00a0=\u00a0P(X\u00a0≤\u00a0x)\u00a0=\u00a0∑ p_j,   "
                "сумма по всем x_j\u00a0≤\u00a0x.")
    rep.p("Интеграл функции распределения от −∞ до t равен площади под "
          "ступенчатым графиком и представляет собой непрерывную "
          "кусочно-линейную функцию:")
    rep.formula("G(t)\u00a0=\u00a0∫_{−∞}^{t} F(x)\u00a0dx.")
    rep.p("Бумага A доминирует бумагу B в первом порядке, если "
          "F_A(x)\u00a0≤\u00a0F_B(x) при всех x. Бумага A доминирует бумагу B "
          "во втором порядке, если интеграл разности функций "
          "распределения неположителен при всех t:")
    rep.formula("∫_{−∞}^{t} [F_A(x)\u00a0−\u00a0F_B(x)]\u00a0dx\u00a0≤\u00a00   "
                "для всех t.")
    rep.p("Для дискретных величин разность F_A\u00a0−\u00a0F_B кусочно-"
          "постоянна, поэтому её интеграл непрерывен и линеен на каждом "
          "участке между соседними значениями x_j. Проверка критерия "
          "сводится к знаку этой разности и к знаку её интеграла.")

    # ------------------------------------------------------------------
    rep.h2("Построение функций распределения")
    rep.p("На рисунке 1 приведены функции распределения дневных "
          "доходностей трёх акций, построенные по законам из таблиц 2-4. "
          "Горизонтальные участки соответствуют промежуткам между "
          "серединами интервалов, точки - накопленным вероятностям в "
          "серединах.")
    path = chart_all(dists, 1)
    rep.figure(path, "Рисунок 1. Функции распределения дневных доходностей "
               "трёх акций", width_cm=16.5)
    rep.p("Кривая Bayer идёт положе остальных: её значения растянуты на "
          "более широкий диапазон доходностей, от %s до %s\u00a0%%. У Sanofi "
          "диапазон самый узкий (%s...%s\u00a0%%), поэтому в окрестности нуля "
          "её функция распределения поднимается раньше: при x\u00a0=\u00a00 "
          "она равна %s против %s у Bayer и %s у Merck. Правее нуля "
          "соотношение меняется: при x\u00a0=\u00a0+5\u00a0%% значения равны "
          "%s, %s и %s соответственно."
          % (pct(dists[TICKERS[0]].x[0]), pct(dists[TICKERS[0]].x[-1]),
             pct(dists[TICKERS[2]].x[0]), pct(dists[TICKERS[2]].x[-1]),
             ru(dists[TICKERS[2]].F(0.0), 4),
             ru(dists[TICKERS[0]].F(0.0), 4),
             ru(dists[TICKERS[1]].F(0.0), 4),
             ru(dists[TICKERS[2]].F(0.05), 4),
             ru(dists[TICKERS[0]].F(0.05), 4),
             ru(dists[TICKERS[1]].F(0.05), 4)))
    rep.p("Аналитически функции распределения записываются как "
          "кусочно-постоянные функции с одиннадцатью участками, включая "
          "лучи (−∞; x_1) и [x_10; +∞).")
    for ticker in TICKERS:
        rep.formula_block(cdf_formula(ticker, dists[ticker]), size=10)

    # ------------------------------------------------------------------
    rep.h2("Критерий стохастического доминирования 1-го порядка")
    rep.p("Случайная величина X₁ доминирует случайную величину X₂ в первом "
          "порядке, если её функция распределения нигде не выше:")
    rep.formula("F₁(x)\u00a0≤\u00a0F₂(x)\u00a0\u00a0для всех x.")
    rep.p("Смысл условия такой: при любом уровне доходности x вероятность "
          "получить не больше x у первой бумаги не выше, чем у второй. "
          "Если кривые пересекаются, то левее точки пересечения "
          "предпочтительнее одна бумага, правее - другая, и доминирования "
          "нет. На рисунках 2-4 приведены попарные графики функций "
          "распределения.")

    for index, (a, b) in enumerate(ORDER, 2):
        item = compare(a, b)
        rep.h3(SUBTITLES[(a, b)])
        path = chart_cdf(a, b, dists, index)
        rep.figure(path, "Рисунок %d. Функции распределения доходностей %s "
                   "и %s" % (index, label(a), label(b)), width_cm=16.5)
        cross = item["first"]["crossings"]
        fa, fb = dists[a].F(-0.03), dists[b].F(-0.03)
        ga, gb = dists[a].F(0.03), dists[b].F(0.03)
        left = _lower(fa, fb, a, b)
        right = _lower(ga, gb, a, b)
        changes = ("один раз" if len(cross) == 1 else "несколько раз")
        rep.p("Кривые пересекаются: разность F(%s) − F(%s) меняет "
              "знак %s, в основном в окрестности нулевой доходности. При "
              "x = −3 %% значения функций равны %s и %s - %s; "
              "при x = +3 %% они равны %s и %s - %s. %s "
              "поэтому ни %s, ни %s не доминирует по первому порядку."
              % (label(a), label(b), changes,
                 ru(fa, 4), ru(fb, 4), left,
                 ru(ga, 4), ru(gb, 4), right,
                 ("Ни одна кривая не лежит ниже другой на всём "
                  "рассматриваемом диапазоне," if index == 2 else
                  "Ни одна из кривых не лежит ниже другой на всём "
                  "диапазоне доходностей,"),
                 label(a), label(b)))

    rep.p("Во всех трёх парах картина одинакова по смыслу: в области "
          "убытков ниже проходит кривая более рискованной бумаги, в "
          "области прибыли - кривая более доходной. Поэтому "
          "доминирование первого порядка отсутствует во всех парах: "
          "функции распределения попарно пересекаются.")

    # ------------------------------------------------------------------
    rep.h2("Критерий стохастического доминирования 2-го порядка")
    rep.p("Случайная величина X₁ доминирует случайную величину X₂ во втором "
          "порядке, если при любом t интеграл разности функций "
          "распределения неположителен:")
    rep.formula("∫_{−∞}^{t} [F₁(x)\u00a0−\u00a0F₂(x)]\u00a0dx\u00a0≤\u00a00   "
                "для всех t.")
    rep.p("Этот критерий допускает пересечение кривых F₁ и F₂, но требует, "
          "чтобы площадь между ними слева от любого t была не больше нуля. "
          "Для дискретных величин разность F₁\u00a0−\u00a0F₂ кусочно-"
          "постоянна, а интеграл - непрерывная кусочно-линейная функция с "
          "изломами в серединах интервалов. Если интеграл меняет знак, то "
          "ни одна из бумаг не доминирует и критерий не даёт однозначного "
          "ответа. На рисунках 5-7 показаны разности F₁\u00a0−\u00a0F₂ для "
          "трёх пар.")
    rep.p("Смена знака происходит в окрестности нулевой доходности и вблизи "
          "t\u00a0≈\u00a02,5\u00a0%. При малых t решает форма левого хвоста, "
          "поэтому в области около нуля предпочтительнее менее рискованная "
          "бумага; при больших t интеграл ведёт себя как t\u00a0−\u00a0E(X) и "
          "преимущество получает бумага с большей средней доходностью.")


    for index, (a, b) in enumerate(ORDER, 5):
        item = compare(a, b)
        rep.h3(SUBTITLES[(a, b)])
        path = chart_diff(a, b, item, index)
        rep.figure(path, "Рисунок %d. Разность функций распределения "
                   "доходностей %s и %s" % (index, label(a), label(b)),
                   width_cm=16.5)
        roots = item["second"]["crossings"]
        value0 = g(0.0, item) * 100.0
        value5 = g(0.05, item) * 100.0
        if index < 7:
            rep.p("Разность F_%s(x)\u00a0−\u00a0F_%s(x) ступенчата, её "
                  "интеграл записывается как сумма линейных слагаемых:"
                  % (label(a), label(b)))
            rep.formula_block(
                integral_formula(a, b, item["terms"]), size=9.5)
        rep.p("При t = 0 интеграл равен %s п.п., при "
              "t = 5 %% он равен %s п.п.: знак "
              "меняется, поэтому условие знакопостоянства нарушается и "
              "доминирования второго порядка нет ни у %s, ни у %s. "
              "Интеграл обращается в нуль при t ≈ %s."
              % (ru(value0, 4), ru(value5, 4), label(a), label(b),
                 (", ".join(ru(r * 100.0, 2) for r in roots) + " %")
                 if roots else "всех t"))


    # ------------------------------------------------------------------
    rep.h1("Вывод")
    rep.p("В работе построены эмпирические функции распределения дневных "
          "доходностей трёх акций, записаны их аналитические выражения, "
          "для каждой из трёх пар найдены разности функций распределения и "
          "их интегралы. По знаку разностей проверены критерии "
          "стохастического доминирования первого и второго порядков.")
    rep.numbers([
        "Доминирование первого порядка отсутствует во всех трёх парах: "
        "графики функций распределения попарно пересекаются, поэтому ни "
        "одно из условий F₁\u00a0≤\u00a0F₂ и F₂\u00a0≤\u00a0F₁ не выполняется "
        "на всём диапазоне доходностей.",
        "Доминирование второго порядка также отсутствует во всех трёх "
        "парах: интеграл разности функций распределения меняет знак, то "
        "есть условие неположительности интеграла нарушается при некоторых "
        "значениях целевого уровня t.",
        "При отсутствии доминирования выбор зависит от профиля инвестора. "
        "Агрессивному инвестору, который максимизирует ожидаемую "
        "доходность, подходит %s: E(X)\u00a0=\u00a0%s\u00a0%%, что больше, "
        "чем у остальных бумаг. Консервативному инвестору, который "
        "минимизирует уровень потерь VaR(0,99), подходит %s: "
        "VaR(0,99)\u00a0=\u00a0%s\u00a0%%. Умеренно-консервативному "
        "инвестору, который ориентируется на минимальную волатильность, "
        "подходит %s: Std\u00a0=\u00a0%s\u00a0%%."
        % (label(by_mean[0]), pct(stats[by_mean[0]]["mean"], 3),
           label(by_var[0]), pct(stats[by_var[0]]["var_"][0.99], 2),
           label(by_std[0]), pct(stats[by_std[0]]["std"], 3)),
    ])
    rep.p("Таким образом, критерии стохастического доминирования "
          "упорядочивают бумаги лишь частично: они позволяют уверенно "
          "отбросить худшие варианты, но при отсутствии доминирования "
          "окончательный выбор остаётся за инвестором и определяется его "
          "отношением к риску. Для такого выбора критерии нужно дополнять "
          "мерами риска из лабораторной работы №1 - ожидаемой доходностью, "
          "стандартным отклонением и VaR.")


def build():
    dates, data = risk_data.load()
    result = risk_measures.compute(data)
    series = {t: result[t]["series"] for t in TICKERS}
    dists, comparisons, pairs = dominance.build(TICKERS, series)

    meta = ReportMeta(
        lab_no="2",
        page_title=PAGE_TITLE,
        full_title=SHORT_TITLE,
        frame_title=FRAME_TITLE,
        dept="Институт информатики, математики и робототехники",
        discipline="Принятие решений в условиях неопределенности",
        teacher="Прокудина Е. И.",
        frame_teacher="Прокудина Е.И.",
        group="КАИД-104М",
        student="Воробьев И. С.",
        frame=False,
        out_name=OUT_NAME,
    )
    rep = Report(meta)
    rep.prepare()
    build_content(rep, dates, data, result, dists, comparisons)
    return rep.save()


if __name__ == "__main__":
    print(build())
