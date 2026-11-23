# -*- coding: utf-8 -*-
"""Лабораторная работа №3, дисциплина «Принятие решений в условиях
неопределённости».

Тема: ожидаемая полезность. Дневные доходности трёх акций фармацевтических
компаний (Bayer, Merck & Co, Sanofi) сравниваются по критерию ожидаемой
полезности Vu(X) = E[u(X)] с двумя функциями полезности: аналитической
функцией варианта 3, u(x) = x^(1/5), и эмпирической функцией, построенной
по точкам и восстановленной монотонным кубическим сплайном.

Расчётная часть вынесена в ``labs/utility.py``: здесь только рисунки,
таблицы и текст. Все числа считаются при сборке отчёта.

Запуск:  python build.py --lab risk3
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from labkit.docxgen import Report, ReportMeta
from labkit.schemes import DPI, FONT

from labs import dominance, risk_data, risk_measures, utility

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(HERE, "out")

PAGE_TITLE = "ОЖИДАЕМАЯ\nПОЛЕЗНОСТЬ"
SHORT_TITLE = ("Ожидаемая полезность на примере акций фармацевтических "
               "компаний")
FRAME_TITLE = "Ожидаемая полезность"
OUT_NAME = "Воробьев_И_С_отчет_по_3_ЛР_Ожидаемая_полезность.docx"

TICKERS = risk_data.TICKERS
LABELS = {"BAYN.DE": "Bayer", "MRK": "Merck", "SAN.PA": "Sanofi"}
COLOR = {"BAYN.DE": "#1f4e79", "MRK": "#b06a2c", "SAN.PA": "#2e7d32"}
ARA_POINTS = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0)

MINUS = "\u2212"


# ---------------------------------------------------------------------------
# Форматирование чисел в русской записи
# ---------------------------------------------------------------------------
def ru(value, digits=2):
    """Число с запятой в дробной части и пробелом между разрядами."""
    text = ("{:,.%df}" % digits).format(value)
    text = text.replace(",", "\u00a0").replace(".", ",")
    return text.replace("-", MINUS)


def pct(value, digits=2):
    """Значение в процентах с единицей измерения."""
    return ru(value, digits) + " %"


def axis_pct(value, _pos=None):
    return ("%.0f" % value).replace("-", MINUS)


def dev(value, base):
    """Отклонение от базового значения в процентах."""
    return (value - base) / abs(base) * 100.0


def best_of(values):
    """Ключ с наибольшим значением в словаре."""
    return max(values, key=values.get)


def best(rows, idx):
    """Бумага с максимальным значением колонки ``idx`` (0 - Vu, 1 - Vu_emp)."""
    return max(rows, key=lambda t: rows[t][idx])


def rank(values):
    """Места бумаг: 1 - наибольшая ожидаемая полезность."""
    order = sorted(values, key=values.get, reverse=True)
    return {t: order.index(t) + 1 for t in values}


# ---------------------------------------------------------------------------
# Оформление осей
# ---------------------------------------------------------------------------
def style(ax, ticks=(-10, -5, 0, 5, 10, 15)):
    ax.grid(True, color="#e3e7ec", lw=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=6.5)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(FONT)
    if ticks:
        ax.set_xticks(list(ticks))
        ax.set_xticklabels([axis_pct(v) for v in ticks], fontsize=6.5,
                           family=FONT)


def canvas(height):
    """Пара полей 1,45:1 шириной 16,5 см."""
    fig, axes = plt.subplots(
        1, 2, figsize=(16.5 / 2.54, height / 2.54), dpi=DPI,
        gridspec_kw={"width_ratios": [1.45, 1.0]})
    fig.subplots_adjust(left=0.085, right=0.985, top=0.87, bottom=0.21,
                        wspace=0.27)
    return fig, axes


def single(height):
    fig, ax = plt.subplots(figsize=(16.5 / 2.54, height / 2.54), dpi=DPI)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.88, bottom=0.21)
    return fig, ax


# ---------------------------------------------------------------------------
# Рисунки
# ---------------------------------------------------------------------------
def chart_utility(r):
    """Рисунок 1: функция варианта и её несклонность к риску."""
    lo, hi = r["lo"], r["hi"]
    u_var = utility.normalize(utility.power_utility, lo, hi)
    count = 400
    grid = [lo + (hi - lo) * i / count for i in range(count + 1)]

    fig, (ax1, ax2) = canvas(6.2)
    ax1.plot(grid, [u_var(x) for x in grid], color=COLOR["BAYN.DE"], lw=1.3)
    ax1.axhline(0.5, color="#a33", lw=0.8, ls=(0, (4, 3)))
    ax1.set_title("Функция полезности варианта", fontsize=7.5, family=FONT,
                  pad=4)
    ax1.set_xlabel("дневная доходность, %", fontsize=7, family=FONT,
                   color="#1b1b1b")
    ax1.set_ylabel("нормированная u(x)", fontsize=7, family=FONT,
                   color="#1b1b1b")
    ax1.set_xlim(lo - 0.5, hi + 0.5)
    ax1.set_ylim(-0.04, 1.06)
    style(ax1, (-10, -5, 0, 5, 10, 15))

    wide = [0.4 + (12.0 - 0.4) * i / 300 for i in range(301)]
    ax2.plot(wide, [utility.absolute_risk_aversion(x) for x in wide],
             color=COLOR["MRK"], lw=1.3)
    for x in ARA_POINTS:
        y = utility.absolute_risk_aversion(x)
        ax2.plot([x], [y], "o", ms=4, color=COLOR["MRK"])
        ax2.annotate(ru(y, 2), xy=(x, y), xytext=(4, 3),
                     textcoords="offset points", fontsize=6,
                     family=FONT, color="#1b1b1b")
    ax2.set_title("Несклонность к риску ARA(x) = 0,8 / |x|", fontsize=7.5,
                  family=FONT, pad=4)
    ax2.set_xlabel("дневная доходность, %", fontsize=7, family=FONT,
                   color="#1b1b1b")
    ax2.set_ylabel("ARA(x), 1/п.п.", fontsize=7, family=FONT, color="#1b1b1b")
    ax2.set_xlim(0.0, 12.0)
    ax2.set_ylim(0.0, 2.0)
    ax2.set_xticks([0, 2, 4, 6, 8, 10, 12])
    ax2.set_xticklabels([axis_pct(v) for v in ax2.get_xticks()], fontsize=6.5,
                        family=FONT)
    ax2.grid(True, color="#e3e7ec", lw=0.5)
    ax2.set_axisbelow(True)
    for side in ("top", "right"):
        ax2.spines[side].set_visible(False)
    ax2.tick_params(labelsize=6.5)

    path = os.path.join(OUT_DIR, "util_fig1.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def chart_empirical(r):
    """Рисунок 2: точки эмпирической полезности и интерполяция."""
    lo, hi = r["lo"], r["hi"]
    u_var = utility.normalize(utility.power_utility, lo, hi)
    count = 400
    grid = [lo + (hi - lo) * i / count for i in range(count + 1)]

    fig, ax = single(6.6)
    ax.plot(grid, [r["u_emp"](x) for x in grid], color=COLOR["SAN.PA"], lw=1.4,
            label="эмпирическая полезность, сплайн")
    ax.plot([p[0] for p in r["knots"]], [p[1] for p in r["knots"]], "o",
            ms=4.5, color=COLOR["SAN.PA"], label="точки по процедуре опроса")
    ax.plot(grid, [u_var(x) for x in grid], color=COLOR["MRK"], lw=1.0,
            ls=(0, (4, 3)), label="функция варианта, u = x^0,2")
    ax.axhline(0.5, color="#a33", lw=0.8, ls=(0, (2, 3)))
    half = [p[0] for p in r["knots"] if abs(p[1] - 0.5) < 1e-9][0]
    ax.annotate("u = 0,5 при x = %s %%" % ru(half, 2),
                xy=(half, 0.5), xytext=(6, -18), textcoords="offset points",
                va="top", fontsize=6.5, family=FONT, color="#a33",
                arrowprops={"arrowstyle": "-", "color": "#a33", "lw": 0.7})
    ax.set_title("Эмпирическая функция полезности", fontsize=7.5, family=FONT,
                 pad=4)
    ax.set_xlabel("дневная доходность, %", fontsize=7, family=FONT,
                  color="#1b1b1b")
    ax.set_ylabel("u(x)", fontsize=7, family=FONT, color="#1b1b1b")
    ax.set_xlim(lo - 0.5, hi + 0.5)
    ax.set_ylim(-0.04, 1.06)
    ax.legend(fontsize=6.5, frameon=False, loc="lower right",
              prop={"family": FONT, "size": 6.5})
    style(ax, (-10, -5, 0, 5, 10, 15))

    path = os.path.join(OUT_DIR, "util_fig2.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def chart_criteria(r):
    """Рисунок 3: значения критериев по бумагам."""
    positions = list(range(len(TICKERS)))
    fig, (ax1, ax2) = canvas(6.2)

    for ax, values, title in ((ax1, r["vu"], "Критерий Vu(X)"),
                              (ax2, r["vu_emp"], "Критерий Vu эмп(X)")):
        heights = [values[t] for t in TICKERS]
        bars = ax.bar(positions, heights, width=0.55,
                      color=[COLOR[t] for t in TICKERS])
        span = max(heights) - min(heights)
        bottom = min(heights) - 0.45 * span
        top = max(heights) + 0.25 * span
        for bar, t in zip(bars, TICKERS):
            ax.annotate(ru(values[t], 4),
                        xy=(bar.get_x() + bar.get_width() / 2.0,
                            values[t]),
                        xytext=(0, 2), textcoords="offset points",
                        ha="center", va="bottom", fontsize=6.2, family=FONT)
        ax.set_title(title, fontsize=7.5, family=FONT, pad=4)
        ax.set_ylabel("%s, шкала обрезана" % ("Vu" if ax is ax1 else "Vu эмп"),
                      fontsize=7, family=FONT, color="#1b1b1b")
        ax.set_ylim(bottom, top)
        ax.set_xticks(positions)
        ax.set_xticklabels([LABELS[t] for t in TICKERS], fontsize=7,
                           family=FONT)
        ax.tick_params(labelsize=6.5)
        ax.grid(True, axis="y", color="#e3e7ec", lw=0.5)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    fig.savefig(os.path.join(OUT_DIR, "util_fig3.png"), facecolor="white")
    plt.close(fig)
    return os.path.join(OUT_DIR, "util_fig3.png")


def chart_sensitivity(r):
    """Рисунок 4: зависимости Vu и Vu_emp от числа интервалов k."""
    ks = r["ks"]
    fig, axes = plt.subplots(
        1, 2, figsize=(16.5 / 2.54, 6.4 / 2.54), dpi=DPI,
        gridspec_kw={"width_ratios": [1.0, 1.0]})
    fig.subplots_adjust(left=0.085, right=0.985, top=0.88, bottom=0.20,
                        wspace=0.22)
    ax1, ax2 = axes

    for idx, ax, title in ((0, ax1, "Критерий Vu(X)"),
                           (1, ax2, "Критерий Vu эмп(X)")):
        for t in TICKERS:
            ax.plot(ks, [r["sens"][k][t][idx] for k in ks], "o-",
                    ms=3.2, lw=1.2, color=COLOR[t], label=LABELS[t])
        ax.axvline(r["k0"], color="#a33", lw=0.9, ls=(0, (4, 3)))
        ax.set_title(title, fontsize=7.5, family=FONT, pad=4)
        ax.set_xlabel("число интервалов k", fontsize=7, family=FONT,
                      color="#1b1b1b")
        ax.set_xticks(list(ks))
        ax.set_xticklabels([str(k) for k in ks], fontsize=6, family=FONT)
        ax.tick_params(labelsize=6.5)
        ax.grid(True, color="#e3e7ec", lw=0.5)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    ax1.set_ylabel("Vu", fontsize=7, family=FONT, color="#1b1b1b")
    ax2.set_ylabel("Vu эмп", fontsize=7, family=FONT, color="#1b1b1b")
    ax2.legend(fontsize=6.5, frameon=False, loc="lower right",
               prop={"family": FONT, "size": 6.5}, ncol=3)
    fig.savefig(os.path.join(OUT_DIR, "util_fig4.png"), facecolor="white")
    plt.close(fig)
    return os.path.join(OUT_DIR, "util_fig4.png")


# ---------------------------------------------------------------------------
# Листинги
# ---------------------------------------------------------------------------
CODE_INTEGRAL = """\ndef power_integral(a, b):
    def antiderivative(x):
        return math.copysign(abs(x) ** (POWER + 1.0), x) / (POWER + 1.0)
    return antiderivative(b) - antiderivative(a)


