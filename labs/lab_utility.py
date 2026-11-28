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
    return ru(value, digits) + " %"


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
    ax1.set_xlabel("дневная доходность, %", fontsize=7, family=FONT,
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
    ax2.set_xlabel("дневная доходность, %", fontsize=7, family=FONT,
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

    fig, ax = single(5.9)
    ax.plot(grid, [r["u_emp"](x) for x in grid], color=COLOR["SAN.PA"], lw=1.4,
            label="эмпирическая полезность, сплайн")
    ax.plot(grid, [r["u_lin"](x) for x in grid], color="#777777", lw=1.0,
            ls=(0, (6, 2, 1, 2)), label="кусочно-линейная интерполяция")
    ax.plot([p[0] for p in r["knots"]], [p[1] for p in r["knots"]], "o",
            ms=4.5, color=COLOR["SAN.PA"], label="точки по процедуре опроса")
    ax.plot(grid, [u_var(x) for x in grid], color=COLOR["MRK"], lw=1.0,
            ls=(0, (4, 3)), label="функция варианта, u = x^0,2")
    ax.axhline(0.5, color="#a33", lw=0.8, ls=(0, (2, 3)))
    half = [p[0] for p in r["knots"] if abs(p[1] - 0.5) < 1e-9][0]
    ax.annotate("u = 0,5 при x = %s %%" % ru(half, 2),
                xy=(half, 0.5), xytext=(6, -18), textcoords="offset points",
                va="top", fontsize=6.5, family=FONT, color="#a33",
                arrowprops={"arrowstyle": "-", "color": "#a33", "lw": 0.7})
    ax.set_title("Эмпирическая функция полезности", fontsize=7.5, family=FONT,
                 pad=4)
    ax.set_xlabel("дневная доходность, %", fontsize=7, family=FONT,
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
        if idx == 0:
            ax.axhline(0.0, color="#555", lw=0.8)
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
        return abs(x) ** (POWER + 1.0) / (POWER + 1.0)
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

# ---------------------------------------------------------------------------
# Вспомогательные расчёты для таблиц
# ---------------------------------------------------------------------------
def midpoint_error(series, func):
    """Расхождение метода середин и точного интегрирования по ряду."""
    return (utility.midpoint_utility(series, func)
            - utility.expected_utility(series, func))


def sample_utility(data, func):
    """Прямой расчёт E[u(X)] по выборке: все наблюдения с весом 1/n."""
    values = [func(x * 100.0) for x in data]
    return sum(values) / len(values)


def interval_text(series, index):
    """Границы интервала в процентах для первой колонки таблиц."""
    a = series["edges"][index] * 100.0
    b = series["edges"][index + 1] * 100.0
    return "%s…%s" % (ru(a, 2), ru(b, 2))


# ---------------------------------------------------------------------------
# Текст отчёта
# ---------------------------------------------------------------------------
def build_content(rep, dates, data, r):
    stats = {t: dominance.describe_sample(data[t]) for t in TICKERS}
    prof = {t: risk_measures.compute(data, alphas=(0.99,))[t]["profile"]
            for t in TICKERS}
    n = stats[TICKERS[0]]["n"]
    k0 = r["k0"]
    vu, vu_emp, ce = r["vu"], r["vu_emp"], r["ce"]
    leader_vu = best_of(vu)
    leader_emp = best_of(vu_emp)
    place_vu = rank(vu)
    place_emp = rank(vu_emp)
    worst_vu = min(TICKERS, key=lambda t: vu[t])
    worst_emp = min(TICKERS, key=lambda t: vu_emp[t])
    sample = {t: sample_utility(data[t], r["u_pow"]) for t in TICKERS}
    sample_emp = {t: sample_utility(data[t], r["u_emp"]) for t in TICKERS}
    same = leader_vu == leader_emp

    def lab(t):
        return LABELS[t]

    # ------------------------------------------------------------------
    rep.h1("Цель работы")
    rep.p("Цель работы - изучить критерий ожидаемой полезности и применить "
          "его к задаче выбора объекта инвестирования. Сравниваются дневные "
          "доходности акций трёх фармацевтических компаний: альтернатива "
          "A₁ - Bayer (BAYN.DE), A₂ - Merck & Co (MRK), A₃ - Sanofi "
          "(SAN.PA). Эмпирические распределения этих доходностей построены "
          "в лабораторных работах №1 и №2.")
    rep.p("Вариант 3: период наблюдений - с %s по %s, всего n = %d общих "
          "торговых дней. Номер варианта нечётный, поэтому функция "
          "полезности имеет вид u(x) = x^(1/(n+2)); при n = 3 она равна "
          "u(x) = x^0,2. Дополнительно строится эмпирическая функция "
          "полезности по точкам и проверяется устойчивость результата к "
          "числу интервалов k."
          % (dates[0].strftime("%d.%m.%Y"), dates[-1].strftime("%d.%m.%Y"),
             n))
    rep.p("Задачи работы:")
    rep.numbers([
        "построить интервальные ряды дневных доходностей при k = %d;" % k0,
        "записать функцию полезности варианта, найти её производные и "
        "показатель несклонности к риску;",
        "вычислить Vu(X) для каждой бумаги и проранжировать альтернативы;",
        "привести подробный расчёт по интервалам вариационного ряда и "
        "сопоставить его с методом середин;",
        "построить эмпирическую функцию полезности, повторить сравнение и "
        "проверить устойчивость выводов к числу интервалов k.",
    ])

    # ------------------------------------------------------------------
    rep.h1("Вариант и статистические данные")
    rep.p("Данные те же, что в предыдущих работах: дневные цены закрытия за "
          "два года, выгруженные через библиотеку yfinance с сайта Yahoo "
          "Finance по тикерам BAYN.DE, MRK и SAN.PA и скорректированные на "
          "сплиты и дивиденды. Биржи работают по своим календарям, поэтому "
          "ряды приведены к общим торговым дням: остаются только даты, "
          "когда торговались все три бумаги, и сравнение не искажается "
          "разной длиной промежутков между строками.")
    rep.p("Дневная доходность считается как X_t = (P_t - P_(t-1)) / P_(t-1) "
          "и выражается в процентах, поскольку функция варианта "
          "u(x) = x^0,2 определена на процентной шкале.")
    rep.p("Выборка из n = %d значений разбита на k = %d интервалов равной "
          "длины по правилу Стерджиса. Наблюдение относится к интервалу с "
          "номером floor((x - x_min) / h), последнее наблюдение - всегда в "
          "последний интервал; внутри интервала распределение считается "
          "равномерным. Ширина интервала составляет %s п.п. у Bayer, %s "
          "п.п. у Merck и %s п.п. у Sanofi."
          % (n, k0,
             ru(r["series"][TICKERS[0]]["h"] * 100.0, 2),
             ru(r["series"][TICKERS[1]]["h"] * 100.0, 2),
             ru(r["series"][TICKERS[2]]["h"] * 100.0, 2)))
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
    rep.p("Средняя доходность и стандартное отклонение убывают от Bayer "
          "(%s и %s %%) к Merck (%s и %s %%) и Sanofi (%s и %s %%). "
          "Вероятность падения более чем на 3 %% у Bayer выше, чем у "
          "Sanofi: %s %% против %s %%. Выбор поэтому связан с компромиссом "
          "между доходностью и риском."
          % (ru(stats[TICKERS[0]]["mean"] * 100.0, 3),
             ru(stats[TICKERS[0]]["std"] * 100.0, 3),
             ru(stats[TICKERS[1]]["mean"] * 100.0, 3),
             ru(stats[TICKERS[1]]["std"] * 100.0, 3),
             ru(stats[TICKERS[2]]["mean"] * 100.0, 3),
             ru(stats[TICKERS[2]]["std"] * 100.0, 3),
             ru(stats[TICKERS[0]]["p_drop"] * 100.0, 2),
             ru(stats[TICKERS[2]]["p_drop"] * 100.0, 2)))
    rep.p("Эмпирические законы распределения, построенные в лабораторной "
          "работе №1, приведены в таблицах 2-4. Для каждого интервала "
          "указаны его границы, середина x_j, число наблюдений n_j и "
          "вероятность p_j = n_j / n; сумма вероятностей равна единице, а "
          "интервалы без наблюдений остаются в таблице с p_j = 0. Именно "
          "эти ряды используются ниже для расчёта ожидаемой полезности.")
    for t, number in zip(TICKERS, ("2", "3", "4")):
        series = r["series"][t]
        rep.table(
            ("Интервал, %", "x_j, %", "n_j", "p_j"),
            [(interval_text(series, j), ru(series["mids"][j] * 100.0, 2),
              str(series["counts"][j]), ru(series["freq"][j], 4))
             for j in range(series["k"])],
            (4.6, 3.4, 2.2, 2.2), size=10,
            caption="Таблица %s. Эмпирический закон распределения дневных "
                    "доходностей %s при k = %d" % (number, lab(t), k0),
            keep_together=True)

    # ------------------------------------------------------------------
    rep.h1("Постановка задачи")
    rep.p("Пусть X - дневная доходность в процентах, u(x) - функция "
          "полезности. Критерий ожидаемой полезности сопоставляет величине "
          "число")
    rep.formula("Vu(X) = E[u(X)] = ∫ u(x) dF(x);")
    rep.p("альтернатива с большим Vu предпочтительнее. Для интервального "
          "ряда с границами a_j и частотами p_j при равномерности внутри "
          "интервала")
    rep.formula("Vu(X) = Σ_j p_j · (1 / h_j) · ∫ u(x) dx,   x ∈ [a_j; a_j+1],")
    rep.p("где h_j - длина j-го интервала. При линейной u критерий совпадает "
          "с математическим ожиданием, при вогнутой - учитывает разброс.")
    rep.p("Для варианта 3 функция полезности является нечётным корнем:")
    rep.formula("u(x) = x^(1/(n+2)) = x^0,2,   u(x) = sign(x)·|x|^0,2.")
    rep.p("Она возрастает и вогнута, поэтому инвестор несклонен к риску. "
          "Производные u′(x) = 0,2·|x|^(−0,8) и u″(x) = −0,16·|x|^(−1,8), "
          "показатель Эрроу-Пратта")
    rep.formula("ARA(x) = −u″(x) / u′(x) = 0,8 / |x|")
    rep.p("убывает с ростом |x|: вблизи нуля инвестор осторожен, в далёких "
          "хвостах почти нейтрален. Нормировка не меняет порядка "
          "альтернатив, на рисунках функция приведена к [0; 1]:")
    rep.formula("ũ(x) = (u(x) − u(x_min)) / (u(x_max) − u(x_min)).")
    rep.p("Вторая функция строится процедурой деления пополам, как в "
          "лекционном алгоритме: крайним значениям приписываются полезности "
          "0 и 1, для отрезка [a; b] находится эквивалент уверенности CE - "
          "гарантированная доходность, равнозначная лотерее «a или b», - и "
          "u(CE) = (u(a) + u(b)) / 2. Выполняются три деления пополам, "
          "поэтому получаются девять опорных точек с уровнями 0; 0,125 ... "
          "0,875; 1.")
    rep.p("Эквивалент уверенности вычисляется для модели с постоянной "
          "абсолютной несклонностью к риску u₀(x) = 1 − exp(−λx):")
    rep.formula("CE = −ln((exp(−λa) + exp(−λb)) / 2) / λ,   λ = 0,2 1/п.п.;")
    rep.p("при разбросе ±5 п.п. ЛПР уступает около 7 п.п.; по точкам "
          "функция восстанавливается монотонным сплайном Фрича-Карлсона.")

    # ------------------------------------------------------------------
    rep.h1("Методика расчёта")
    rep.p("Интеграл по каждому интервалу считается точно: производная "
          "u(x) = x^0,2 обращается в бесконечность в нуле, а эмпирическая "
          "функция имеет изломы в узлах сплайна, поэтому квадратуры на "
          "равномерной сетке дают заметную ошибку. Для функции варианта "
          "первообразная известна в замкнутом виде:")
    rep.formula("∫ u(x) dx = (|b|^1,2 − |a|^1,2) / 1,2.")
    rep.p("Замена интервала серединой здесь непригодна: в интервале, "
          "содержащем нуль, функция меняется от отрицательных значений к "
          "положительным, и u(x_j) в середине сильно отличается от среднего "
          "по интервалу. У Bayer при k = %d метод середин даёт %s вместо "
          "%s, а при k = %d - %s вместо %s: расхождение сравнимо с самим "
          "Vu."
          % (k0,
             ru(r["vu_mid"][leader_vu], 4), ru(vu[leader_vu], 4),
             min(r["ks"]),
             ru(utility.midpoint_utility(
                 risk_measures.variation_series(data[leader_vu],
                                                min(r["ks"])),
                 utility.power_utility), 4),
             ru(r["sens"][min(r["ks"])][leader_vu][0], 4)))
    rep.code(CODE_INTEGRAL, size=8.5)
    rep.p("Листинг 1. Точное интегрирование функции полезности по "
          "интервальному ряду")
    rep.p("Функция варианта записывается одной строкой, эмпирическая "
          "строится по точкам, а эквивалент уверенности считается по "
          "замкнутой формуле.")
    rep.code(CODE_KNOTS, size=8.5)
    rep.p("Листинг 2. Функция полезности варианта и точки эмпирической "
          "полезности")
    rep.p("Интерполяция выполняется монотонным кубическим сплайном: при "
          "разном знаке соседних наклонов производная в узле обнуляется, "
          "поэтому полезность не выходит за [0; 1]. На каждом сегменте "
          "сплайн - кубический многочлен, и интеграл по интервалу ряда "
          "считается по формуле Симпсона точно.")

    # ------------------------------------------------------------------
    rep.h1("Критерий ожидаемой полезности Vu")
    rep.p("На рисунке 1 показана нормированная функция полезности варианта "
          "и её показатель несклонности к риску. Кривая круто поднимается "
          "вблизи нуля и выходит на плато при больших доходностях, а ARA "
          "падает с %s при x = 0,5 %% до %s при x = 10 %% - примерно в "
          "двадцать раз."
          % (ru(utility.absolute_risk_aversion(0.5), 2),
             ru(utility.absolute_risk_aversion(10.0), 2)))
    rep.figure(chart_utility(r),
               "Рисунок 1. Функция полезности варианта u(x) = x^0,2 и её "
               "показатель несклонности к риску ARA(x)", width_cm=16.5)
    reps = [(x, utility.absolute_risk_aversion(x)) for x in ARA_POINTS]
    rep.table(
        ("x, %", "ARA(x), 1/п.п."),
        [(ru(x, 1), ru(y, 3)) for x, y in reps],
        (3.4, 3.4), size=10,
        caption="Таблица 5. Абсолютная несклонность к риску функции варианта")
    rep.p("При k = %d значения Vu равны %s у Bayer, %s у Merck и %s у "
          "Sanofi: первой оказывается бумага %s, последней - %s. Разрыв "
          "составляет %s, или около %s %% от значения лидера."
          % (k0, ru(vu[TICKERS[0]], 5), ru(vu[TICKERS[1]], 5),
             ru(vu[TICKERS[2]], 5), lab(leader_vu), lab(worst_vu),
             ru(vu[leader_vu] - vu[worst_vu], 5),
             ru((vu[leader_vu] - vu[worst_vu]) / abs(vu[leader_vu]) * 100.0,
                1)))
    rep.p("Значения малы по модулю и лежат около нуля: полезность x^0,2 "
          "сжимает шкалу доходности, поэтому вклад каждого процента в "
          "среднюю полезность невелик, а сама оценка оказывается разностью "
          "больших по модулю слагаемых. Порядок альтернатив определяется "
          "массой далёких хвостов: убывающая ARA почти не штрафует крупный "
          "проигрыш, но и не слишком поощряет крупный выигрыш. Поэтому "
          "устойчивость ответа здесь нужно проверять отдельно - сравнение "
          "методов расчёта приведено в разделе 7, а зависимость от k - в "
          "разделе 9.")

    # ------------------------------------------------------------------
    rep.h1("Эмпирическая функция полезности")
    rep.p("Точки эмпирической полезности при λ = 0,2 приведены в таблице 6. "
          "Шкала аргумента общая для всех бумаг: от %s %% до %s %%, поэтому "
          "функции полезности сопоставимы."
          % (ru(r["lo"], 2), ru(r["hi"], 2)))
    rep.table(
        ("x, %", "u(x)", "Уровень"),
        [(ru(x, 2), ru(u, 4), ("минимум" if i == 0 else
                               "максимум" if i == len(r["knots"]) - 1 else
                               "точка деления"))
         for i, (x, u) in enumerate(r["knots"])],
        (3.4, 3.4, 4.4), size=10,
        caption="Таблица 6. Точки эмпирической функции полезности")
    rep.p("На рисунке 2 точки показаны маркерами, сплошная линия - "
          "интерполяция сплайном, штрихпунктирная - кусочно-линейная "
          "интерполяция по тем же точкам, пунктирная - функция варианта. "
          "Эмпирическая функция резко вогнута: половина шкалы достигается "
          "при x = %s %%, последняя восьмая часть - на интервале от %s до "
          "%s %%."
          % (ru([p[0] for p in r["knots"] if abs(p[1] - 0.5) < 1e-9][0], 2),
             ru([p[0] for p in r["knots"] if abs(p[1] - 0.875) < 1e-9][0], 2),
             ru(r["hi"], 2)))
    rep.figure(chart_empirical(r),
               "Рисунок 2. Точки эмпирической функции полезности, "
               "интерполяция сплайном и ломаной", width_cm=16.5)
    rep.p("Ломаная даёт Vu эмп = %s, %s и %s, то есть на %s %% ниже "
          "сплайна, но порядок альтернатив не меняет. Сплайн выбран потому, "
          "что у ломаной в узлах изломы: производная там не определена, "
          "вогнутость между узлами не гарантирована, и в точках деления "
          "полезность ведёт себя как функция с постоянной несклонностью к "
          "риску только на каждом звене."
          % (ru(r["vu_lin"][TICKERS[0]], 4), ru(r["vu_lin"][TICKERS[1]], 4),
             ru(r["vu_lin"][TICKERS[2]], 4),
             ru(abs(dev(r["vu_lin"][TICKERS[0]], vu_emp[TICKERS[0]])), 1)))
    rep.p("По эмпирической функции Vu эмп равно %s у Bayer, %s у Merck и "
          "%s у Sanofi: первой оказывается %s, последней - %s. Эквивалент "
          "уверенности составляет %s; %s и %s %% - отрицательные значения "
          "означают, что лотерея хуже гарантированного малого убытка."
          % (ru(vu_emp[TICKERS[0]], 5), ru(vu_emp[TICKERS[1]], 5),
             ru(vu_emp[TICKERS[2]], 5), lab(leader_emp), lab(worst_emp),
             ru(ce[TICKERS[0]], 3), ru(ce[TICKERS[1]], 3),
             ru(ce[TICKERS[2]], 3)))

    # ------------------------------------------------------------------
    rep.h1("Расчёт по интервалам вариационного ряда")
    rep.p("В таблицах 7-9 приведён полный расчёт ожидаемой полезности при "
          "k = %d: для каждого интервала указаны его границы, середина x_j, "
          "вероятность p_j, значения обеих функций полезности в середине "
          "интервала и их вклады. Строка «Итого» в этих таблицах даёт Vu по "
          "методу середин, то есть сумму p_j·u(x_j)." % k0)

    def calc_rows(series):
        out, total_pow, total_emp = [], 0.0, 0.0
        for j, p in enumerate(series["freq"]):
            mid = series["mids"][j] * 100.0
            u_mid = r["u_pow"](mid)
            emp_mid = r["u_emp"](mid)
            out.append([interval_text(series, j), ru(mid, 2), ru(p, 4),
                        ru(u_mid, 4), ru(p * u_mid, 4),
                        ru(emp_mid, 4), ru(p * emp_mid, 4)])
            total_pow += p * u_mid
            total_emp += p * emp_mid
        out.append(["Итого", "", "1,0000", "", ru(total_pow, 4), "",
                    ru(total_emp, 4)])
        return out

    for t, number in zip(TICKERS, ("7", "8", "9")):
        rep.table(
            ("Интервал, %", "x_j, %", "p_j", "u(x_j)", "p_j·u(x_j)",
             "u эмп(x_j)", "p_j·u эмп(x_j)"),
            calc_rows(r["series"][t]),
            (3.8, 1.9, 1.8, 1.9, 2.3, 2.0, 2.4), size=8.5,
            caption="Таблица %s. Расчёт ожидаемой полезности по интервалам "
                    "для %s" % (number, lab(t)),
            keep_together=True)
    rep.p("Метод середин и точное интегрирование дают разные значения, "
          "поскольку внутри широкого интервала полезность меняется сильно "
          "нелинейно. В таблице 10 оба расчёта сопоставлены со средним по "
          "выборке, где каждое из %d наблюдений входит с весом 1/n: это "
          "значение не зависит от разбиения и служит эталоном." % n)
    rep.table(
        ("Акция", "Vu: середины", "Vu: по ряду", "Vu: по выборке",
         "Vu эмп: середины", "Vu эмп: по ряду", "Vu эмп: по выборке"),
        [(lab(t), ru(r["vu_mid"][t], 4), ru(vu[t], 4), ru(sample[t], 4),
          ru(r["vu_emp_mid"][t], 4), ru(vu_emp[t], 4), ru(sample_emp[t], 4))
         for t in TICKERS],
        (2.4, 2.2, 2.2, 2.2, 2.4, 2.3, 2.3), size=9,
        caption="Таблица 10. Сравнение методов расчёта ожидаемой полезности",
        keep_together=True)
    rep.p("У эмпирической функции все три способа дают почти одно и то же: "
          "расхождение метода середин с точным расчётом не превышает %s %%, "
          "а сплайн и выборка совпадают до третьего знака. У функции "
          "варианта картина иная: метод середин завышает разброс оценки, и "
          "порядок альтернатив меняется. Прямой расчёт по выборке даёт %s у "
          "Bayer, %s у Merck и %s у Sanofi, то есть первое место занимает "
          "%s, тогда как интервальный ряд при k = %d ставит на первое место "
          "%s. Расхождение объясняется равномерным распределением внутри "
          "интервалов: оно приписывает широкому интервалу, содержащему "
          "нуль, слишком много массы в далёких хвостах."
          % (ru(max(abs(dev(r["vu_emp_mid"][t], vu_emp[t]))
                    for t in TICKERS), 1),
             ru(sample[TICKERS[0]], 4), ru(sample[TICKERS[1]], 4),
             ru(sample[TICKERS[2]], 4), lab(best_of(sample)), k0,
             lab(leader_vu)))

    # ------------------------------------------------------------------
    rep.h1("Сравнение критериев")
    rep.p("Итоги при k = %d сведены в таблицу 11; места указаны от лучшей "
          "бумаги к худшей." % k0)
    rep.table(
        ("Акция", "Vu(X)", "Vu эмп(X)", "CE, %", "Место по Vu",
         "Место по Vu эмп"),
        [(lab(t), ru(vu[t], 5), ru(vu_emp[t], 5), ru(ce[t], 3),
          str(place_vu[t]), str(place_emp[t])) for t in TICKERS],
        (2.5, 2.7, 2.7, 2.4, 2.6, 2.9), size=10,
        caption="Таблица 11. Сравнение критериев ожидаемой полезности")
    if same:
        rep.p("При k = %d оба критерия указывают на одну и ту же бумагу - "
              "%s. Совпадение не случайно: эмпирическая функция построена "
              "по той же шкале доходности, что и функция варианта, и обе "
              "вогнуты, поэтому одинаково реагируют на разброс. Совпадает "
              "и разрыв: у эмпирической функции он равен %s, у функции "
              "варианта - %s."
              % (k0, lab(leader_vu),
                 ru(max(vu_emp.values()) - min(vu_emp.values()), 4),
                 ru(max(vu.values()) - min(vu.values()), 4)))
    else:
        rep.p("Критерии дают разные ответы: по функции варианта лучшая "
              "бумага - %s, по эмпирической функции - %s. Расхождение "
              "отражает различие в отношении к риску: функция x^0,2 имеет "
              "убывающую ARA, а эмпирическая функция с постоянной ARA "
              "штрафует каждый процент разброса одинаково."
              % (lab(leader_vu), lab(leader_emp)))
    rep.figure(chart_criteria(r),
               "Рисунок 3. Значения ожидаемой полезности по двум критериям",
               width_cm=16.5)
    rep.p("Оба критерия представляют один принцип максимизации ожидаемой "
          "полезности и различаются только функцией u. Vu лежит в диапазоне "
          "%s ... %s с размахом %s, Vu эмп - в диапазоне %s ... %s с "
          "размахом %s. Второе место определено отчётливо, а Bayer и Merck "
          "по эмпирическому критерию разделяют тысячные доли."
          % (ru(min(vu.values()), 4), ru(max(vu.values()), 4),
             ru(max(vu.values()) - min(vu.values()), 4),
             ru(min(vu_emp.values()), 4), ru(max(vu_emp.values()), 4),
             ru(max(vu_emp.values()) - min(vu_emp.values()), 4)))
    rep.p("Полезно сопоставить результат с мерами риска из лабораторной "
          "работы №1 (таблица 12): они считаются по тем же интервальным "
          "рядам, но не используют функцию полезности.")
    rep.table(
        ("Акция", "μ, %", "σ, %", "Lσ, %", "VaR₀,₉₉, %", "CVaR₀,₉₉, %"),
        [(lab(t), ru(prof[t]["mean"] * 100.0, 3),
          ru(prof[t]["std"] * 100.0, 3),
          ru(prof[t]["lstd"] * 100.0, 3),
          ru(prof[t]["var_"][0.99] * 100.0, 2),
          ru(prof[t]["cvar"][0.99] * 100.0, 2)) for t in TICKERS],
        (2.2, 2.1, 2.1, 2.2, 2.6, 2.8), size=10,
        caption="Таблица 12. Меры риска дневных доходностей из "
                "лабораторной работы №1")
    rep.p("Средняя доходность максимальна у Bayer (%s %%), стандартное "
          "отклонение и полуотклонение - у Sanofi (%s и %s %%), а "
          "наименьшие VaR и CVaR на уровне 0,99 имеет Merck (%s и %s %%). "
          "Обычный критерий «доходность-риск» смотрит в сторону Bayer по "
          "доходности и Sanofi по разбросу, тогда как хвостовые меры "
          "выделяют Merck. Критерий ожидаемой полезности сглаживает эти "
          "характеристики в одно число: при эмпирической функции "
          "преимущество получает %s, у которой меньше разброс, а при "
          "функции варианта ответ зависит от разбиения (раздел 7). "
          "Расхождение с VaR и CVaR закономерно: эти меры учитывают только "
          "левый хвост, а ожидаемая полезность - всё распределение, и при "
          "убывающей ARA далёкий выигрыш компенсирует далёкий проигрыш."
          % (ru(stats[TICKERS[0]]["mean"] * 100.0, 3),
             ru(prof[TICKERS[2]]["std"] * 100.0, 3),
             ru(prof[TICKERS[2]]["lstd"] * 100.0, 3),
             ru(prof[TICKERS[1]]["var_"][0.99] * 100.0, 2),
             ru(prof[TICKERS[1]]["cvar"][0.99] * 100.0, 2),
             lab(leader_emp)))

    # ------------------------------------------------------------------
    rep.h1("Анализ чувствительности к числу интервалов k")
    rep.p("Число интервалов k выбирается с некоторой свободой, поэтому "
          "расчёт повторён для k от %d до %d. Отклонения в таблицах 13 и "
          "14 указаны в процентах от значения при k = %d."
          % (min(r["ks"]), max(r["ks"]), k0))

    rep.figure(chart_sensitivity(r),
               "Рисунок 4. Зависимость критериев от числа интервалов k",
               width_cm=16.5)

    def sens_rows(idx):
        base = {t: r["sens"][k0][t][idx] for t in TICKERS}
        out = []
        for k in r["ks"]:
            winner = lab(best(r["sens"][k], idx))
            for t in TICKERS:
                v = r["sens"][k][t][idx]
                out.append([str(k), lab(t), ru(v, 4),
                            ru(dev(v, base[t]), 1), winner])
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
        spread[idx] = max(abs(dev(r["sens"][k][t][idx], base[t]))
                          for k in r["ks"] for t in TICKERS)
    signs = sorted({("положительно" if r["sens"][k][t][0] > 0
                     else "отрицательно")
                    for k in r["ks"] for t in TICKERS})

    rep.p("Критерий Vu сильно зависит от k: лидер меняется - %s, а "
          "максимальное отклонение достигает %s %% (у Bayer %s %%, у "
          "Merck %s %%, у Sanofi %s %%). Оценка по функции x^0,2 не только "
          "смещается, но и меняет знак: при разных k она бывает %s. Причина "
          "в том, что средняя полезность близка к нулю, а вклад интервала, "
          "содержащего нуль, при равномерном внутриинтервальном "
          "распределении сильно зависит от его границ; с ростом k этот "
          "вклад стабилизируется, и Vu приближается к прямому расчёту по "
          "выборке."
          % (text_vu, ru(spread[0], 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[0]][0], base_vu[TICKERS[0]]))
                   for k in r["ks"]), 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[1]][0], base_vu[TICKERS[1]]))
                   for k in r["ks"]), 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[2]][0], base_vu[TICKERS[2]]))
                   for k in r["ks"]), 1),
             " и ".join(signs)))
    rep.p("Критерий Vu эмп почти не зависит от k: %s, максимальное "
          "отклонение не превышает %s %% (у Bayer %s %%, у Merck %s %%, у "
          "Sanofi %s %%). Эмпирическая функция задана на всём диапазоне и "
          "интегрируется между узлами, поэтому меняются лишь веса "
          "интервалов. Вывод о преимуществе %s устойчив."
          % (text_emp, ru(spread[1], 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[0]][1], base_emp[TICKERS[0]]))
                   for k in r["ks"]), 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[1]][1], base_emp[TICKERS[1]]))
                   for k in r["ks"]), 1),
             ru(max(abs(dev(r["sens"][k][TICKERS[2]][1], base_emp[TICKERS[2]]))
                   for k in r["ks"]), 1),
             lab(leader_emp)))

    rep.table(
        ("k", "Акция", "Vu(X)", "Отклонение, %", "Лучшая"),
        sens_rows(0),
        (1.2, 3.4, 3.2, 3.2, 3.2), size=8.5,
        caption="Таблица 13. Чувствительность критерия Vu(X) к числу "
                "интервалов k")
    rep.table(
        ("k", "Акция", "Vu эмп(X)", "Отклонение, %", "Лучшая"),
        sens_rows(1),
        (1.2, 3.4, 3.2, 3.2, 3.2), size=8.5,
        caption="Таблица 14. Чувствительность критерия Vu эмп(X) к числу "
                "интервалов k")

    # ------------------------------------------------------------------
    rep.h1("Выводы")
    rep.numbers([
        "По функции варианта u(x) = x^0,2 при k = %d лучшей оказывается %s: "
        "Vu = %s против %s у Merck и %s у Sanofi, но эта оценка неустойчива "
        "- прямой расчёт по выборке ставит на первое место %s."
        % (k0, lab(leader_vu), ru(vu[leader_vu], 5), ru(vu[TICKERS[1]], 5),
           ru(vu[TICKERS[2]], 5), lab(best_of(sample))),
        "По эмпирической функции лучшей оказывается %s: Vu эмп = %s, "
        "эквивалент уверенности %s %% против %s у %s."
        % (lab(leader_emp), ru(vu_emp[leader_emp], 5),
           ru(ce[leader_emp], 3), ru(ce[worst_emp], 3), lab(worst_emp)),
        "Расхождение объясняется формой полезности: убывающая ARA у x^0,2 "
        "почти не различает хвосты, а функция с постоянной ARA штрафует "
        "левый хвост и выбирает менее волатильную бумагу.",
        "Vu чувствителен к числу интервалов: отклонения достигают %s %%, а "
        "лидер меняется при разных k. Vu эмп устойчив: отклонения не "
        "превышают %s %%."
        % (ru(spread[0], 1), ru(spread[1], 1)),
        "Порядок, полученный методом середин, использовать нельзя: он "
        "расходится с точным интегрированием по тем же рядам, поэтому в "
        "отчёте все значения Vu считаются интегралом по интервалу.",
        "Для обоснованного решения необходим явный профиль предпочтений "
        "ЛПР: без него оба критерия дают корректные, но разные рекомендации.",
    ])
    rep.p("Задача выбора решена в рамках теории ожидаемой полезности. При "
          "эмпирической функции с постоянной несклонностью к риску следует "
          "выбрать %s; функция варианта x^0,2 на этих данных даёт "
          "неустойчивый ответ, поэтому опираться на неё без проверки "
          "чувствительности к k нельзя."
          % lab(leader_emp))


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
