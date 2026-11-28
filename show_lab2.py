# -*- coding: utf-8 -*-
"""ЛР №2 «Стохастическое доминирование». Один файл: csv, math, matplotlib.

Читает цены закрытия -> доходности X -> интервальный ряд (x_j = середины,
p_j = частоты) -> для каждой пары бумаг проверяет:
    F_A(x) <= F_B(x)  при всех x              (1-й порядок),
    integral(F_A - F_B)dx <= 0  при всех t    (2-й порядок).
Печатает 3 таблицы и открывает рисунки 1-7.

Запуск:  python show_lab2.py
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


def load_prices(path=CSV_PATH):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    names = [name.strip() for name in rows[0][1:]]
    dates = [row[0] for row in rows[1:]]
    prices = {n: [float(row[i + 1]) for row in rows[1:]]
              for i, n in enumerate(names)}
    return dates, prices


def variation_series(values):
    n = len(values)
    k = max(1, int(round(1.0 + 3.322 * math.log10(n))))
    lo, hi = min(values), max(values)
    h = (hi - lo) / k
    counts = [0] * k
    for x in values:
        counts[min(int((x - lo) / h), k - 1)] += 1
    mids = [lo + h * (i + 0.5) for i in range(k)]
    freq = [c / n for c in counts]
    cum, total = [], 0.0
    for p in freq:
        total += p
        cum.append(total)
    return {"x": mids, "p": freq, "cum": cum}


class Distribution:

    def __init__(self, series):
        self.x, self.p, self.cum = series["x"], series["p"], series["cum"]

    def F(self, x):
        return sum(p for value, p in zip(self.x, self.p) if value <= x)

    def jump(self, x):
        return sum(p for value, p in zip(self.x, self.p)
                   if abs(value - x) < 1e-12)

    def S(self, x):
        total = level = 0.0
        previous = self.x[0]
        for value, p in zip(self.x, self.p):
            if x <= value:
                return total + level * (x - previous)
            total += level * (value - previous)
            level += p
            previous = value
        return total + level * (x - self.x[-1])


def analyse(diffs, grid, tol=1e-9):
    lo = min(range(len(diffs)), key=lambda i: diffs[i])
    hi = max(range(len(diffs)), key=lambda i: diffs[i])
    signs = [1 if v > tol else (-1 if v < -tol else 0) for v in diffs]
    crossings, previous = [], None
    for i, sign in enumerate(signs):
        if sign and previous is not None and sign != previous:
            span = diffs[i] - diffs[i - 1]
            ratio = -diffs[i - 1] / span if span else 0.0
            crossings.append(grid[i - 1] + ratio * (grid[i] - grid[i - 1]))
        previous = sign or previous
    return {"min": diffs[lo], "max": diffs[hi], "argmin": grid[lo],
            "argmax": grid[hi], "crossings": crossings,
            "verdict": ("a" if max(diffs) <= tol else
                        "b" if min(diffs) >= -tol else "none")}


def compare(a, b, points=1600):
    lo, hi = min(a.x[0], b.x[0]), max(a.x[-1], b.x[-1])
    grid = sorted(set(a.x) | set(b.x)
                  | {lo + (hi - lo) * i / float(points)
                     for i in range(points + 1)})
    d1 = [a.F(x) - b.F(x) for x in grid]
    d2 = [a.S(x) - b.S(x) for x in grid]
    return {"grid": grid, "d1": d1,
            "first": analyse(d1, grid), "second": analyse(d2, grid)}


def ru(value, digits=2):
    text = ("%.*f" % (digits, value)).replace(".", ",")
    return "\u2212" + text[1:] if text.startswith("-") else text


def pct(value, digits=2):
    return ru(value * 100.0, digits)


def md(header, rows):
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join(["---"] * len(header)) + "|"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


def plot(dists, pairs, comps):
    figs = []

    def new(title, height=3.2):
        fig, ax = plt.subplots(figsize=(9, height), layout="constrained")
        ax.grid(alpha=0.25)
        ax.set_xlim(-10, 12)
        ax.set_xlabel("дневная доходность, %")
        ax.tick_params(labelsize=8)
        figs.append(fig)
        fig.suptitle(title)
        return ax

    def cdf(ax, ticker, ls="-"):
        box = dists[ticker]
        xs = [box.x[0] - 3.0] + box.x + [box.x[-1] + 3.0]
        ax.step([x * 100.0 for x in xs], [0.0] + box.cum + [1.0],
                where="post", color=COLOR[ticker], lw=1.2, ls=ls,
                label=LABELS[ticker])

    ax = new("Рисунок 1. Функции распределения трёх акций", 3.4)
    for t in TICKERS:
        cdf(ax, t)
    ax.set_ylabel("F(x)")
    ax.set_ylim(-0.03, 1.05)
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    for i, (a, b) in enumerate(pairs, 2):
        ax = new("Рисунок %d. F(x): %s и %s" % (i, LABELS[a], LABELS[b]))
        cdf(ax, a, "-")
        cdf(ax, b, "--")
        ax.set_ylabel("F(x)")
        ax.set_ylim(-0.03, 1.05)
        ax.legend(frameon=False, fontsize=8, loc="upper left")

    for i, (a, b) in enumerate(pairs, len(pairs) + 2):
        d = comps[(a, b)]
        ax = new("Рисунок %d. Разность F: %s и %s" % (i, LABELS[a], LABELS[b]),
                 3.0)
        xs = [x * 100.0 for x in d["grid"]]
        ys = [v * 100.0 for v in d["d1"]]
        ax.axhline(0.0, color="#5b6770", lw=0.8)
        ax.step(xs, ys, where="post", color="#1b1b1b", lw=0.9)
        for color, sign in ((COLOR[a], 1), (COLOR[b], -1)):
            ax.fill_between(xs, ys, 0.0, step="post", color=color, alpha=0.2,
                            where=[v * sign >= 0 for v in ys])
        ax.set_ylabel("F₁(x) − F₂(x), п.п.")
    return figs


def main():
    # 1. Данные -> доходности -> законы распределения.
    dates, prices = load_prices()
    data = {t: [(b - a) / a for a, b in zip(prices[t], prices[t][1:])]
            for t in TICKERS}
    dists = {t: Distribution(variation_series(data[t])) for t in TICKERS}
    print("Наблюдений: %d (%s … %s)\n"
          % (len(data[TICKERS[0]]), dates[1], dates[-1]))

    # 2. Таблица 1: характеристики доходностей по сгруппированному ряду.
    rows = []
    for t in TICKERS:
        box = dists[t]
        mean = sum(x * p for x, p in zip(box.x, box.p))
        std = (sum((x - mean) ** 2 * p for x, p in zip(box.x, box.p))) ** 0.5
        # VaR(0,99) для убыточности Y = -X: где накоплено уже 1 %.
        var99 = -next(x for x, f in zip(box.x, box.cum) if f >= 0.01)
        rows.append((t, pct(mean, 3), pct(std, 3), pct(var99, 2),
                     pct(box.F(0.0), 2), pct(box.F(-0.03), 2)))
    print(md(("Акция", "E(X), %", "Std, %", "VaR(0,99), %",
              "P(X ≤ 0), %", "P(X ≤ −3), %"), rows))

    # 3. Таблица 2: законы распределения.
    for t in TICKERS:
        box = dists[t]
        rows = [(pct(x, 2), ru(p, 4), ru(f, 4))
                for x, p, f in zip(box.x, box.p, box.cum)]
        print("\n## %s\n" % LABELS[t])
        print(md(("x_j, %", "p_j", "F(x_j)"), rows))

    # 4. Таблица 3: проверка критериев по трём парам.
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

    # 5. Рисунки.
    figs = plot(dists, pairs, comps)
    print("\nОткрыто окон: %d. Закройте их, чтобы выйти." % len(figs))
    plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
