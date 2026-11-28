# -*- coding: utf-8 -*-
"""Лабораторная работа №2 «Стохастическое доминирование».

Один файл, только стандартная библиотека и matplotlib.

Скрипт читает дневные цены закрытия трёх акций, считает доходности
X = (P_t - P_(t-1)) / P_(t-1), строит по ним интервальный вариационный ряд
(дискретная величина: значения - середины интервалов x_j, вероятности -
частоты p_j), затем для каждой пары бумаг проверяет стохастическое
доминирование 1-го и 2-го порядков:

    F_A(x) <= F_B(x) при всех x                - доминирование 1-го порядка;
    integral(F_A - F_B)dx <= 0 при всех t      - доминирование 2-го порядка.

Печатает три таблицы в консоль и открывает рисунки 1-7 в окнах matplotlib.

Запуск:
    python show_lab2.py
"""
import csv
import math
import os

import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "labs", "data", "risk_quotes.csv")
TICKERS = ("BAYN.DE", "MRK", "SAN.PA")
LABELS = {"BAYN.DE": "Bayer", "MRK": "Merck", "SAN.PA": "Sanofi"}
COLOR = {"BAYN.DE": "#1f4e79", "MRK": "#b06a2c", "SAN.PA": "#2e7d32"}


# ---------------------------------------------------------------------------
# Данные и вариационный ряд
# ---------------------------------------------------------------------------
def load_prices(path=CSV_PATH):
    """CSV с колонкой date и колонками тикеров. Возвращает (даты, цены)."""
    with open(path, encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        names = [name.strip() for name in header[1:]]
        dates, prices = [], {name: [] for name in names}
        for row in reader:
            dates.append(row[0])
            for name, value in zip(names, row[1:]):
                prices[name].append(float(value))
    return dates, prices


def returns(prices):
    """Простые дневные доходности в долях."""
    return [(b - a) / a for a, b in zip(prices, prices[1:])]


def variation_series(values):
    """Интервальный ряд: число интервалов по Стерджессу, частоты, F."""
    n = len(values)
    k = max(1, int(round(1.0 + 3.322 * math.log10(n))))
    lo, hi = min(values), max(values)
    h = (hi - lo) / k
    counts = [0] * k
    for x in values:
        counts[min(int((x - lo) / h), k - 1)] += 1
    edges = [lo + h * i for i in range(k + 1)]
    mids = [(edges[i] + edges[i + 1]) / 2.0 for i in range(k)]
    freq = [c / n for c in counts]
    cum, acc = [], 0.0
    for p in freq:
        acc += p
        cum.append(acc)
    return {"edges": edges, "mids": mids, "freq": freq, "cum": cum}


# ---------------------------------------------------------------------------
# Дискретная величина, заданная рядом
# ---------------------------------------------------------------------------
class Distribution:
    """Значения x_j с вероятностями p_j; F(x) - ступенчатая."""

    def __init__(self, series):
        self.x = series["mids"]
        self.p = series["freq"]
        self.cum = series["cum"]

    def F(self, x):
        """P(X <= x): накопленная вероятность левее x включительно."""
        total = 0.0
        for value, prob in zip(self.x, self.p):
            if value > x:
                break
            total += prob
        return total

    def jump(self, x):
        """Скачок F в точке x (0, если такой середины нет)."""
        for value, prob in zip(self.x, self.p):
            if abs(value - x) < 1e-12:
                return prob
        return 0.0

    def S(self, x):
        """Интеграл F от -oo до x: площадь под ступенчатым графиком."""
        total = 0.0
        level = 0.0
        previous = self.x[0]
        for value, prob in zip(self.x, self.p):
            if x <= value:
                return total + level * (x - previous)
            total += level * (value - previous)
            level += prob
            previous = value
        return total + level * (x - self.x[-1])


# ---------------------------------------------------------------------------
# Критерии доминирования
# ---------------------------------------------------------------------------
def analyse(diffs, grid, tol=1e-9, step=False):
    """Экстремумы разности и точки перемены знака."""
    lo = min(range(len(diffs)), key=lambda i: diffs[i])
    hi = max(range(len(diffs)), key=lambda i: diffs[i])
    signs = [1 if v > tol else (-1 if v < -tol else 0) for v in diffs]

    crossings, previous = [], None
    for i, sign in enumerate(signs):
        if not sign:
            continue
        if previous is not None and sign != previous:
            span = diffs[i] - diffs[i - 1]
            ratio = -diffs[i - 1] / span if span else 0.0
            crossings.append(grid[i] if step else
                             grid[i - 1] + ratio * (grid[i] - grid[i - 1]))
        previous = sign

    if max(diffs) <= tol:
        verdict = "a"
    elif min(diffs) >= -tol:
        verdict = "b"
    else:
        verdict = "none"
    return {"min": diffs[lo], "max": diffs[hi],
            "argmin": grid[lo], "argmax": grid[hi],
            "crossings": crossings, "verdict": verdict}


def compare(box_a, box_b, points=1600):
    """Разности F_A - F_B и их интегралы на общей сетке точек."""
    lo = min(box_a.x[0], box_b.x[0])
    hi = max(box_a.x[-1], box_b.x[-1])
    grid = sorted(set(box_a.x) | set(box_b.x)
                  | {lo + (hi - lo) * i / float(points)
                     for i in range(points + 1)})
    d1 = [box_a.F(x) - box_b.F(x) for x in grid]
    d2 = [box_a.S(x) - box_b.S(x) for x in grid]
    return {"grid": grid, "d1": d1, "d2": d2,
            "first": analyse(d1, grid, step=True),
            "second": analyse(d2, grid)}


# ---------------------------------------------------------------------------
# Оформление чисел и таблиц
# ---------------------------------------------------------------------------
def ru(value, digits=2):
    """Русская запись: запятая в дроби, минус U+2212."""
    text = ("%.*f" % (digits, value)).replace(".", ",")
    return "\u2212" + text[1:] if text.startswith("-") else text


def pct(value, digits=2):
    """Доля -> проценты."""
    return ru(value * 100.0, digits)


def md(header, rows):
    """Таблица в Markdown."""
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join(["---"] * len(header)) + "|"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Рисунки
# ---------------------------------------------------------------------------
def cdf_points(box):
    """Точки ступенчатого графика F: x_j и накопленные вероятности."""
    xs = [box.x[0] - 3.0] + box.x + [box.x[-1] + 3.0]
    ys = [0.0] + box.cum + [1.0]
    return [x * 100.0 for x in xs], ys


def style(ax, ylabel):
    ax.grid(alpha=0.25)
    ax.set_xlabel("дневная доходность, %")
    ax.set_ylabel(ylabel)
    ax.tick_params(labelsize=8)
    ax.set_xlim(-10, 12)


def fig_all(dists):
    fig, ax = plt.subplots(figsize=(9, 3.4), layout="constrained")
    for t in TICKERS:
        xs, ys = cdf_points(dists[t])
        ax.step(xs, ys, where="post", color=COLOR[t], lw=1.2, label=LABELS[t])
    ax.set_ylim(-0.03, 1.05)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    style(ax, "F(x)")
    ax.figure.suptitle("Рисунок 1. Функции распределения трёх акций")
    return fig


def fig_pair(dists, a, b, number):
    """Две функции распределения."""
    fig, ax = plt.subplots(figsize=(9, 3.2), layout="constrained")
    for t, ls in ((a, "-"), (b, "--")):
        xs, ys = cdf_points(dists[t])
        ax.step(xs, ys, where="post", color=COLOR[t], lw=1.2, ls=ls,
                label=LABELS[t])
    ax.set_ylim(-0.03, 1.05)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    style(ax, "F(x)")
    fig.suptitle("Рисунок %d. F(x): %s и %s"
                 % (number, LABELS[a], LABELS[b]))
    return fig


def fig_diff(result, a, b, number):
    """Разность F_A - F_B."""
    fig, ax = plt.subplots(figsize=(9, 3.0), layout="constrained")
    xs = [x * 100.0 for x in result["grid"]]
    diffs = [v * 100.0 for v in result["d1"]]
    ax.axhline(0.0, color="#5b6770", lw=0.8)
    ax.step(xs, diffs, where="post", color="#1b1b1b", lw=0.9)
    ax.fill_between(xs, diffs, 0.0, where=[v >= 0 for v in diffs],
                    step="post", color=COLOR[a], alpha=0.2)
    ax.fill_between(xs, diffs, 0.0, where=[v < 0 for v in diffs],
                    step="post", color=COLOR[b], alpha=0.2)
    style(ax, "F₁(x) − F₂(x), п.п.")
    fig.suptitle("Рисунок %d. Разность F(x): %s и %s"
                 % (number, LABELS[a], LABELS[b]))
    return fig


# ---------------------------------------------------------------------------
# Запуск
# ---------------------------------------------------------------------------
def main():
    # 1. Данные и законы распределения.
    dates, prices = load_prices()
    data = {t: returns(prices[t]) for t in TICKERS}
    series = {t: variation_series(data[t]) for t in TICKERS}
    dists = {t: Distribution(series[t]) for t in TICKERS}
    print("Наблюдений: %d (%s … %s)\n" % (len(data[TICKERS[0]]),
                                          dates[1], dates[-1]))

    # 2. Таблица 1: характеристики доходностей (по сгруппированному ряду).
    rows = []
    for t in TICKERS:
        dist = dists[t]
        mean = sum(x * p for x, p in zip(dist.x, dist.p))
        var = sum((x - mean) ** 2 * p for x, p in zip(dist.x, dist.p))
        # VaR(0,99) для убыточности Y = -X: уровень потерь, ниже которого
        # накоплено не более 1 % вероятности.
        var99 = -next(x for x, f in zip(dist.x, dist.cum) if f >= 0.01)
        rows.append((t, pct(mean, 3), pct(math.sqrt(var), 3), pct(var99, 2),
                     pct(dist.F(0.0), 2), pct(dist.F(-0.03), 2)))
    print(md(("Акция", "E(X), %", "Std, %", "VaR(0,99), %",
              "P(X ≤ 0), %", "P(X ≤ −3), %"), rows))

    # 3. Таблица 2: законы распределения (x_j, p_j, F(x_j)).
    for t in TICKERS:
        dist = dists[t]
        rows = [(pct(x, 2), ru(p, 4), ru(f, 4))
                for x, p, f in zip(dist.x, dist.p, dist.cum)]
        print("\n## %s\n" % LABELS[t])
        print(md(("x_j, %", "p_j", "F(x_j)"), rows))

    # 4. Таблица 3: итоги по трём парам.
    pairs = [(TICKERS[0], TICKERS[1]), (TICKERS[1], TICKERS[2]),
             (TICKERS[0], TICKERS[2])]
    comps = {pair: compare(dists[pair[0]], dists[pair[1]]) for pair in pairs}
    rows = []
    for a, b in pairs:
        d = comps[(a, b)]
        rows.append(("%s - %s" % (LABELS[a], LABELS[b]),
                     pct(d["first"]["max"], 2), pct(d["first"]["min"], 2),
                     ru(d["second"]["max"] * 100.0, 3),
                     ru(d["second"]["min"] * 100.0, 3),
                     "нет" if d["second"]["verdict"] == "none" else "есть"))
    print("\n## Проверка критериев\n")
    print(md(("Пара", "max(F₁−F₂), %", "min(F₁−F₂), %",
              "max ∫, п.п.", "min ∫, п.п.", "СД-2"), rows))

    # 5. Рисунки: 1 - три F, 2-4 - пары F, 5-7 - разности F₁ − F₂.
    figs = [fig_all(dists)]
    figs += [fig_pair(dists, a, b, i) for i, (a, b) in enumerate(pairs, 2)]
    figs += [fig_diff(comps[(a, b)], a, b, i)
             for i, (a, b) in enumerate(pairs, len(pairs) + 2)]
    print("\nОткрыто окон: %d. Закройте их, чтобы выйти." % len(figs))
    plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