def interval_integral(func, a, b):
    exact = getattr(func, "integral", None)
    if exact is not None:
        return exact(a, b)
    if func is power_utility:
        return power_integral(a, b)
    center, half = 0.5 * (a + b), 0.5 * (b - a)
    acc = 0.0
    for node, weight in zip(GAUSS_X, GAUSS_W):
        acc += weight * func(center + half * node)
    return 0.5 * half * acc


def expected_utility(series, func, scale=100.0):
    total = 0.0
    for j, p in enumerate(series["freq"]):
        a = series["edges"][j] * scale
        b = series["edges"][j + 1] * scale
        total += p * interval_integral(func, a, b) / (b - a)
    return total
"""

CODE_KNOTS = """\
def power_utility(x):
    if x == 0.0:
        return 0.0
    return math.copysign(abs(x) ** POWER, x)


def absolute_risk_aversion(x):
    return (1.0 - POWER) / abs(x)


def certainty_equivalent(a, b, lam=LAMBDA):
    target = 0.5 * (math.exp(-lam * a) + math.exp(-lam * b))
    return -math.log(max(target, 1e-300)) / lam


def utility_knots(lo, hi, lam=LAMBDA, levels=KNOT_LEVELS):
    points = [(lo, 0.0), (hi, 1.0)]
    queue = [(lo, hi, 0.0, 1.0)]
    for _ in range(int(math.log2(levels))):
        nxt = []
        for a, b, ua, ub in queue:
            m = certainty_equivalent(a, b, lam)
            um = 0.5 * (ua + ub)
            points.append((m, um))
            nxt.append((a, m, ua, um))
            nxt.append((m, b, um, ub))
        queue = nxt
    points.sort()
    return points
