# -*- coding: utf-8 -*-
"""Лабораторная работа №1, дисциплина «Принятие решений в условиях
неопределённости».

Тема: меры риска. Сравниваются дневные доходности трёх акций
фармацевтических компаний - Bayer, Merck & Co и Sanofi - за два года.

Числа в отчёте не вписаны руками: они считаются из выборки
``labs/data/risk_quotes.csv`` модулем ``labs.risk_measures`` при сборке.
Поэтому текст и таблицы всегда согласованы, а пересчёт под другой вариант -
это правка ``TICKERS`` в ``labs.risk_data``.

Запуск:  python build.py --lab risk1
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

from labkit.docxgen import Report, ReportMeta
from labkit.schemes import DPI, FONT

from labs import risk_data, risk_measures

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(HERE, "out")

TITLE = "Меры риска"
PAGE_TITLE = "МЕРЫ РИСКА"
SHORT_TITLE = "Меры риска на примере акций фармацевтических компаний"
OUT_NAME = "Воробьев_И_С_отчет_по_1_ЛР_Меры_риска.docx"

IMG_PRICES = os.path.join(OUT_DIR, "risk_prices.png")
IMG_DIST = os.path.join(OUT_DIR, "risk_distributions.png")
IMG_TAIL = os.path.join(OUT_DIR, "risk_tail.png")

TICKERS = risk_data.TICKERS
LABELS = {"BAYN.DE": "Bayer", "MRK": "Merck", "SAN.PA": "Sanofi"}
CURRENCY = risk_data.CURRENCY
COLOR = {"BAYN.DE": "#1f4e79", "MRK": "#b06a2c", "SAN.PA": "#2e7d32"}
ALPHAS = (0.95, 0.97, 0.99)

# Листинги для отчёта: фрагменты labs/risk_measures.py. Строки собраны
# вручную, чтобы в DOCX попадал только расчёт, без импортов и CLI.
CODE_SERIES = """\
def sturges_k(n):
    return max(1, int(round(1.0 + 3.322 * math.log10(n))))


def variation_series(values, k=None):
    n = len(values)
    k = k or sturges_k(n)
    lo, hi = min(values), max(values)
    if hi == lo:
        hi = lo + 1e-12
    h = (hi - lo) / k
    counts = [0] * k
    for x in values:
        idx = int((x - lo) / h)
        if idx >= k:
            idx = k - 1
        counts[idx] += 1
    edges = [lo + h * i for i in range(k + 1)]
    mids = [(edges[i] + edges[i + 1]) / 2.0 for i in range(k)]
    freq = [count / n for count in counts]
    cum, acc = [], 0.0
    for p in freq:
        acc += p
        cum.append(acc)
    return {"n": n, "k": k, "h": h, "edges": edges,
            "mids": mids, "counts": counts, "freq": freq, "cum": cum}
"""

CODE_MOMENTS = """\
def grouped_moments(series):
    mids, freq = series["mids"], series["freq"]
    mean_value = sum(x * p for x, p in zip(mids, freq))
    var_value = sum((x - mean_value) ** 2 * p for x, p in zip(mids, freq))
    return mean_value, var_value


def grouped_left_contribution(series):
    mu, _ = grouped_moments(series)
    contrib, mass = 0.0, 0.0
    for x, p in zip(series["mids"], series["freq"]):
        if x <= mu:
            contrib += (x - mu) ** 2 * p
            mass += p
    return contrib, mass
"""

CODE_TAIL = """\
def grouped_loss_series(series):
    rows = []
    for i, (x, p) in enumerate(zip(series["mids"], series["freq"])):
        rows.append((-x, p, -series["edges"][i + 1], -series["edges"][i]))
    rows.sort(key=lambda item: item[0])
    mids = [row[0] for row in rows]
    freq = [row[1] for row in rows]
    edges = [(row[2], row[3]) for row in rows]
    cum, acc = [], 0.0
    for p in freq:
        acc += p
        cum.append(acc)
    return {"mids": mids, "freq": freq, "cum": cum, "intervals": edges}


def grouped_var(loss_series, alpha):
    for y, acc in zip(loss_series["mids"], loss_series["cum"]):
        if acc >= alpha - 1e-15:
            return y
    return loss_series["mids"][-1]


