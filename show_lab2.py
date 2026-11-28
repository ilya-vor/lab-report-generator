# -*- coding: utf-8 -*-
"""Показать результаты ЛР №2 «Стохастическое доминирование» без файлов.

Аналог ``kod/show_lab.py`` для второй лабораторной работы: скрипт заново
считает законы распределения дневных доходностей, печатает таблицы 1-7 в
консоль и открывает рисунки 1-7 в отдельных окнах matplotlib. Ничего не
сохраняется на диск.

Запуск:

    python show_lab2.py
    python show_lab2.py --data labs/data/risk_quotes.csv
    python show_lab2.py --no-figures
    python show_lab2.py --no-tables

Окна нужно закрыть вручную; после последнего окна скрипт завершится.
"""
import argparse
import sys

from labs import dominance, risk_data, risk_measures
from labs import lab_dominance as view


# ---------------------------------------------------------------------------
# Печать таблиц в Markdown
# ---------------------------------------------------------------------------
def md_table(header, rows, align=None):
    """Таблица в Markdown: как tables.md у первой лабораторной."""
    align = align or ["---"] * len(header)
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join(align) + "|"]
    lines += ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    return "\n".join(lines)


def print_tables(series_list, profiles, dists, comparisons, pairs):
    """Печатает таблицы 1-7 так же, как они выглядят в отчёте."""
    label = lambda t: view.LABELS.get(t, t)

    print("## Таблица 1. Характеристики дневных доходностей, %\n")
    rows = []
    for ticker in series_list:
        prof = profiles[ticker]
        rows.append((
            "%s (%s)" % (label(ticker), ticker),
            view.pct(prof["mean"], 3),
            view.pct(prof["std"], 3),
            view.pct(prof["var"][0.99], 2),
            view.pct(dists[ticker].F(0.0), 2),
            view.pct(dists[ticker].F(-0.03), 2),
        ))
    print(md_table(("Акция", "E(X)", "Std", "VaR(0,99)", "P(X ≤ 0)",
                    "P(X ≤ −3)"), rows,
                   ("---", "---:", "---:", "---:", "---:", "---:")))

    for i, ticker in enumerate(series_list, 2):
        dist = dists[ticker]
        print("\n## Таблица %d. Закон распределения доходности %s\n"
              % (i, label(ticker)))
        rows = []
        for j, (x, p, f) in enumerate(zip(dist.x, dist.p, dist.cum)):
            left = dist.edges[j]
            right = dist.edges[j + 1]
            rows.append(("[%s; %s%s" % (view.pct(left), view.pct(right),
                                        "]" if j == len(dist.x) - 1 else ")"),
                         view.pct(x, 2), view.ru(p, 4), view.ru(f, 4)))
        print(md_table(("Интервал, %", "x_j, %", "p_j", "F(x_j)"), rows,
                       ("---", "---:", "---:", "---:")))

    total = len(series_list) + 2
    print("\n## Таблица %d. Проверка критериев для трёх пар\n" % total)
    rows = []
    for a, b in pairs:
        item = comparisons[(a, b)]
        first, second = item["first"], item["second"]
        roots = ", ".join(view.ru(x * 100.0, 2) for x in second["crossings"])
        rows.append((
            "%s – %s" % (label(a), label(b)),
            "%s @ %s" % (view.pct(first["max"], 2),
                         view.pct(first["argmax"], 2)),
            "%s @ %s" % (view.pct(first["min"], 2),
                         view.pct(first["argmin"], 2)),
            "%s @ %s" % (view.ru(second["max"] * 100.0, 3),
                         view.pct(second["argmax"], 2)),
            "%s @ %s" % (view.ru(second["min"] * 100.0, 3),
                         view.pct(second["argmin"], 2)),
            roots or "нет",
            "нет" if first["verdict"] == "none" else "есть",
            "нет" if second["verdict"] == "none" else "есть",
        ))
    print(md_table(("Пара", "max(F₁−F₂), %", "min(F₁−F₂), %", "max ∫, п.п.",
                    "min ∫, п.п.", "∫ = 0 при t, %", "СД-1", "СД-2"), rows))


# ---------------------------------------------------------------------------
# Окна с рисунками
# ---------------------------------------------------------------------------
def show_figures(dists, comparisons, pairs):
    """Открывает рисунки 1-7 в интерактивных окнах matplotlib."""
    import matplotlib.pyplot as plt

    # Модуль отчёта включает Agg при импорте; для окон нужен интерактивный
    # бэкенд, поэтому переключаем его на лету.
    for backend in ("TkAgg", "QtAgg", "Qt5Agg", "GTK3Agg", "WXAgg"):
        try:
            plt.switch_backend(backend)
            break
        except Exception:
            continue

    figures, titles = [], []

    def add(fig, title):
        figures.append(fig)
        titles.append(title)

    add(view.fig_all(dists),
        "Рисунок 1. Функции распределения трёх акций")
    for index, (a, b) in enumerate(pairs, 2):
        add(view.fig_cdf(a, b, dists),
            "Рисунок %d. Функции распределения %s и %s"
            % (index, view.LABELS.get(a, a), view.LABELS.get(b, b)))
    for index, (a, b) in enumerate(pairs, len(pairs) + 2):
        add(view.fig_diff(a, b, comparisons[(a, b)]),
            "Рисунок %d. Разность функций распределения %s и %s"
            % (index, view.LABELS.get(a, a), view.LABELS.get(b, b)))

    for figure, title in zip(figures, titles):
        manager = getattr(figure.canvas, "manager", None)
        if manager is not None:
            manager.set_window_title(title)
    print("Открыто окон: %d. Закройте их, чтобы завершить скрипт."
          % len(figures))
    sys.stdout.flush()
    plt.show()


# ---------------------------------------------------------------------------
# Запуск
# ---------------------------------------------------------------------------
def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Показать таблицы и рисунки ЛР «Стохастическое "
                    "доминирование»")
    parser.add_argument("--data", default=None,
                        help="CSV с ценами закрытия (по умолчанию файл "
                             "первой лабораторной работы)")
    parser.add_argument("--no-tables", action="store_true",
                        help="не печатать таблицы")
    parser.add_argument("--no-figures", action="store_true",
                        help="не открывать окна с рисунками")
    args = parser.parse_args(argv)

    if args.data:
        dates, prices = risk_data.load_csv(args.data)
        data = {t: risk_data.returns(s) for t, s in prices.items()}
    else:
        dates, data = risk_data.load()

    series_list = [t for t in risk_data.TICKERS if t in data]
    series = {t: risk_measures.variation_series(data[t]) for t in series_list}
    dists, comparisons, _ = dominance.build(series_list, series)
    # порядок пар как в отчёте: нумерация рисунков 2-4 и 5-7 совпадает
    pairs = [pair for pair in view.ORDER if pair in comparisons]
    profiles = {t: {
        "mean": risk_measures.grouped_moments(series[t])[0],
        "std": risk_measures.grouped_moments(series[t])[1] ** 0.5,
        "var": {a: risk_measures.grouped_var(
            risk_measures.grouped_loss_series(series[t]), a)
            for a in (0.99,)},
    } for t in series_list}

    print("Наблюдений: %d, период: %s … %s\n"
          % (len(dates), dates[0], dates[-1]))
    if not args.no_tables:
        print_tables(series_list, profiles, dists, comparisons, pairs)
    if not args.no_figures:
        show_figures(dists, comparisons, pairs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
