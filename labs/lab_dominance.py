# -*- coding: utf-8 -*-
"""Лабораторная работа №2, дисциплина «Принятие решений в условиях
неопределённости».

Тема: стохастическое доминирование. Дневные доходности трёх акций
фармацевтических компаний (Bayer, Merck & Co, Sanofi) сравниваются по
критериям первого и второго порядков. Для каждой пары строятся функции
распределения, их интегралы и разности - всего шесть рисунков.

Расчёт опирается на интервальные вариационные ряды из лабораторной работы
№1 (``labs.risk_measures``): внутри интервала распределение считается
равномерным. Все числа в тексте считаются при сборке.

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
THRESHOLDS = (-0.05, -0.03, -0.01, 0.0, 0.01, 0.03, 0.05)

IMG = {}


# ---------------------------------------------------------------------------
# Форматирование чисел в русской записи
# ---------------------------------------------------------------------------
def ru(value, digits=2):
    """Число с запятой в дробной части и пробелом между разрядами."""
    text = ("{:,.%df}" % digits).format(value)
    text = text.replace(",", "\u00a0").replace(".", ",")
    return text.replace("-", "\u2212")


def plural(number, one, few, many):
    """Склонение существительного при числительном."""
    if number % 10 == 1 and number % 100 != 11:
        return "%d %s" % (number, one)
    if 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        return "%d %s" % (number, few)
    return "%d %s" % (number, many)


def axis_pct(value, _pos=None):
    return ("%.0f" % value).replace("-", "\u2212") + " %"


def axis_frac(value, _pos=None):
    return ("%.2f" % value).replace(".", ",").replace("-", "−")


# ---------------------------------------------------------------------------
# Рисунок пары: функции и их разность
# ---------------------------------------------------------------------------
def chart_pair(a, b, result, order, number):
    """Два поля: слева функции A и B, справа их разность.

    ``order`` = 1 - функции распределения F, ``order`` = 2 - их интегралы S.
    """
    if order == 1:
        key, diff_key = "d1", "first"
        scale, diff_scale = 1.0, 100.0
        ylabel = "F(x)"
        left_title = "Функции распределения"
        diff_title = "Разность D1 = F(%s) - F(%s)" % (LABELS[a], LABELS[b])
        unit = "п.п."
    else:
        key, diff_key = "d2", "second"
        scale, diff_scale = 100.0, 100.0
        ylabel = "S(x), %"
        left_title = "Интегралы функций распределения"
        diff_title = "Разность D2 = S(%s) - S(%s)" % (LABELS[a], LABELS[b])
        unit = "п.п."

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(16.5 / 2.54, 4.6 / 2.54), dpi=DPI,
        gridspec_kw={"width_ratios": [1.55, 1.0]})
    fig.subplots_adjust(left=0.085, right=0.985, top=0.86, bottom=0.19,
                        wspace=0.26)

    grid = result["grid"]
    xs = [x * 100.0 for x in grid]
    func = ((lambda d, x: d.F(x)) if order == 1
            else (lambda d, x: d.S(x)))
    left_a = [func(result["dist_a"], x) * scale for x in grid]
    left_b = [func(result["dist_b"], x) * scale for x in grid]
    ax1.plot(xs, left_a, color=COLOR[a], lw=1.2, label=LABELS[a])
    ax1.plot(xs, left_b, color=COLOR[b], lw=1.2, ls="--", label=LABELS[b])
    ax1.set_title(left_title, fontsize=7.5, family=FONT, pad=4)
    ax1.set_ylabel(ylabel, fontsize=7, family=FONT, color="#1b1b1b")
    ax1.legend(fontsize=7, frameon=False, loc="upper left",
               prop={"family": FONT, "size": 7})

    diffs = [v * diff_scale for v in result[key]]
    ax2.axhline(0.0, color="#5b6770", lw=0.8)
    ax2.fill_between(xs, diffs, 0.0, where=[v >= 0 for v in diffs],
                     color=COLOR[a], alpha=0.20, interpolate=True)
    ax2.fill_between(xs, diffs, 0.0, where=[v < 0 for v in diffs],
                     color=COLOR[b], alpha=0.20, interpolate=True)
    ax2.plot(xs, diffs, color="#1b1b1b", lw=1.0)
    ax2.set_title(diff_title, fontsize=7.5, family=FONT, pad=4)
    ax2.set_ylabel("D, " + unit, fontsize=7, family=FONT, color="#1b1b1b")
    lo2, hi2 = ax2.get_ylim()
    ax2.set_ylim(lo2, hi2 + 0.14 * (hi2 - lo2))  # запас под подпись

    crossing = result[diff_key]["crossings"]
    if crossing:
        point = crossing[-1][0] * 100.0
        ax2.axvline(point, color="#a33", lw=0.9, ls=(0, (4, 3)), zorder=1)
        ax2.annotate("x ≈ %s %%" % ru(point, 2),
                     xy=(point, 0.97), xycoords=("data", "axes fraction"),
                     xytext=(3, -2), ha="left", va="top",
                     textcoords="offset points", fontsize=6.5,
                     family=FONT, color="#a33")

    for ax in (ax1, ax2):
        ax.set_xlim(-10.0, 10.0)
        ax.set_xlabel("дневная доходность, %", fontsize=7, family=FONT,
                      color="#1b1b1b")
        if ax is ax1:
            ticks = (-10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10)
        else:
            ticks = (-10, -5, 0, 5, 10)
        ax.set_xticks(list(ticks))
        ax.set_xticklabels([axis_pct(v) for v in ticks],
                           fontsize=6.5, family=FONT)
        ax.grid(True, color="#e3e7ec", lw=0.5)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.tick_params(labelsize=6.5)
        for label in ax.get_yticklabels():
            label.set_fontfamily(FONT)
        ax.yaxis.set_major_formatter(FuncFormatter(axis_frac))

    path = os.path.join(OUT_DIR, "dom_fig%d.png" % number)
    os.makedirs(OUT_DIR, exist_ok=True)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Листинги
# ---------------------------------------------------------------------------
CODE_DIST = """\
class Distribution:
    def __init__(self, series):
        self.edges = series["edges"]
        self.freq = series["freq"]
        self.cum = [0.0]
        for p in self.freq:
            self.cum.append(self.cum[-1] + p)

    def F(self, x):
        if x <= self.edges[0]:
            return 0.0
        if x >= self.edges[-1]:
            return 1.0
        j = bisect.bisect_right(self.edges, x) - 1
        h = self.edges[j + 1] - self.edges[j]
        return self.cum[j] + self.freq[j] * (x - self.edges[j]) / h

    def S(self, x):
        if x <= self.edges[0]:
            return 0.0
        if x >= self.edges[-1]:
            return self.full + (x - self.edges[-1])
        j = bisect.bisect_right(self.edges, x) - 1
        h = self.edges[j + 1] - self.edges[j]
        t = x - self.edges[j]
        total = sum(self.cum[i] * (self.edges[i + 1] - self.edges[i])
                    + self.freq[i] * (self.edges[i + 1] - self.edges[i]) / 2
                    for i in range(j))
        return total + self.cum[j] * t + self.freq[j] * t ** 2 / (2 * h)