def grouped_cvar(loss_series, alpha):
    threshold = grouped_var(loss_series, alpha)
    num, den = 0.0, 0.0
    for y, p in zip(loss_series["mids"], loss_series["freq"]):
        if y > threshold + 1e-15:
            num += y * p
            den += p
    if den == 0.0:
        return threshold, 0.0
    return num / den, den
"""


# ---------------------------------------------------------------------------
# Форматирование чисел в русской записи
# ---------------------------------------------------------------------------
def ru(value, digits=2):
    """Число с запятой в дробной части и пробелом между разрядами."""
    text = ("{:,.%df}" % digits).format(value)
    return text.replace(",", "\u00a0").replace(".", ",")


def ru_trunc(value, digits=2):
    """То же, но лишние знаки отбрасываются, а не округляются."""
    factor = 10 ** digits
    return ru(math.floor(value * factor) / factor, digits)


def axis_pct(value, _pos=None):
    return ("%.0f" % value).replace("-", "\u2212") + " %"


def plural(number, one, few, many):
    """Склонение существительного при числительном."""
    if number % 10 == 1 and number % 100 != 11:
        return "%d %s" % (number, one)
    if 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        return "%d %s" % (number, few)
    return "%d %s" % (number, many)


# ---------------------------------------------------------------------------
# Рисунок 1. Динамика цен закрытия
# ---------------------------------------------------------------------------
def chart_prices(dates, prices):
    """Три нормированных ряда: все начинаются со 100.

    Нормировка нужна потому, что бумаги торгуются в разных валютах и в
    разных ценовых диапазонах; абсолютные цены несравнимы, а накопленная
    доходность - да.
    """
    fig, ax = plt.subplots(figsize=(17.0 / 2.54, 5.4 / 2.54), dpi=DPI)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.92, bottom=0.20)

    for ticker in TICKERS:
        series = prices[ticker]
        base = series[0]
        norm = [value / base * 100.0 for value in series]
        ax.plot(range(len(norm)), norm, color=COLOR[ticker], lw=1.0,
                label="%s (%s)" % (LABELS[ticker], ticker))

    # подписи по годам: первое наблюдение года
    ticks, labels = [], []
    for i, day in enumerate(dates):
        if day.month == 1 and (not ticks or dates[ticks[-1]].year != day.year):
            ticks.append(i)
            labels.append(str(day.year))
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, fontsize=7, family=FONT)
    ax.set_xlim(0, len(dates) - 1)

    ax.grid(True, color="#e3e7ec", lw=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=7, colors="#2c3e50")
    for label in ax.get_yticklabels():
        label.set_fontfamily(FONT)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: "%.0f" % v))
    ax.set_ylabel("цена, % от начальной", fontsize=7, family=FONT,
                  color="#1b1b1b")
    ax.legend(fontsize=7, frameon=False, loc="upper left", ncol=3,
              prop={"family": FONT, "size": 7})

    os.makedirs(OUT_DIR, exist_ok=True)
    fig.savefig(IMG_PRICES, facecolor="white")
    plt.close(fig)
    return IMG_PRICES


# ---------------------------------------------------------------------------
# Рисунок 2. Эмпирические законы распределения
# ---------------------------------------------------------------------------
def chart_distributions(result):
    """Гистограмма частот и полигон относительных частот по трём акциям.

    Столбцы строятся по границам интервалов вариационного ряда, полигон
    проходит через середины интервалов: на рисунке виден ровно тот закон,
    который выписан в таблицах.
    """
    fig, axes = plt.subplots(1, 3, figsize=(17.0 / 2.54, 6.2 / 2.54),
                             dpi=DPI, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.99, top=0.80, bottom=0.20,
                        wspace=0.12)

    for ax, ticker in zip(axes, TICKERS):
        item = result[ticker]
        series, profile = item["series"], item["profile"]
        edges = [edge * 100.0 for edge in series["edges"]]
        mids = [mid * 100.0 for mid in series["mids"]]
        freq = series["freq"]
        peak = max(freq)

        ax.bar(mids, freq, width=[b - a for a, b in zip(edges, edges[1:])],
               facecolor="#dce6f0", edgecolor=COLOR[ticker], linewidth=0.5,
               zorder=2)
        ax.plot(mids, freq, color=COLOR[ticker], lw=1.1, marker="o",
                markersize=2.6, zorder=3)

        # VaR на рисунке - граница левого хвоста доходности, то есть -VaR(Y)
        var_line = -profile["var_"][0.95] * 100.0
        ax.axvline(var_line, color="#a33", lw=0.9, ls=(0, (4, 3)), zorder=4)
        ax.annotate("VaR 0,95", xy=(var_line, peak * 0.9),
                    xytext=(var_line + 0.5, peak * 0.9), fontsize=6,
                    family=FONT, color="#a33", va="center")

        ax.set_title("%s: k = %d, h = %s %%"
                     % (LABELS[ticker], series["k"],
                        ru(series["h"] * 100.0, 6)),
                     fontsize=7.5, family=FONT, pad=4)
        ax.set_xlim(min(edges) - 0.8, max(edges) + 0.8)
        ax.set_ylim(0, 0.62)
        ax.grid(True, axis="y", color="#e3e7ec", lw=0.5)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.tick_params(labelsize=6.5)
        ax.set_xlabel("дневная доходность", fontsize=7, family=FONT,
                      color="#1b1b1b")
        ax.xaxis.set_major_locator(MultipleLocator(5))
        ax.xaxis.set_major_formatter(FuncFormatter(axis_pct))
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontfamily(FONT)

    axes[0].set_ylabel("относительная частота", fontsize=7, family=FONT,
                       color="#1b1b1b")

    os.makedirs(OUT_DIR, exist_ok=True)
    fig.savefig(IMG_DIST, facecolor="white")
    plt.close(fig)
    return IMG_DIST



# ---------------------------------------------------------------------------
# Рисунок 4. VaR и CVaR в зависимости от доверительной вероятности
# ---------------------------------------------------------------------------
def chart_tail(result):
    """Два поля: VaR слева, CVaR справа; по оси абсцисс - alpha."""
    fig, axes = plt.subplots(1, 2, figsize=(17.0 / 2.54, 4.8 / 2.54),
                             dpi=DPI)
    fig.subplots_adjust(left=0.075, right=0.98, top=0.86, bottom=0.17,
                        wspace=0.24)
    xs = [alpha * 100.0 for alpha in ALPHAS]

    for ax, key, title in ((axes[0], "var_", "VaR"),
                           (axes[1], "cvar", "CVaR")):
        for ticker in TICKERS:
            values = [result[ticker]["profile"][key][a] * 100.0
                      for a in ALPHAS]
            ax.plot(xs, values, color=COLOR[ticker], lw=1.2, marker="o",
                    markersize=3.0, label=LABELS[ticker])
            ax.annotate(ru(values[-1], 6), xy=(xs[-1], values[-1]),
                        xytext=(3, 0), textcoords="offset points",
                        fontsize=6.5, family=FONT, color=COLOR[ticker],
                        va="center")
        ax.set_title(title + ", % от вложенной суммы", fontsize=7.5,
                     family=FONT, pad=4)
        ax.set_xlabel("доверительная вероятность, %", fontsize=7,
                      family=FONT, color="#1b1b1b")
        ax.set_xticks(xs)
        ax.set_xticklabels([ru(x, 0) for x in xs], fontsize=6.5,
                           family=FONT)
        ax.set_xlim(94.7, 100.5)
        ax.grid(True, color="#e3e7ec", lw=0.5)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.tick_params(labelsize=6.5)
        for label in ax.get_yticklabels():
            label.set_fontfamily(FONT)
        ax.legend(fontsize=7, frameon=False, loc="upper left",
                  prop={"family": FONT, "size": 7})

    os.makedirs(OUT_DIR, exist_ok=True)
    fig.savefig(IMG_TAIL, facecolor="white")
    plt.close(fig)
    return IMG_TAIL


def build_content(rep, dates, prices, data, result):
    """Текст отчёта. Все числа берутся из интервального ряда."""
    prof = {t: result[t]["profile"] for t in TICKERS}
    ser = {t: result[t]["series"] for t in TICKERS}
    loss = {t: result[t]["loss_series"] for t in TICKERS}
    n = prof[TICKERS[0]]["n"]

    by_std = sorted(TICKERS, key=lambda t: prof[t]["std"], reverse=True)
    by_mean = sorted(TICKERS, key=lambda t: prof[t]["mean"], reverse=True)
    by_semi = sorted(TICKERS, key=lambda t: prof[t]["lstd"], reverse=True)
    by_var99 = sorted(TICKERS, key=lambda t: prof[t]["var_"][0.99],
                      reverse=True)
    by_cvar99 = sorted(TICKERS, key=lambda t: prof[t]["cvar"][0.99],
                       reverse=True)

    def label(ticker):
        return LABELS[ticker]

    def interval(a, b):
        return "[%s; %s]" % (ru(a * 100.0, 6), ru(b * 100.0, 6))

    # ------------------------------------------------------------------
    rep.h1("Цель работы")
    rep.p("Цель работы - изучить меры риска и применить их к дневным "
          "доходностям акций трёх компаний. В работе строятся интервальные "
          "вариационные ряды, по ним вычисляются среднее, дисперсия, "
          "стандартное отклонение, левосторонние полудисперсию и "
          "полуотклонение, VaR и CVaR, а затем результаты сопоставляются "
          "между бумагами.")
    rep.p("Вариант 3: Bayer (BAYN.DE), Merck & Co (MRK) и Sanofi (SAN.PA). "
          "Данные - дневные цены закрытия за период с %s по %s. "
          "Доходность считается в долях, а в таблицах переводится в "
          "проценты; для дисперсий используется единица (п.п.)², то есть "
          "квадрат процентного пункта."
          % (dates[0].strftime("%d.%m.%Y"),
             dates[-1].strftime("%d.%m.%Y")))

    rep.p("Для достижения цели решаются следующие задачи:")
    rep.numbers([
        "загрузить и выровнять по датам цены закрытия трёх акций;",
        "построить интервальные вариационные ряды дневных доходностей;",
        "вычислить по рядам моменты и левосторонние полумеры;",
        "преобразовать ряд доходности в распределение убыточности и найти "
        "VaR и CVaR;",
        "сравнить бумаги по полученным мерам и сформулировать выводы.",
    ])

    # ------------------------------------------------------------------
    rep.h1("Исходные данные")
    rep.p("Используются скорректированные цены закрытия (auto_adjust): "
          "дивиденды и дробление акций не создают ложных провалов в ряду "
          "доходностей. Даты выровнены по общим торговым дням, пропуски и "
          "дубликаты устранены, поэтому каждая бумага имеет одинаковое "
          "число наблюдений n = %d." % n)

    rows = []
    for ticker in TICKERS:
        values = prices[ticker]
        rows.append((
            "%s (%s)" % (LABELS[ticker], ticker),
            CURRENCY[ticker],
            ru(values[0], 6),
            ru(min(values), 6),
            ru(max(values), 6),
            ru(values[-1], 6),
        ))
    rep.table(
        ("Акция", "Валюта", "Начало периода", "Минимум", "Максимум",
         "Конец периода"),
        rows, (2.6, 1.7, 3.0, 2.8, 2.8, 2.8), size=10,
        caption="Таблица 1. Цены закрытия, %s - %s"
                % (dates[0].strftime("%d.%m.%Y"),
                   dates[-1].strftime("%d.%m.%Y")))

    rep.p("Нормированная динамика цен показана на рисунке 1: все ряды "
          "начинаются со 100 %, поэтому видны различия в накопленной "
          "доходности, а не в абсолютных ценах и валютах.")
    rep.figure(IMG_PRICES, "Рисунок 1. Динамика цен закрытия, % от "
               "начального уровня", width_cm=16.5)

    # ------------------------------------------------------------------
    rep.h1("Математическая постановка задачи")
    rep.p("Эмпирический закон распределения задаётся интервальным "
          "вариационным рядом. Выборка из n наблюдений разбивается на k "
          "интервалов равной длины h; для каждого интервала указываются "
          "середина x_j, частота n_j и относительная частота p_j. Все "
          "дальнейшие меры считаются по этому ряду, а не по исходным "
          "наблюдениям, поэтому каждое число отчёта можно пересчитать по "
          "таблицам вариационных рядов.")
    rep.formula("p_j = n_j / n,   Σ p_j = 1.")
    rep.formula("μ = M(X) = Σ x_j · p_j.")
    rep.formula("D(X) = Σ (x_j − μ)² · p_j,   σ(X) = √D(X).")
    rep.p("Дисперсия и стандартное отклонение измеряются в (п.п.)² и "
          "процентах соответственно. Левосторонняя полудисперсия LVar(X) "
          "учитывает только неблагоприятные отклонения x_j ≤ μ. "
          "Вероятности уже входят в слагаемые p_j, поэтому LVar не делится "
          "на P(X ≤ μ): это часть общей дисперсии, а не дисперсия при "
          "условии X ≤ μ. Вклады левого и правого хвостов в сумме дают "
          "D(X), так что LVar ≤ D(X).")
    rep.formula("LVar(X) = Σ_{x_j ≤ μ} (x_j − μ)² · p_j.")
    rep.formula("Lσ(X) = √LVar(X).")
    rep.p("Для перехода к риску убытков вводится величина Y = −X. "
          "Интервалы доходности при этом зеркально переставляются, а "
          "вероятности не меняются. Доверительный уровень α задаёт "
          "правый хвост распределения убыточности:")
    rep.formula("VaR_α(Y) = min { y : P(Y ≤ y) ≥ α }.")
    rep.formula("CVaR_α(Y) = E[Y | Y > VaR_α(Y)] = "
                "Σ_{y_j > VaR_α} y_j · p_j / Σ_{y_j > VaR_α} p_j.")
    rep.p("Последняя формула использует строгое неравенство: в средний "
          "убыток попадают только интервалы, лежащие дальше границы VaR. "
          "Поэтому фактическая вероятность хвоста может быть чуть меньше "
          "1 − α, и это не является ошибкой расчёта.")

    # ------------------------------------------------------------------
    rep.h1("Эмпирические законы распределения доходностей")
    rep.p("Число интервалов оценивается по формуле Стерджиса:")
    rep.formula("k = 1 + 3,322 · lg n = 1 + 3,322 · lg %d ≈ %s."
                % (n, ru(1.0 + 3.322 * math.log10(n), 6)))
    rep.p("Округление даёт k = %d. Оценка k ≈ √n ≈ %d даёт величину того "
          "же порядка, но заметно больше; выбрано k = %d, потому что при "
          "большем числе интервалов относительные частоты становятся "
          "неустойчивыми, а при меньшем теряется форма распределения."
          % (ser[TICKERS[0]]["k"], int(round(math.sqrt(n))),
             ser[TICKERS[0]]["k"]))

    for index, ticker in enumerate(TICKERS):
        item = ser[ticker]
        rows = []
        for i in range(item["k"]):
            rows.append((
                interval(item["edges"][i], item["edges"][i + 1]),
                ru(item["mids"][i] * 100.0, 6),
                str(item["counts"][i]),
                ru(item["freq"][i], 6),
                ru(item["cum"][i], 6),
            ))
        rep.table(
            ("Интервал доходности, %", "Середина x_j, %", "n_j", "p_j",
             "F(x_j)"),
            rows, (6.0, 3.4, 1.4, 2.6, 3.0), size=10, keep_together=True,
            caption="Таблица %d. Вариационный ряд доходности %s"
                    % (index + 2, label(ticker)))
        rep.spacer(4)

    rep.figure(IMG_DIST, "Рисунок 2. Полигоны относительных частот "
               "дневных доходностей", width_cm=16.5)

    widths = ", ".join("%s - %s %%" % (label(t), ru(ser[t]["h"] * 100.0, 6))
                       for t in TICKERS)
    rep.p("Ширина интервала h различна: %s. Уже всего интервалы у %s, "
          "шире всего - у %s, что уже указывает на разный размах дневных "
          "колебаний. Все три ряда одновершинные, с длинными хвостами: "
          "основная масса наблюдений сосредоточена в нескольких центральных "
          "интервалах, а редкие крайние интервалы отвечают за крупные "
          "падения и рост." % (widths, label(by_std[-1]), label(by_std[0])))
    rep.p("Сумма частот каждого ряда равна n = %d, а накопленная частота "
          "последнего интервала равна единице. Это подтверждает, что "
          "группировка выполнена без потери наблюдений." % n)

    rep.p("Алгоритм построения ряда приведён в листинге 1. Границы "
          "считаются по минимуму и максимуму выборки, номер интервала - "
          "через int((x - lo) / h), а максимум отдельно относится к "
          "последнему интервалу.")
    rep.code(CODE_SERIES, size=9.5)
    rep.p("Листинг 1. Построение интервального вариационного ряда")
    rep.p("В коде номер интервала вычисляется как int((x - lo) / h); "
          "для максимального наблюдения этот номер равен k, поэтому он "
          "принудительно относится к последнему интервалу. Пустые "
          "интервалы не удаляются: они сохраняют нулевую частоту и нужны "
          "для восстановления формы распределения.")
    rep.spacer(8)

    # ------------------------------------------------------------------
    rep.h1("Оценка мер риска по интервальному ряду")
    rep.p("По формулам для дискретной случайной величины получены "
          "характеристики, приведённые в таблице 5. Среднее и стандартное "
          "отклонение измеряются в процентах, дисперсия и полудисперсия - "
          "в (п.п.)², полуотклонение - в процентах.")
    rows = []
    for ticker in TICKERS:
        p = prof[ticker]
        rows.append((
            label(ticker),
            ru(p["mean"] * 100.0, 6),
            ru(p["var"] * 10000.0, 6),
            ru(p["std"] * 100.0, 6),
            ru(p["lvar"] * 10000.0, 6),
            ru_trunc(p["lstd"] * 100.0, 5),
            ru(p["left_mass"], 6),
        ))
    rep.table(
        ("Акция", "μ, %", "D, (п.п.)²", "σ, %", "LVar, (п.п.)²",
         "Lσ, %", "P(X ≤ μ)"),
        rows, (2.5, 2.1, 2.4, 2.0, 2.6, 2.0, 2.2), size=10,
        caption="Таблица 5. Моменты и левосторонние полумеры")

    rep.p("Наибольшая средняя доходность у %s (%s %%), наименьшая - у %s "
          "(%s %%). По стандартному отклонению порядок такой: %s. "
          "Размах σ между крайними бумагами составляет %s процентного "
          "пункта, то есть риск различается заметно."
          % (label(by_mean[0]), ru(prof[by_mean[0]]["mean"] * 100.0, 6),
             label(by_mean[-1]), ru(prof[by_mean[-1]]["mean"] * 100.0, 6),
             ", ".join("%s (%s %%)" % (label(t), ru(prof[t]["std"] * 100.0, 6))
                       for t in by_std),
             ru((prof[by_std[0]]["std"] - prof[by_std[-1]]["std"]) * 100.0, 6)))

    bay = prof[TICKERS[0]]
    left = [(x, p, (x - bay["mean"]) ** 2 * p)
            for x, p in zip(ser[TICKERS[0]]["mids"],
                            ser[TICKERS[0]]["freq"])
            if x <= bay["mean"]]
    main = max(left, key=lambda row: row[2])
    numerator = sum(row[2] for row in left)
    rep.p("Покажем расчёт левосторонней полудисперсии на примере %s. "
          "Среднее по ряду μ = %s %%. Левее среднего лежат %s с суммарной "
          "вероятностью P(X ≤ μ) = %s. Сумма взвешенных квадратов "
          "отклонений по этим интервалам равна %s (п.п.)², поэтому "
          "LVar = %s (п.п.)², или %s %% от D = %s (п.п.)², а Lσ = %s %%."
          % (label(TICKERS[0]), ru(bay["mean"] * 100.0, 6),
             plural(len(left), "интервал", "интервала", "интервалов"),
             ru(bay["left_mass"], 6), ru(numerator * 10000.0, 6),
             ru(numerator * 10000.0, 6),
             ru(bay["left_share"] * 100.0, 4),
             ru(bay["var"] * 10000.0, 6),
             ru_trunc(bay["lstd"] * 100.0, 5)))
    rep.p("Наибольший вклад в LVar даёт интервал с серединой %s %%: "
          "его вероятность %s, отклонение от среднего %s %%, а вклад "
          "%s (п.п.)². Нормировать LVar на вероятность левой части не "
          "нужно: p_j уже входит в каждое слагаемое. Поэтому LVar - это "
          "часть общей дисперсии, а не условная дисперсия: LVar ≤ D, и "
          "вклады левого и правого хвостов в сумме дают D."
          % (ru(main[0] * 100.0, 6), ru(main[1], 6),
             ru((bay["mean"] - main[0]) * 100.0, 6),
             ru(main[2] * 10000.0, 6)))
    rep.p("По Lσ порядок такой: %s. Он совпадает с порядком по σ: у более "
          "волатильной бумаги левый хвост даёт и большее абсолютное "
          "отклонение. При этом Lσ меньше σ, потому что учитывает только "
          "левую часть распределения."
          % ", ".join("%s (%s %%)" % (label(t),
                                      ru_trunc(prof[t]["lstd"] * 100.0, 5))
                      for t in by_semi))

    rep.p("Моменты и полудисперсия вычисляются по серединам и вероятностям "
          "интервалов (листинг 2); отдельный проход по исходным "
          "наблюдениям не нужен.")
    rep.code(CODE_MOMENTS, size=9.5)
    rep.p("Листинг 2. Моменты и левосторонняя полудисперсия")
    rep.p("Функция grouped_left_contribution возвращает LVar и вероятность "
          "левой части: второе значение используется как P(X ≤ μ). "
          "В сумму попадают интервалы, середина которых не больше "
          "среднего; поэтому P(X ≤ μ) в таблице 5 является суммой p_j по "
          "таким интервалам.")
    rep.spacer(8)

    # ------------------------------------------------------------------
    rep.h1("VaR и CVaR убыточности")
    rep.p("Ряд доходности преобразуется в ряд убыточности Y = −X: "
          "интервалы зеркально переставляются по возрастанию убытка, "
          "середины меняют знак, вероятности остаются прежними. "
          "Преобразование и расчёт хвостовых мер реализованы в листинге 3. "
          "В таблицах 6-8 для каждого интервала убыточности указаны "
          "середина y_j, вероятность p_j и накопленная вероятность F(y_j). "
          "По этому распределению непосредственно находятся VaR и CVaR.")
    rep.code(CODE_TAIL, size=9.5)
    rep.p("Листинг 3. Убыточность, VaR и CVaR")
    rep.spacer(8)
    for index, ticker in enumerate(TICKERS):
        item = loss[ticker]
        rows = []
        for i in range(len(item["mids"])):
            rows.append((
                ru(item["mids"][i] * 100.0, 6),
                ru(item["freq"][i], 6),
                ru(item["cum"][i], 6),
            ))
        rep.table(
            ("y_j, %", "p_j", "F(y_j)"),
            rows, (3.2, 2.6, 3.0), size=10,
            caption="Таблица %d. Распределение убыточности %s"
                    % (index + 6, label(ticker)))
        rep.spacer(4)

    rows = []
    for ticker in TICKERS:
        p = prof[ticker]
        rows.append((
            label(ticker),
            ru(p["var_"][0.95] * 100.0, 6), ru(p["cvar"][0.95] * 100.0, 6),
            ru(p["var_"][0.97] * 100.0, 6), ru(p["cvar"][0.97] * 100.0, 6),
            ru(p["var_"][0.99] * 100.0, 6), ru(p["cvar"][0.99] * 100.0, 6),
        ))
    rep.table(
        ("Акция", "VaR 0,95", "CVaR 0,95", "VaR 0,97", "CVaR 0,97",
         "VaR 0,99", "CVaR 0,99"),
        rows, (2.4, 2.3, 2.4, 2.3, 2.4, 2.3, 2.4), size=10,
        caption="Таблица 9. VaR и CVaR дневной убыточности, % от суммы")

    p = prof[TICKERS[0]]
    threshold = p["var_"][0.99]
    tail_rows = [(y, q) for y, q in zip(loss[TICKERS[0]]["mids"],
                                        loss[TICKERS[0]]["freq"])
                 if y > threshold + 1e-15]
    tail_mass = sum(q for _, q in tail_rows)
    tail_mean = sum(y * q for y, q in tail_rows) / tail_mass
    rep.p("Пример расчёта для %s при α = 0,99. По накопленной "
          "вероятности находим первый интервал, где F(y) ≥ 0,99; его "
          "середина даёт VaR = %s %%. Строго правее этой границы лежат "
          "%s с суммарной вероятностью %s. Их средневзвешенная "
          "середина равна %s %%, это и есть CVaR. Превышение CVaR над VaR "
          "составляет %s процентного пункта."
          % (label(TICKERS[0]), ru(threshold * 100.0, 6),
             plural(len(tail_rows), "интервал", "интервала", "интервалов"),
             ru(tail_mass, 6),
             ru(tail_mean * 100.0, 6),
             ru((tail_mean - threshold) * 100.0, 6)))

    rep.p("Порядок бумаг по VaR на уровне 0,99: %s. По CVaR: %s. "
          "Совпадение значений VaR на соседних уровнях 0,95 и 0,97 "
          "объясняется дискретностью интервального ряда: оба уровня могут "
          "попадать в один и тот же интервал, и тогда граница не меняется."
          % (", ".join("%s (%s %%)" % (label(t),
                                       ru(prof[t]["var_"][0.99] * 100.0, 6))
                       for t in by_var99),
             ", ".join("%s (%s %%)" % (label(t),
                                       ru(prof[t]["cvar"][0.99] * 100.0, 6))
                       for t in by_cvar99)))
    rep.p("Зависимость хвостовых мер от доверительной вероятности показана "
          "на рисунке 3. С ростом α обе меры не убывают, а CVaR остаётся "
          "выше VaR, поскольку усредняет убытки строго за границей "
          "квантиля.")
    rep.figure(IMG_TAIL, "Рисунок 3. VaR и CVaR убыточности при "
               "доверительных вероятностях 0,95, 0,97 и 0,99",
               width_cm=16.5)

    # ------------------------------------------------------------------
    rep.h1("Выводы")
    rep.p("В работе построены интервальные вариационные ряды дневных "
          "доходностей трёх акций за период с %s по %s (n = %d). Все меры "
          "риска - среднее, дисперсия, стандартное отклонение, "
          "левосторонние полудисперсия и полуотклонение, VaR и CVaR - "
          "рассчитаны по этим рядам, поэтому они согласованы между собой и "
          "воспроизводимы по таблицам."
          % (dates[0].strftime("%d.%m.%Y"),
             dates[-1].strftime("%d.%m.%Y"), n))
    rep.numbers([
        "Наибольшее стандартное отклонение у %s (%s %%), наименьшее - "
        "у %s (%s %%)."
        % (label(by_std[0]), ru(prof[by_std[0]]["std"] * 100.0, 6),
           label(by_std[-1]), ru(prof[by_std[-1]]["std"] * 100.0, 6)),
        "По левостороннему полуотклонению Lσ первое место занимает %s "
        "(%s %%), что указывает на более тяжёлый левый хвост относительно "
        "среднего."
        % (label(by_semi[0]),
           ru_trunc(prof[by_semi[0]]["lstd"] * 100.0, 5)),
        "На уровне 0,99 наибольший VaR у %s (%s %%), наибольший CVaR - "
        "у %s (%s %%)."
        % (label(by_var99[0]), ru(prof[by_var99[0]]["var_"][0.99] * 100.0, 6),
           label(by_cvar99[0]),
           ru(prof[by_cvar99[0]]["cvar"][0.99] * 100.0, 6)),
        "Средняя доходность выше всего у %s (%s %%), поэтому выбор "
        "бумаги зависит от готовности инвестора принимать риск: "
        "наибольшая доходность сопровождается и наибольшими хвостовыми "
        "убытками."
        % (label(by_mean[0]), ru(prof[by_mean[0]]["mean"] * 100.0, 6)),
    ])
    rep.p("Таким образом, интервальный ряд позволяет получить полный "
          "набор мер риска из одного и того же эмпирического закона. "
          "VaR показывает границу убытка, CVaR - его среднюю величину за "
          "границей, а Lσ дополняет стандартное отклонение "
          "характеристикой только неблагоприятных отклонений.")


def build():
    dates, prices = risk_data.load_csv()
    _, data = risk_data.load()
    result = risk_measures.compute(data, ALPHAS)

    chart_prices(dates, prices)
    chart_distributions(result)
    chart_tail(result)

    meta = ReportMeta(
        lab_no="1",
        page_title=PAGE_TITLE,
        full_title=SHORT_TITLE,
        frame_title="Меры риска",
        dept="Институт информатики, математики и робототехники",
        discipline="Принятие решений в условиях неопределенности",
        teacher="Прокудина Е. И.",
        frame_teacher="Прокудина Е.И.",
        group="КАИД-104М",
        student="Воробьев И. С.",
        out_name=OUT_NAME,
    )
    rep = Report(meta)
    rep.prepare()
    build_content(rep, dates, prices, data, result)
    return rep.save()


if __name__ == "__main__":
    print(build())