"""

CODE_SPLINE = """\
class InterpolatedUtility:
    def __init__(self, points):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        n = len(xs)
        d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i])
             for i in range(n - 1)]
        m = [0.0] * n
        m[0], m[-1] = d[0], d[-1]
        for i in range(1, n - 1):
            if d[i - 1] * d[i] <= 0.0:
                m[i] = 0.0
            else:
                w1 = 2.0 * (xs[i + 1] - xs[i]) + (xs[i] - xs[i - 1])
                w2 = (xs[i + 1] - xs[i]) + 2.0 * (xs[i] - xs[i - 1])
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        self.xs, self.ys, self.ms = xs, ys, m

    def __call__(self, x):
        xs, ys, ms = self.xs, self.ys, self.ms
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = bisect.bisect_right(xs, x) - 1
        h = xs[i + 1] - xs[i]
        t = (x - xs[i]) / h
        return ((2 * t ** 3 - 3 * t ** 2 + 1) * ys[i]
                + (t ** 3 - 2 * t ** 2 + t) * h * ms[i]
                + (-2 * t ** 3 + 3 * t ** 2) * ys[i + 1]
                + (t ** 3 - t ** 2) * h * ms[i + 1])

    def integral(self, a, b):
        bounds = [a] + [x for x in self.xs if a < x < b] + [b]
        total = 0.0
        for left, right in zip(bounds, bounds[1:]):
            mid = 0.5 * (left + right)
            total += (right - left) / 6.0 * (self(left) + 4.0 * self(mid)
                                             + self(right))
        return total