"""

CODE_COMPARE = """\
def compare(dist_a, dist_b, points=1600):
    lo = min(dist_a.lo, dist_b.lo)
    hi = max(dist_a.hi, dist_b.hi)
    grid = sorted(set(dist_a.edges) | set(dist_b.edges)
                  | {lo + (hi - lo) * i / points
                     for i in range(points + 1)})
    d1 = [dist_a.F(x) - dist_b.F(x) for x in grid]
    d2 = [dist_a.S(x) - dist_b.S(x) for x in grid]
    return grid, d1, d2


def verdict(diffs, tol=1e-9):
    # D = F_A - F_B <= 0 всюду -> доминирует A
    if max(diffs) <= tol:
        return "A"
    # D >= 0 всюду -> доминирует B
    if min(diffs) >= -tol:
        return "B"
    return "нет доминирования"
"""


# ---------------------------------------------------------------------------
# Текст отчёта
# ---------------------------------------------------------------------------
def build_content(rep, dates, data, result, dists, comparisons, pairs):
    stats = {t: dominance.describe_sample(data[t]) for t in TICKERS}
    first = {p: comparisons[p]["first"] for p in pairs}
    second = {p: comparisons[p]["second"] for p in pairs}
    n = stats[TICKERS[0]]["n"]

    def label(ticker):
        return LABELS[ticker]

    def order(rows, key):
        return sorted(rows, key=lambda t: stats[t][key], reverse=True)

    by_mean = order(TICKERS, "mean")
    by_std = order(TICKERS, "std")

    # ------------------------------------------------------------------
    rep.h1("Цель работы")
    rep.p("Цель работы - изучить критерии стохастического доминирования "
          "первого и второго порядков и применить их к выбору объекта "
          "инвестирования. Сравниваются дневные доходности акций трёх "
          "фармацевтических компаний, эмпирические законы распределения "
          "которых построены в лабораторной работе №1.")
    rep.p("Вариант 3: Bayer (BAYN.DE), Merck & Co (MRK) и Sanofi (SAN.PA). "
          "Период наблюдений - с %s по %s. Для каждой пары бумаг строятся "
          "функции распределения и их разности (первый порядок), а также "
          "интегралы функций распределения и их разности (второй порядок), "
          "всего шесть рисунков. По знаку разностей делается вывод о "
          "наличии доминирования и о предпочтениях инвестора."
          % (dates[0].strftime("%d.%m.%Y"),
             dates[-1].strftime("%d.%m.%Y")))

    rep.p("Для достижения цели решаются следующие задачи:")
    rep.numbers([
        "построить по выборке дневных доходностей эмпирические функции "
        "распределения;",
        "вычислить интегралы функций распределения и попарные разности;",
        "проверить критерии доминирования первого и второго порядков;",
        "определить точки пересечения кривых и области предпочтения;",
        "сформулировать выводы о выборе бумаги.",
    ])

    # ------------------------------------------------------------------
    rep.h1("Вариант и статистические данные")
    rep.p("Используются те же данные, что и в лабораторной работе №1: "
          "скорректированные цены закрытия за два года, приведённые к общим "
          "торговым дням трёх бирж. Дневная доходность считается как "
          "X_t = (P_t - P_(t-1)) / P_(t-1) и выражается в долях; в таблицах "
          "она переведена в проценты. Каждая бумага имеет n = %d "
          "наблюдений." % n)

    rows = []
    for ticker in TICKERS:
        s = stats[ticker]
        rows.append((
            "%s (%s)" % (label(ticker), ticker),
            ru(s["mean"] * 100.0, 3),
            ru(s["std"] * 100.0, 3),
            ru(s["min"] * 100.0, 2),
            ru(s["max"] * 100.0, 2),
            ru(s["p_neg"] * 100.0, 2),
            ru(s["p_drop"] * 100.0, 2),
        ))
    rep.table(
        ("Акция", "μ, %", "σ, %", "Мин., %", "Макс., %",
         "P(X ≤ 0)", "P(X ≤ −3)"),
        rows, (2.5, 1.9, 1.9, 2.0, 2.0, 2.4, 2.5), size=10,
        caption="Таблица 1. Характеристики дневных доходностей, %")

    rep.p("Наибольшая средняя доходность у %s (%s %%), наименьшая - у %s "
          "(%s %%). По стандартному отклонению порядок такой: %s. "
          "Разброс доходностей и вероятности заметного падения убывают от "
          "Bayer к Sanofi: у Bayer выше и средняя доходность, и риск, "
          "у Sanofi ниже и то, и другое, а Merck занимает промежуточное "
          "положение. Именно поэтому выбор между бумагами нельзя сделать "
          "по одной характеристике."
          % (label(by_mean[0]), ru(stats[by_mean[0]]["mean"] * 100.0, 3),
             label(by_mean[-1]), ru(stats[by_mean[-1]]["mean"] * 100.0, 3),
             ", ".join("%s (%s %%)"
                       % (label(t), ru(stats[t]["std"] * 100.0, 3))
                       for t in by_std)))

    rep.p("Эмпирические законы распределения взяты из лабораторной работы "
          "№1: это интервальные вариационные ряды с k = %d интервалами "
          "равной длины. Каждый ряд задаёт вероятности p_j попадания "
          "доходности в интервал, поэтому по нему однозначно "
          "восстанавливается функция распределения."
          % result[TICKERS[0]]["series"]["k"])

    # ------------------------------------------------------------------
    rep.h1("Математическая постановка задачи")
    rep.p("Пусть X_A и X_B - дневные доходности двух бумаг, а F_A и F_B - "
          "их функции распределения:")
    rep.formula("F(x) = P(X ≤ x).")
    rep.p("Бумага A предпочтительнее бумаги B в смысле доминирования "
          "первого порядка, если при любом уровне доходности вероятность "
          "получить не больше этого уровня у A не выше, чем у B:")
    rep.formula("A ≽₁ B   ⇔   F_A(x) ≤ F_B(x) для всех x.")
    rep.p("Иначе говоря, распределение A целиком сдвинуто вправо: при "
          "любом x вероятность оказаться ниже x у A меньше. Это самый "
          "сильный критерий: он не зависит от вида функции полезности, "
          "если полезность возрастает.")

    rep.p("Доминирование второго порядка допускает пересечение кривых, но "
          "требует, чтобы площадь под F_A слева от любого x была не больше, "
          "чем под F_B. Вводится интеграл функции распределения:")
    rep.formula("S(x) = ∫_{−∞}^{x} F(t) dt = E[(x − X)₊].")
    rep.p("Величина S(x) равна ожидаемому недобору доходности относительно "
          "целевого уровня x и имеет размерность доходности. Критерий "
          "второго порядка записывается так:")
    rep.formula("A ≽₂ B   ⇔   S_A(x) ≤ S_B(x) для всех x.")
    rep.p("Этот критерий соответствует инвестору с возрастающей вогнутой "
          "функцией полезности, то есть несклонному к риску. Из "
          "доминирования первого порядка всегда следует доминирование "
          "второго порядка, обратное неверно. Для проверки удобно ввести "
          "разности:")
    rep.formula("D1(x) = F_A(x) − F_B(x),   D2(x) = S_A(x) − S_B(x).")
    rep.p("Если D1 ≤ 0 (D2 ≤ 0) на всей оси, то доминирует A; если "
          "D1 ≥ 0 (D2 ≥ 0) - доминирует B. Если разность меняет знак, то "
          "ни одна из бумаг не доминирует, и критерий не позволяет сделать "
          "однозначный выбор: предпочтение зависит от целевого уровня и "
          "отношения инвестора к риску.")

    # ------------------------------------------------------------------
    rep.h1("Методика расчёта")
    rep.p("Для интервального ряда функция распределения достраивается в "
          "предположении о равномерности внутри интервала:")
    rep.formula("F(x) = F_j + p_j · (x − a_j) / h_j,   x ∈ [a_j; a_j + h_j),")
    rep.p("где F_j - накопленная вероятность к началу интервала, a_j - его "
          "левая граница, h_j - длина. На каждом интервале F линейна, "
          "поэтому S вычисляется аналитически как сумма площадей "
          "трапеций и параболы. Это позволяет строить гладкие кривые и "
          "не терять информацию о положении границ интервалов.")
    rep.p("Для каждой бумаги по таблице вариационного ряда строится объект "
          "Distribution, который умеет вычислять F(x) и S(x) в любой точке. "
          "Функция распределения находится по номеру интервала, в который "
          "попадает x, а интеграл - последовательным суммированием площадей "
          "под F на предыдущих интервалах (листинг 1).")
    rep.code(CODE_DIST, size=9.0)
    rep.p("Листинг 1. Функция распределения и её интеграл по интервальному "
          "ряду")
    rep.p("Проверка критерия выполняется на общей сетке, включающей все "
          "границы интервалов обоих рядов и равномерное заполнение между "
          "ними. На таких отрезках D1 линейна, а D2 квадратична, поэтому "
          "смена знака определяется с достаточной точностью (листинг 2).")
    rep.code(CODE_COMPARE, size=9.0)
    rep.p("Листинг 2. Построение разностей и проверка критерия")
    rep.p("Точки пересечения находятся как нули разности с линейной "
          "интерполяцией между соседними узлами сетки. Дополнительно "
          "контролируются экстремумы разности: они показывают, насколько "
          "сильно одна бумага превосходит другую в той области, где это "
          "превосходство есть.")

    rows = []
    for x in THRESHOLDS:
        rows.append((ru(x * 100.0, 0),) + tuple(
            ru(dists[t].F(x), 4) for t in TICKERS))
    rep.p("Значения функций распределения в характерных точках приведены "
          "в таблице 2.")
    rep.table(
        ("Уровень x, %", "F Bayer", "F Merck", "F Sanofi"),
        rows, (3.4, 3.6, 3.6, 3.6), size=10,
        caption="Таблица 2. Значения функций распределения F(x)")
    rep.p("Например, при x = −3 %% вероятность получить такую доходность "
          "или ниже равна %s у Bayer, %s у Merck и %s у Sanofi, а при "
          "x = +3 %% - %s, %s и %s соответственно. Это отражает более тяжёлые "
          "хвосты у более волатильной бумаги."
          % (ru(dists[TICKERS[0]].F(-0.03), 3),
             ru(dists[TICKERS[1]].F(-0.03), 3),
             ru(dists[TICKERS[2]].F(-0.03), 3),
             ru(dists[TICKERS[0]].F(0.03), 3),
             ru(dists[TICKERS[1]].F(0.03), 3),
             ru(dists[TICKERS[2]].F(0.03), 3)))

    # ------------------------------------------------------------------
    rep.h1("Доминирование первого порядка")
    rep.p("На рисунках 1-3 показаны попарные функции распределения и их "
          "разности D1 = F_A - F_B. Ось абсцисс ограничена диапазоном "
          "−10...+10 %: за его пределами кривые практически совпадают, а "
          "проверка критерия выполнена на всей области значений выборки. "
          "Если разность положительна, то F_A > F_B, то есть при данном "
          "уровне доходности A чаще оказывается ниже уровня и потому хуже. "
          "Отрицательная разность означает, что A лучше.")

    for index, (a, b) in enumerate(pairs):
        item = comparisons[(a, b)]
        item = dict(item, dist_a=dists[a], dist_b=dists[b])
        path = chart_pair(a, b, item, 1, index + 1)
        IMG[(a, b, 1)] = path
        f, s = first[(a, b)], item["first"]
        cross = s["crossings"][-1][0] if s["crossings"] else None
        rep.p("Пара %s - %s (рисунок %d). Разность D1 = F(%s) - F(%s) "
              "достигает максимума %s п.п. при x = %s %%: в этой области "
              "уровень доходности чаще не достигается у %s. Минимум %s п.п. "
              "достигается при x = %s %%: здесь, наоборот, преимущество у "
              "%s. Кривые пересекаются вблизи нуля, причём разность меняет "
              "знак несколько раз (последнее пересечение - при x ≈ %s %%), "
              "поэтому %s не доминирует над %s по первому порядку."
              % (label(a), label(b), index + 1, label(a), label(b),
                 ru(f["max"] * 100.0, 2), ru(f["argmax"] * 100.0, 2),
                 label(a),
                 ru(f["min"] * 100.0, 2), ru(f["argmin"] * 100.0, 2),
                 label(a),
                 ru(cross * 100.0, 2) if cross is not None else "-",
                 label(a), label(b)))
        rep.figure(path, "Рисунок %d. Функции распределения и их разность "
                   "для пары %s - %s (первый порядок)"
                   % (index + 1, label(a), label(b)), width_cm=16.5)

    rep.p("Во всех трёх парах картина одинакова по смыслу: в области "
          "убытков разность в среднем положительна, в области прибыли - "
          "отрицательна. Это означает, что более волатильная бумага хуже "
          "защищает от падений, но даёт больше шансов на сильный рост. "
          "Ни одна кривая не лежит ниже другой на всей оси, поэтому "
          "доминирование первого порядка отсутствует во всех парах.")
    rows = []
    for (a, b) in pairs:
        s = first[(a, b)]
        cross = s["crossings"][-1][0] if s["crossings"] else None
        rows.append((
            "%s - %s" % (label(a), label(b)),
            ru(s["max"] * 100.0, 2),
            ru(s["argmax"] * 100.0, 2),
            ru(s["min"] * 100.0, 2),
            ru(s["argmin"] * 100.0, 2),
            ru(cross * 100.0, 2) if cross is not None else "-",
            "нет",
        ))
    rep.table(
        ("Пара", "max D1, п.п.", "при x, %", "min D1, п.п.", "при x, %",
         "пересечение, %", "вывод"),
        rows, (2.5, 2.2, 1.9, 2.2, 1.9, 2.7, 2.1), size=9,
        caption="Таблица 3. Проверка доминирования первого порядка")
    # ------------------------------------------------------------------
    rep.h1("Доминирование второго порядка")
    rep.p("На рисунках 4-6 показаны интегралы функций распределения S(x) и "
          "их разности D2 = S_A - S_B. Величина S(x) измеряется в процентах "
          "доходности и равна ожидаемому недобору относительно уровня x. "
          "Положительная разность D2 означает, что ожидаемый недобор у A "
          "больше, то есть A хуже; отрицательная - что A лучше. Итоги проверки сведены "
          "в таблицу 4.")

    rows = []
    for (a, b) in pairs:
        s = second[(a, b)]
        cross = s["crossings"][-1][0] if s["crossings"] else None
        rows.append((
            "%s - %s" % (label(a), label(b)),
            ru(s["max"] * 100.0, 3),
            ru(s["argmax"] * 100.0, 2),
            ru(s["min"] * 100.0, 3),
            ru(s["argmin"] * 100.0, 2),
            ru(cross * 100.0, 2) if cross is not None else "-",
            "нет",
        ))
    rep.table(
        ("Пара", "max D2, п.п.", "при x, %", "min D2, п.п.", "при x, %",
         "пересечение, %", "вывод"),
        rows, (2.5, 2.2, 1.9, 2.2, 1.9, 2.7, 2.1), size=9,
        caption="Таблица 4. Проверка доминирования второго порядка")


    for index, (a, b) in enumerate(pairs):
        item = comparisons[(a, b)]
        item = dict(item, dist_a=dists[a], dist_b=dists[b])
        path = chart_pair(a, b, item, 2, index + 4)
        IMG[(a, b, 2)] = path
        f, s = second[(a, b)], item["second"]
        cross = s["crossings"][-1][0] if s["crossings"] else None
        rep.p("Пара %s - %s (рисунок %d). Разность D2 = S(%s) - S(%s) "
              "положительна на большей части оси до x ≈ %s %% (максимум %s п.п. "
              "при x = %s %%), "
              "следовательно при любом целевом уровне ниже этой точки "
              "ожидаемый недобор меньше у %s. Правее разность "
              "отрицательна (минимум %s п.п. при x = %s %%), и "
              "предпочтительнее становится %s. Однократная смена знака "
              "означает отсутствие доминирования второго порядка."
              % (label(a), label(b), index + 4, label(a), label(b),
                 ru(cross * 100.0, 2) if cross is not None else "-",
                 ru(f["max"] * 100.0, 3), ru(f["argmax"] * 100.0, 2),
                 label(b),
                 ru(f["min"] * 100.0, 3), ru(f["argmin"] * 100.0, 2),
                 label(a)))
        rep.figure(path, "Рисунок %d. Интегралы функций распределения и их "
                   "разность для пары %s - %s (второй порядок)"
                   % (index + 4, label(a), label(b)), width_cm=16.5)

    rep.p("Смена знака происходит при x ≈ 3,1 % во всех парах. Причина "
          "в том, что при больших x интеграл ведёт себя как S(x) ≈ x − μ: "
          "преимущество получает бумага с большей средней доходностью. При "
          "малых x решает форма левого хвоста, поэтому в области убытков "
          "порядок предпочтений обратен порядку по средней доходности. "
          "В далёком левом хвосте (x < −3 %) знак также меняется, но там "
          "значения S малы и на вывод не влияют.")
    # ------------------------------------------------------------------
    rep.h1("Выводы")
    rep.p("В работе построены эмпирические функции распределения дневных "
          "доходностей трёх акций и их интегралы, для каждой из трёх пар "
          "найдены разности D1 и D2. По знаку разностей проверены критерии "
          "стохастического доминирования первого и второго порядков.")
    rep.numbers([
        "Доминирование первого порядка отсутствует во всех парах: "
        "функции распределения попарно пересекаются вблизи нулевой "
        "доходности. Левее точки пересечения лучше бумага с меньшим "
        "риском, правее - с большей средней доходностью.",
        "Доминирование второго порядка также отсутствует: разность "
        "интегралов меняет знак при x ≈ 3,1 % в день. Ни одна бумага не "
        "предпочтительнее другой при любом целевом уровне доходности.",
        "В окрестности нуля (примерно от −3 % до 3 %), где сосредоточена "
        "основная масса наблюдений, порядок предпочтений такой: Sanofi, "
        "Merck, Bayer; в области высокой доходности порядок обратный: "
        "Bayer, Merck, Sanofi. Это согласуется с характеристиками "
        "таблицы 1: у Bayer наибольшая средняя доходность и наибольший "
        "риск, у Sanofi - наименьший.",
        "Критерии стохастического доминирования упорядочивают бумаги "
        "только частично. Поскольку ни одна пара не упорядочена "
        "однозначно, окончательный выбор зависит от отношения инвестора "
        "к риску и от целевого уровня доходности.",
    ])
    rep.p("Практический вывод: консервативному инвестору, который "
          "минимизирует вероятность и глубину убытков, следует выбрать "
          "Sanofi; инвестору, ориентированному на высокую доходность и "
          "готовому принять тяжёлые хвосты, - Bayer; Merck является "
          "компромиссным вариантом. Таким образом, стохастическое "
          "доминирование даёт корректный, но неполный ответ, и для "
          "окончательного решения его нужно дополнять мерами риска из "
          "лабораторной работы №1 или функцией полезности.")


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
    build_content(rep, dates, data, result, dists, comparisons, pairs)
    return rep.save()


if __name__ == "__main__":
    print(build())
