# -*- coding: utf-8 -*-
"""Показать результаты ЛР №2 «Стохастическое доминирование» без отчёта.

Скрипт заново считает законы распределения доходностей, печатает три
таблицы в консоль и открывает рисунки 1-7 в окнах matplotlib.
Ничего не сохраняется на диск.

Запуск:
    python show_lab2.py
"""
import matplotlib.pyplot as plt

from labs import dominance, risk_data, risk_measures
from labs import lab_dominance as view


def md(header, rows):
    """Таблица в Markdown: шапка, разделитель, строки."""
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join(["---"] * len(header)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def main():
    # 1. Данные: дневные доходности трёх акций.
    dates, data = risk_data.load()
    tickers = list(risk_data.TICKERS)
    print("Наблюдений: %d (%s … %s)\n" % (len(dates), dates[0], dates[-1]))

    # 2. Законы распределения, разности F и проверка критериев.
    series = {t: risk_measures.variation_series(data[t]) for t in tickers}
    dists, comps, _ = dominance.build(tickers, series)
    pairs = [pair for pair in view.ORDER if pair in comps]

    # 3. Таблица 1: характеристики доходностей.
    profile = risk_measures.compute(data)
    rows = []
    for t in tickers:
        prof = profile[t]["profile"]
        rows.append((t, view.pct(prof["mean"], 3), view.pct(prof["std"], 3),
                     view.pct(prof["var_"][0.99], 2)))
    print(md(("Акция", "E(X), %", "Std, %", "VaR(0,99), %"), rows))

    # 4. Таблица 2: законы распределения (x_j, p_j, F(x_j)).
    for t in tickers:
        dist = dists[t]
        rows = [(view.pct(x, 2), view.ru(p, 4), view.ru(f, 4))
                for x, p, f in zip(dist.x, dist.p, dist.cum)]
        print("\n## %s\n" % view.LABELS[t])
        print(md(("x_j, %", "p_j", "F(x_j)"), rows))

    # 5. Таблица 3: итоги проверки критериев по трём парам.
    rows = []
    for a, b in pairs:
        d = comps[(a, b)]
        rows.append(("%s – %s" % (view.LABELS[a], view.LABELS[b]),
                     view.pct(d["first"]["max"], 2),
                     view.pct(d["first"]["min"], 2),
                     view.ru(d["second"]["max"] * 100.0, 3),
                     view.ru(d["second"]["min"] * 100.0, 3),
                     "нет" if d["second"]["verdict"] == "none" else "есть"))
    print("\n## Проверка критериев\n")
    print(md(("Пара", "max(F₁−F₂), %", "min(F₁−F₂), %",
              "max ∫, п.п.", "min ∫, п.п.", "СД-2"), rows))

    # 6. Рисунки: 1 - три F(x), 2-4 - пары F(x), 5-7 - разности F₁ − F₂.
    try:
        plt.switch_backend("TkAgg")   # окна, а не сохранение в файлы
    except Exception:
        pass
    figs = [view.fig_all(dists)]
    figs += [view.fig_cdf(a, b, dists) for a, b in pairs]
    figs += [view.fig_diff(a, b, comps[(a, b)]) for a, b in pairs]
    for i, fig in enumerate(figs, 1):
        fig.canvas.manager.set_window_title("Рисунок %d" % i)
    print("\nОткрыто окон: %d. Закройте их, чтобы выйти." % len(figs))
    plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