"""


# ---------------------------------------------------------------------------
# Оценка ошибки квадратуры для середины интервала
# ---------------------------------------------------------------------------
def midpoint_error(series, func):
    """Максимальное расхождение метода середин и квадратуры."""
    total = 0.0
    for j, p in enumerate(series["freq"]):
        a = series["edges"][j] * 100.0
        b = series["edges"][j + 1] * 100.0
        total += p * func(0.5 * (a + b))
    return abs(total - utility.expected_utility(series, func))


# ---------------------------------------------------------------------------
# Текст отчёта
# ---------------------------------------------------------------------------
def build_content(rep, dates, data, r):
    stats = {t: dominance.describe_sample(data[t]) for t in TICKERS}
    n = stats[TICKERS[0]]["n"]
    k0 = r["k0"]
    vu, vu_emp, ce = r["vu"], r["vu_emp"], r["ce"]
    leader_vu = best_of(vu)
    leader_emp = best_of(vu_emp)
    place_vu = rank(vu)
    place_emp = rank(vu_emp)
    worst_vu = min(TICKERS, key=lambda t: vu[t])
    worst_emp = min(TICKERS, key=lambda t: vu_emp[t])

    def lab(t):
        return LABELS[t]

    # ------------------------------------------------------------------
    rep.h1("Цель работы")
    rep.p("Цель работы - изучить критерий ожидаемой полезности и применить "
          "его к задаче выбора объекта инвестирования. Сравниваются дневные "
          "доходности акций трёх фармацевтических компаний, эмпирические "
          "распределения которых построены в лабораторной работе №1, а "
          "свойства проверены в лабораторной работе №2.")
    rep.p("Вариант 3: Bayer (BAYN.DE), Merck & Co (MRK) и Sanofi (SAN.PA). "
          "Период наблюдений - с %s по %s, всего n = %d общих торговых дней. "
          "Номер варианта нечётный, поэтому используется функция полезности "
          "u(x) = x^(1/(n+2)) = x^0,2, где n - номер варианта. Помимо "
          "аналитической функции строится эмпирическая функция полезности по "
          "точкам и выполняется анализ чувствительности критерия к числу "
          "интервалов вариационного ряда."
          % (dates[0].strftime("%d.%m.%Y"), dates[-1].strftime("%d.%m.%Y"),
             n))
    rep.p("Для достижения цели решаются следующие задачи:")
    rep.numbers([
        "построить интервальные вариационные ряды дневных доходностей с "
        "исходным числом интервалов k = %d;" % k0,
        "записать функцию полезности варианта, найти её производные и "
        "показатель несклонности к риску;",
        "вычислить ожидаемую полезность Vu(X) для каждой бумаги и "
        "проранжировать альтернативы;",
        "построить эмпирическую функцию полезности по точкам, "
        "интерполировать её и повторить сравнение;",
        "выполнить анализ чувствительности результатов к числу интервалов "
        "k и сопоставить выводы двух критериев.",
    ])

    # ------------------------------------------------------------------
    rep.h1("Вариант и статистические данные")
    rep.p("Используются те же данные, что и в предыдущих работах: "
          "скорректированные цены закрытия за два года, приведённые к общим "
          "торговым дням трёх бирж. Дневная доходность считается как "
          "X_t = (P_t - P_(t-1)) / P_(t-1). В таблицах и формулах она "
          "выражена в процентах: функция полезности варианта u(x) = x^0,2 "
          "определена на процентной шкале, и переход к долям изменил бы не "
          "только значения критерия, но и порядок альтернатив.")
    rep.p("Для каждой бумаги выборка из n = %d значений разбита на k = %d "
          "интервалов равной длины (правило Стерджиса k = 1 + 3,322·lg n). "
          "Ширина интервала составляет %s п.п. у Bayer, %s п.п. у Merck и "
          "%s п.п. у Sanofi. Внутри интервала распределение считается "
          "равномерным - так же, как при построении эмпирических функций "
          "распределения в лабораторной работе №2."
          % (n, k0,
             ru(r["series"][TICKERS[0]]["h"] * 100.0, 2),
             ru(r["series"][TICKERS[1]]["h"] * 100.0, 2),
             ru(r["series"][TICKERS[2]]["h"] * 100.0, 2)))

    rep.p("Сводные характеристики выборок приведены в таблице 1; "
          "вероятности P(X ≤ 0) и P(X ≤ −3) считаются по эмпирическому "
          "распределению и показывают, как часто дневная доходность "
          "оказывается неположительной и падает сильнее трёх процентов.")
    rows = []
    for t in TICKERS:
        s = stats[t]
        rows.append((
            lab(t),
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
        rows, (2.2, 2.1, 2.1, 2.1, 2.1, 2.45, 2.45), size=10,
        caption="Таблица 1. Характеристики дневных доходностей "
                "Bayer, Merck и Sanofi, %")

    rep.p("Средняя доходность убывает от Bayer (%s %%) к Merck (%s %%) и "
          "Sanofi (%s %%), и в том же порядке убывает стандартное "
          "отклонение: %s, %s и %s %%. Вероятность нулевой или "
          "отрицательной доходности у Bayer выше, чем у Sanofi, и "
          "вероятность падения более чем на 3 %% также выше: %s %% против "
          "%s %%. Таким образом, выбор связан с компромиссом между "
          "средней доходностью и риском, и для его разрешения нужен "
          "критерий, учитывающий отношение инвестора к риску."
          % (ru(stats[TICKERS[0]]["mean"] * 100.0, 3),
             ru(stats[TICKERS[1]]["mean"] * 100.0, 3),
             ru(stats[TICKERS[2]]["mean"] * 100.0, 3),
             ru(stats[TICKERS[0]]["std"] * 100.0, 3),
             ru(stats[TICKERS[1]]["std"] * 100.0, 3),
             ru(stats[TICKERS[2]]["std"] * 100.0, 3),
             ru(stats[TICKERS[0]]["p_drop"] * 100.0, 2),
             ru(stats[TICKERS[2]]["p_drop"] * 100.0, 2)))

    # ------------------------------------------------------------------
    rep.h1("Постановка задачи")
    rep.p("Пусть X - дневная доходность бумаги в процентах, а u(x) - функция "
          "полезности денежного результата. Критерий ожидаемой полезности "
          "сопоставляет случайной величине число")
    rep.formula("Vu(X) = E[u(X)] = ∫ u(x) dF(x).")
    rep.p("Альтернатива с большим Vu предпочтительнее. Если распределение "
          "задано интервальным рядом с границами a_j и частотами p_j, то при "
          "равномерности внутри интервала интеграл распадается на сумму")
    rep.formula("Vu(X) = Σ_j p_j · (1 / h_j) · ∫ u(x) dx,   x ∈ [a_j; a_j+1],")
    rep.p("где h_j - длина j-го интервала. Критерий является частным случаем "
          "принципа максимизации ожидаемой полезности и обобщает сравнение "
          "по среднему: при линейной u он совпадает с математическим "
          "ожиданием, а при вогнутой u учитывает и разброс.")
    rep.p("Для варианта 3 (нечётный номер, n = 3) функция полезности имеет "
          "вид нечётного корня:")
    rep.formula("u(x) = x^(1/(n+2)) = x^0,2,   u(x) = sign(x)·|x|^0,2.")
    rep.p("Функция возрастает и вогнута на положительной полуоси, поэтому "
          "инвестор несклонен к риску. Её производные равны "
          "u′(x) = 0,2·|x|^(−0,8) и u″(x) = −0,16·|x|^(−1,8), а показатель "
          "абсолютной несклонности к риску (Arrow-Pratt)")
    rep.formula("ARA(x) = −u″(x) / u′(x) = 0,8 / |x|")
    rep.p("убывает по модулю аргумента: вблизи нуля инвестор крайне "
          "несклонен к риску, а в далёких хвостах почти нейтрален. Это "
          "свойство функции варианта и определяет её поведение в задаче: "
          "крупные отклонения доходности штрафуются слабо, поэтому критерий "
          "склонен выбирать бумагу с более широким разбросом. "
          "Нормировка полезности аффинным преобразованием не меняет "
          "порядка альтернатив, и на рисунках функция приведена к отрезку "
          "[0; 1] по формуле")
    rep.formula("ũ(x) = (u(x) − u(x_min)) / (u(x_max) − u(x_min)).")
    rep.p("Вторая функция полезности не задаётся формулой, а строится по "
          "ответам воображаемого лица, принимающего решение (ЛПР). Процедура "
          "деления пополам состоит в следующем. Крайним значениям доходности "
          "приписываются полезности u(x_min) = 0 и u(x_max) = 1. Затем для "
          "отрезка [a; b] с известными полезностями находится эквивалент "
          "уверенности CE - гарантированная доходность, столь же "
          "привлекательная, как лотерея «a с вероятностью 0,5 или b с "
          "вероятностью 0,5», - и полагается u(CE) = (u(a) + u(b)) / 2. "
          "Повторяя деление, получают точки с уровнями 0,5; 0,25 и 0,75; "
          "0,125 ... 0,875, всего девять точек.")
    rep.p("Эквивалент уверенности вычисляется для модели ЛПР с постоянной "
          "абсолютной несклонностью к риску u₀(x) = 1 − exp(−λx) аналитически:")
    rep.formula("CE = −ln((exp(−λa) + exp(−λb)) / 2) / λ,   λ = 0,2 1/п.п.")
    rep.p("Параметр λ выбран так, что при разбросе ±5 п.п. ЛПР уступает "
          "около 7 п.п. разброса, то есть модель описывает осторожного "
          "инвестора. Это модельное допущение, а не измерение: при другом "
          "λ эмпирическая функция изменится, и это отражено в обсуждении "
          "результатов. По найденным точкам функция восстанавливается "
          "монотонным кубическим сплайном Фрича-Карлсона, который не даёт "
          "колебаний между узлами.")

    # ------------------------------------------------------------------
    rep.h1("Методика расчёта")
    rep.p("Интеграл по каждому интервалу вариационного ряда считается точно, "
          "без численного приближения, и для обеих функций полезности "
          "используется своя формула. Причина в том, что подынтегральная "
          "функция в обоих случаях недостаточно гладкая: производная "
          "u(x) = x^0,2 обращается в бесконечность в нуле, а эмпирическая "
          "функция имеет изломы в узлах сплайна.")
    rep.p("Для функции варианта первообразная известна в замкнутом виде, "
          "поэтому вклад интервала [a; b] равен")
    rep.formula("∫ u(x) dx = (5/6) · (sign(b)·|b|^1,2 − sign(a)·|a|^1,2).")
    rep.p("Замена интервала его серединой здесь непригодна. Среднее значение "
          "корня по интервалу, содержащему нуль, растёт с его длиной: для "
          "симметричного интервала [−a; a] оно равно a^0,2 / 1,2, поэтому "
          "метод середин даёт ошибку того же порядка, что и само значение "
          "критерия. Расчёт показывает, что для бумаги Bayer смещение "
          "достигает %s при k = %d и %s при k = 5, то есть сопоставимо с Vu; "
          "именно поэтому интегрирование выполняется аналитически."
          % (ru(midpoint_error(r["series"][leader_vu],
                               utility.power_utility), 4), k0,
             ru(midpoint_error(
                 risk_measures.variation_series(data[leader_vu], 5),
                 utility.power_utility), 4)))
    rep.p("Интегрирование по интервальному ряду выполняет функция "
          "expected_utility; она выбирает точную первообразную, если функция "
          "полезности её предоставляет.")
    rep.code(CODE_INTEGRAL, size=8.5)
    rep.p("Листинг 1. Точное интегрирование функции полезности по "
          "интервальному ряду")
    rep.p("Функция полезности варианта записывается одной строкой, а "
          "эмпирическая функция строится по точкам. Эквивалент уверенности "
          "для модели с постоянной несклонностью к риску считается по "
          "замкнутой формуле, что делает процедуру опроса воспроизводимой.")
    rep.code(CODE_KNOTS, size=8.5)
    rep.p("Листинг 2. Функция полезности варианта, эквивалент уверенности и "
          "точки эмпирической полезности")
    rep.p("Интерполяция выполняется кубическим сплайном с ограничением "
          "наклона: если соседние наклоны имеют разный знак, производная в "
          "узле обнуляется, и функция остаётся монотонной. Благодаря этому "
          "интерполированная полезность не выходит за пределы [0; 1] и не "
          "создаёт ложной склонности к риску.")
    rep.code(CODE_SPLINE, size=8)
    rep.p("Листинг 3. Монотонный кубический сплайн и его точное "
          "интегрирование")
    rep.p("На отрезке между соседними узлами сплайн является кубическим "
          "многочленом, поэтому интеграл по такому отрезку вычисляется "
          "формулой Симпсона точно. В методе integral отрезок интегрирования "
          "разбивается по всем узлам, попавшим внутрь, и суммируются точные "
          "значения по сегментам. Такой способ не требует сетки и даёт "
          "результат, не зависящий от шага квадратуры.")
    rep.p("Оба критерия считаются на одной и той же сетке интервалов, "
          "поэтому их значения сопоставимы по составу исходных данных, но "
          "не по абсолютной величине: у функции варианта Vu может принимать "
          "значения вне отрезка [0; 1], поскольку сама u(x) = x^0,2 на "
          "используемом диапазоне доходности выходит за его пределы, а у "
          "эмпирической функции Vu лежит в [0; 1] по построению.")

    rep.h1("Критерий ожидаемой полезности Vu")
    rep.p("На рисунке 1 показана функция полезности варианта после "
          "нормировки и её показатель несклонности к риску. Кривая имеет "
          "характерный корневой вид: она круто поднимается вблизи нуля и "
          "почти выходит на плато в области больших доходностей. Правая "
          "панель показывает, что ARA падает с %s при x = 0,5 %% до %s при "
          "x = 10 %% - примерно в двадцать раз."
          % (ru(utility.absolute_risk_aversion(0.5), 2),
             ru(utility.absolute_risk_aversion(10.0), 2)))
    rep.figure(chart_utility(r),
               "Рисунок 1. Функция полезности варианта u(x) = x^0,2 и её "
               "показатель несклонности к риску ARA(x)", width_cm=16.5)

    reps = [(x, utility.absolute_risk_aversion(x)) for x in ARA_POINTS]
    rep.p("Числовые значения показателя приведены в таблице 2.")
    rep.table(
        ("x, %", "ARA(x), 1/п.п."),
        [(ru(x, 1), ru(y, 3)) for x, y in reps],
        (3.4, 3.4), size=10,
        caption="Таблица 2. Абсолютная несклонность к риску функции варианта")
    rep.p("Значения Vu(X) при исходном числе интервалов k = %d равны: "
          "%s у Bayer, %s у Merck и %s у Sanofi. По критерию ожидаемой "
          "полезности первой оказывается бумага %s, последней - %s. Разрыв "
          "между лидером и аутсайдером составляет %s, то есть около %s %% "
          "от значения лидера."
          % (k0, ru(vu[TICKERS[0]], 5), ru(vu[TICKERS[1]], 5),
             ru(vu[TICKERS[2]], 5), lab(leader_vu), lab(worst_vu),
             ru(vu[leader_vu] - vu[worst_vu], 5),
             ru((vu[leader_vu] - vu[worst_vu]) / abs(vu[leader_vu]) * 100.0,
                1)))
    rep.p("Такой результат объясняется видом функции: поскольку ARA "
          "убывает с ростом |x|, далёкие хвосты распределения почти не "
          "штрафуются, а вклад в критерий определяется главным образом "
          "областью вблизи нуля и правым хвостом. У Bayer самый широкий "
          "диапазон доходности (от %s до %s %%) и заметная положительная "
          "асимметрия, поэтому крупный выигрыш перевешивает столь же крупный "
          "проигрыш. Критерий с функцией x^0,2 фактически поощряет "
          "асимметрию: при почти линейном поведении в хвостах он близок к "
          "сравнению по среднему, но дополнительно усиливает вклад "
          "небольших положительных отклонений."
          % (ru(stats[TICKERS[0]]["min"] * 100.0, 2),
             ru(stats[TICKERS[0]]["max"] * 100.0, 2)))

    # ------------------------------------------------------------------
    rep.h1("Эмпирическая функция полезности")
    rep.p("Точки эмпирической полезности, полученные процедурой деления "
          "пополам при λ = 0,2, приведены в таблице 3. Шкала аргумента - "
          "общая для всех трёх бумаг: от минимального наблюдения Bayer "
          "(%s %%) до максимального (%s %%), поэтому функции полезности "
          "сопоставимы между собой."
          % (ru(r["lo"], 2), ru(r["hi"], 2)))
    rep.table(
        ("x, %", "u(x)", "Уровень"),
        [(ru(x, 2), ru(u, 4), ("минимум" if i == 0 else
                               "максимум" if i == len(r["knots"]) - 1 else
                               "точка деления"))
         for i, (x, u) in enumerate(r["knots"])],
        (3.4, 3.4, 4.4), size=10,
        caption="Таблица 3. Точки эмпирической функции полезности")
    rep.p("На рисунке 2 точки нанесены маркерами, а сплошная линия - "
          "результат интерполяции. Функция резко вогнута: полезность "
          "половины шкалы достигается уже при x = %s %%, а последняя восьмая "
          "часть полезности приходится на диапазон от %s до %s %%. Иными "
          "словами, "
          "для ЛПР умеренный убыток почти так же неприятен, как большой, а "
          "дополнительный выигрыш сверх нескольких процентов ценится слабо. "
          "Пунктиром показана функция варианта: при отрицательных "
          "доходностях она лежит заметно выше эмпирической, то есть "
          "аналитическая функция недооценивает неприятие убытков."
          % (ru([p[0] for p in r["knots"] if abs(p[1] - 0.5) < 1e-9][0], 2),
             ru([p[0] for p in r["knots"] if abs(p[1] - 0.875) < 1e-9][0], 2),
             ru(r["hi"], 2)))
    rep.figure(chart_empirical(r),
               "Рисунок 2. Точки эмпирической функции полезности и её "
               "интерполяция", width_cm=16.5)
    rep.p("Ожидаемая полезность по эмпирической функции при k = %d равна "
          "%s у Bayer, %s у Merck и %s у Sanofi: первой оказывается бумага "
          "%s, последней - %s. Эквивалент уверенности, то есть "
          "гарантированная доходность с той же полезностью, составляет "
          "%s %% у Bayer, %s %% у Merck и %s %% у Sanofi. Отрицательные "
          "значения означают, что при выбранной шкале предпочтений ЛПР "
          "оценивает дневную лотерею ниже гарантированного небольшого "
          "убытка: несклонность к риску настолько велика, что риск не "
          "компенсируется средней доходностью."
          % (k0, ru(vu_emp[TICKERS[0]], 5), ru(vu_emp[TICKERS[1]], 5),
             ru(vu_emp[TICKERS[2]], 5), lab(leader_emp), lab(worst_emp),
             ru(ce[TICKERS[0]], 3), ru(ce[TICKERS[1]], 3),
             ru(ce[TICKERS[2]], 3)))
    rep.p("Разрыв между Merck и Sanofi по эквиваленту уверенности "
          "составляет всего %s п.п., но он устойчив: Sanofi имеет меньшую "
          "дисперсию, а при сильной вогнутости полезности именно разброс, а "
          "не средняя доходность определяет оценку."
          % ru(abs(ce[TICKERS[1]] - ce[TICKERS[2]]), 3))

    # ------------------------------------------------------------------
    rep.h1("Сравнение критериев")
    rep.p("Итоги сравнения при k = %d сведены в таблицу 4; места указаны от "
          "лучшей бумаги к худшей." % k0)
    rep.table(
        ("Акция", "Vu(X)", "Vu эмп(X)", "CE, %", "Место по Vu",
         "Место по Vu эмп"),
        [(lab(t), ru(vu[t], 5), ru(vu_emp[t], 5), ru(ce[t], 3),
          str(place_vu[t]), str(place_emp[t])) for t in TICKERS],
        (2.5, 2.7, 2.7, 2.4, 2.6, 2.9), size=10,
        caption="Таблица 4. Сравнение критериев ожидаемой полезности")
    rep.p("Критерии дают разные ответы: по функции варианта лучшая бумага - "
          "%s, по эмпирической функции - %s. Расхождение не является "
          "ошибкой расчёта, оно отражает различие в отношении к риску. "
          "Функция u(x) = x^0,2 имеет убывающую ARA и почти линейна в "
          "хвостах, поэтому критерий Vu вознаграждает широкий разброс и "
          "положительную асимметрию. Эмпирическая функция построена для "
          "ЛПР с постоянной ARA: каждый процент разброса штрафуется "
          "одинаково сильно, и бумага с меньшей дисперсией выигрывает, "
          "хотя её средняя доходность ниже."
          % (lab(leader_vu), lab(leader_emp)))
    rep.figure(chart_criteria(r),
               "Рисунок 3. Значения ожидаемой полезности по двум критериям",
               width_cm=16.5)
    rep.p("Оба критерия представляют один и тот же принцип максимизации "
          "ожидаемой полезности и различаются только функцией u. Выбор "
          "между ними - это выбор модели предпочтений, а не выбор более "
          "точного расчёта: Vu требует явного задания аналитической "
          "функции, эмпирический критерий - процедуры опроса ЛПР. По "
          "абсолютной величине шкалы не совпадают: Vu лежит в диапазоне "
          "%s ... %s с размахом %s, Vu эмп - в диапазоне %s ... %s, причём "
          "размах Vu эмп составляет всего %s, то есть критерии различают "
          "бумаги с разной степенью уверенности. Первое место в обоих "
          "случаях определено отчётливо, а вот Merck и Sanofi по "
          "эмпирическому критерию разделяют тысячные доли, и их порядок "
          "следует считать условным."
          % (ru(min(vu.values()), 4), ru(max(vu.values()), 4),
             ru(max(vu.values()) - min(vu.values()), 4),
             ru(min(vu_emp.values()), 4), ru(max(vu_emp.values()), 4),
             ru(max(vu_emp.values()) - min(vu_emp.values()), 4)))

    # ------------------------------------------------------------------
    rep.h1("Анализ чувствительности к числу интервалов k")
    rep.p("Интервальный ряд строится с некоторой свободой в выборе k, "
          "поэтому важно проверить, насколько вывод зависит от этого "
          "параметра. Расчёт повторён для k от %d до %d, то есть в "
          "окрестности исходного значения k = %d. Значения критериев и их "
          "отклонения от расчёта при k = %d приведены в таблицах 5 и 6 и на "
          "рисунке 4; отклонения указаны в процентах от значения при "
          "k = %d, для самого k = %d они равны нулю."
          % (min(r["ks"]), max(r["ks"]), k0, k0, k0, k0))

    rep.figure(chart_sensitivity(r),
               "Рисунок 4. Зависимость критериев от числа интервалов k",
               width_cm=16.5)

    def sens_rows(idx):
        base = {t: r["sens"][k0][t][idx] for t in TICKERS}
        out = []
        for k in r["ks"]:
            row = [str(k)]
            for t in TICKERS:
                v = r["sens"][k][t][idx]
                row.append("%s (%s %%)" % (ru(v, 4),
                                           ru(dev(v, base[t]), 1)))
            row.append(lab(best(r["sens"][k], idx)))
            out.append(row)
        return out

    def leaders(idx):
        found = {}
        for k in r["ks"]:
            found.setdefault(best(r["sens"][k], idx), []).append(k)
        parts = []
        for t in TICKERS:
            if t in found:
                parts.append("%s - при k = %s" % (
                    lab(t), ", ".join(str(k) for k in found[t])))
        return "; ".join(parts), found

    text_vu, found_vu = leaders(0)
    text_emp, found_emp = leaders(1)
    base_vu = {t: r["sens"][k0][t][0] for t in TICKERS}
    base_emp = {t: r["sens"][k0][t][1] for t in TICKERS}
    spread = {}
    for idx, base in ((0, base_vu), (1, base_emp)):
        worst = max(abs(dev(r["sens"][k][t][idx], base[t]))
                    for k in r["ks"] for t in TICKERS)
        spread[idx] = worst

    rep.p("Критерий Vu чувствителен к выбору k. Первое место распределяется "
          "так: %s, а максимальное отклонение значений от расчёта при "
          "k = %d достигает %s %% (у Bayer %s %%, у Merck %s %%, у Sanofi "
          "%s %%). Причина в том, что вклад интервала, содержащего нуль, "
          "равен среднему значению корня по этому интервалу, а оно растёт с "
          "длиной интервала: для симметричного интервала [−a; a] среднее "
          "составляет a^0,2 / 1,2. Поэтому при малом k, когда интервал с "
          "нулём широкий, Vu систематически завышается, а положение границ "
          "этого интервала зависит от числа групп."
          % (text_vu, k0, ru(spread[0], 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[0]][0], base_vu[TICKERS[0]]))
                   for k in r["ks"]), 1),
             ru(abs(dev(r["sens"][min(r["ks"])][TICKERS[1]][0],
                        base_vu[TICKERS[1]])), 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[2]][0], base_vu[TICKERS[2]]))
                   for k in r["ks"]), 1)))
    rep.p("Критерий Vu эмп практически не зависит от выбора k: %s, а "
          "максимальное отклонение не превышает %s %% (у Bayer %s %%, у "
          "Merck %s %%, у Sanofi %s %%). Причина в том, что эмпирическая "
          "функция задана на всём диапазоне доходности и интегрируется по "
          "сегментам между узлами, поэтому изменение границ интервалов "
          "лишь перераспределяет веса, не меняя формы функции. Вывод о "
          "преимуществе %s устойчив."
          % (text_emp, ru(spread[1], 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[0]][1], base_emp[TICKERS[0]]))
                   for k in r["ks"]), 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[1]][1], base_emp[TICKERS[1]]))
                   for k in r["ks"]), 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[2]][1], base_emp[TICKERS[2]]))
                   for k in r["ks"]), 1),
             lab(leader_emp)))
    rep.p("На рисунке 4 левая панель соответствует критерию Vu, правая - "
          "критерию Vu эмп. Линии на левой панели немонотонны и сближаются: "
          "при k = 7 Merck опережает Bayer на %s, тогда как при остальных k "
          "лидирует Bayer с отрывом до %s. На правой панели Sanofi "
          "сохраняет первое место на всём диапазоне k, а кривые идут почти "
          "параллельно. Практический вывод: ранжирование по эмпирической "
          "функции полезности устойчиво к выбору числа интервалов, а "
          "ранжирование по аналитической функции следует проверять "
          "пересчётом при нескольких k."
          % (ru(r["sens"][7][TICKERS[1]][0] - r["sens"][7][TICKERS[0]][0], 4),
             ru(max(r["sens"][k][leader_vu][0] - min(r["sens"][k][t][0]
                                                   for t in TICKERS)
                   for k in r["ks"]), 4)))

    rep.table(
        ("k", "Bayer", "Merck", "Sanofi", "Лучшая"),
        sens_rows(0),
        (1.0, 3.8, 3.8, 3.8, 2.6), size=8.5,
        caption="Таблица 5. Чувствительность критерия Vu(X) к числу "
                "интервалов k",
        keep_together=True)
    rep.table(
        ("k", "Bayer", "Merck", "Sanofi", "Лучшая"),
        sens_rows(1),
        (1.0, 3.8, 3.8, 3.8, 2.6), size=8.5,
        caption="Таблица 6. Чувствительность критерия Vu эмп(X) к числу "
                "интервалов k",
        keep_together=True)

    # ------------------------------------------------------------------
    rep.h1("Выводы")
    rep.numbers([
        "По функции полезности варианта u(x) = x^0,2 лучшей оказывается "
        "бумага %s: Vu = %s, тогда как у Merck %s и у Sanofi %s."
        % (lab(leader_vu), ru(vu[leader_vu], 5), ru(vu[TICKERS[1]], 5),
           ru(vu[TICKERS[2]], 5)),
        "По эмпирической функции полезности, построенной по девяти точкам и "
        "интерполированной сплайном, лучшей оказывается бумага %s: "
        "Vu эмп = %s, эквивалент уверенности %s %% против %s у %s."
        % (lab(leader_emp), ru(vu_emp[leader_emp], 5),
           ru(ce[leader_emp], 3), ru(ce[worst_emp], 3), lab(worst_emp)),
        "Расхождение критериев объясняется формой функции полезности: у "
        "x^0,2 несклонность к риску ARA = 0,8/|x| убывает с ростом |x|, "
        "поэтому критерий поощряет асимметрию и разброс, а функция с "
        "постоянной несклонностью к риску штрафует левый хвост и выбирает "
        "менее волатильную бумагу.",
        "Критерий Vu чувствителен к числу интервалов: отклонения достигают "
        "%s %%, а при k = 7 лидер меняется. Критерий Vu эмп устойчив: "
        "первое место неизменно, отклонения не превышают %s %%."
        % (ru(spread[0], 1), ru(spread[1], 1)),
        "Для обоснованного решения необходим явный профиль предпочтений "
        "ЛПР: без него оба критерия дают корректные, но разные рекомендации.",
    ])
    rep.p("Таким образом, задача выбора решена в рамках теории ожидаемой "
          "полезности, а её результат зависит от того, какая функция "
          "полезности принята. Если инвестор описывается функцией варианта, "
          "ему следует выбрать %s, если он несклонен к риску с постоянным "
          "показателем ARA, - %s. Критерий ожидаемой полезности позволяет "
          "учесть оба аспекта доходности - средний уровень и риск, - и "
          "именно это делает его содержательнее простого сравнения по "
          "среднему." % (lab(leader_vu), lab(leader_emp)))


# ---------------------------------------------------------------------------
# Сборка
# ---------------------------------------------------------------------------
def build():
    """Собирает отчёт: считает критерии, рисует фигуры, сохраняет DOCX."""
    dates, data = risk_data.load()
    r = utility.build(TICKERS, data)
    os.makedirs(OUT_DIR, exist_ok=True)

    meta = ReportMeta(
        lab_no="3",
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
    build_content(rep, dates, data, r)
    return rep.save()


if __name__ == "__main__":
    print(build())
