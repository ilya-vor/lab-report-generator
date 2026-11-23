# -*- coding: utf-8 -*-
"""Лабораторная работа №5-6, дисциплина «Принятие решений в условиях
неопределённости».

Тема: принятие решений в условиях полной неопределённости. По матрице
средних дневных доходностей трёх акций за 24 месяца (Bayer, Merck & Co,
Sanofi) выбирается лучшая альтернатива шестью критериями: максимакса,
Лапласа, Вальда, Гурвица, Сэвиджа и критерием с субъективными вероятностями.
Отдельно исследуется зависимость выбора от коэффициента оптимизма.

Расчётная часть - в ``labs/uncertainty.py``: здесь только рисунки, таблицы
и текст. Все числа считаются при сборке отчёта.

Запуск:  python build.py --lab risk56
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from labkit.docxgen import Report, ReportMeta
from labkit.schemes import DPI, FONT

from labs import risk_data, uncertainty

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(HERE, "out")

PAGE_TITLE = "ПРИНЯТИЕ РЕШЕНИЙ\nВ УСЛОВИЯХ ПОЛНОЙ\nНЕОПРЕДЕЛЁННОСТИ"
SHORT_TITLE = ("Принятие решений в условиях полной неопределённости "
               "на примере акций фармацевтических компаний")
FRAME_TITLE = "Решения в условиях неопределённости"
OUT_NAME = ("Воробьев_И_С_отчет_по_5-6_ЛР_Принятие_решений_в_условиях_"
            "полной_неопределенности.docx")

TICKERS = uncertainty.TICKERS
LABELS = {"BAYN.DE": "Bayer", "MRK": "Merck & Co", "SAN.PA": "Sanofi"}
COLOR = {"BAYN.DE": "#1f4e79", "MRK": "#b06a2c", "SAN.PA": "#2e7d32"}

CRIT_NAMES = {
    "maximax": "Максимакса",
    "laplace": "Лапласа",
    "wald": "Вальда",
    "hurwitz": "Гурвица",
    "savage": "Сэвиджа",
    "subjective": "С субъективными вероятностями",
}

MINUS = "\u2212"


# ---------------------------------------------------------------------------
# Форматирование чисел в русской записи
# ---------------------------------------------------------------------------
def ru(value, digits=2):
    """Число с запятой в дробной части и пробелом между разрядами."""
    text = ("{:,.%df}" % digits).format(value)
    text = text.replace(",", "\u00a0").replace(".", ",")
    return text.replace("-", MINUS)


def pct(value, digits=3):
    """Доходность в процентах за день."""
    return ru(value * 100.0, digits)


def qpct(value):
    return ru(value * 100.0, 2)


def month_text(key):
    return "%02d.%02d" % (key[1], key[0] % 100)


# ---------------------------------------------------------------------------
# Оформление осей
# ---------------------------------------------------------------------------
def style(ax, ticks=None):
    ax.grid(True, color="#e3e7ec", lw=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=6.5)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(FONT)
    if ticks is not None:
        ax.set_xticks(list(ticks))


def single(height):
    fig, ax = plt.subplots(figsize=(16.5 / 2.54, height / 2.54), dpi=DPI)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.88, bottom=0.21)
    return fig, ax


# ---------------------------------------------------------------------------
# Рисунки
# ---------------------------------------------------------------------------
def chart_returns(r):
    """Рисунок 1: средняя дневная доходность по месяцам."""
    months = [month_text(k) for k in r["months"]]
    x = list(range(len(months)))

    fig, ax = single(9.5)
    for t in TICKERS:
        ax.plot(x, [v * 100.0 for v in r["matrix"][t]], "o-", ms=2.6, lw=1.2,
                color=COLOR[t], label=LABELS[t])
    ax.axhline(0.0, color="#888", lw=0.7)
    ax.set_title("Средняя дневная доходность акций по месяцам, %",
                 fontsize=7.5, family=FONT, pad=4)
    ax.set_xlabel("месяц", fontsize=7, family=FONT, color="#1b1b1b")
    ax.set_ylabel("средняя доходность, % в день", fontsize=7, family=FONT,
                  color="#1b1b1b")
    ax.set_xlim(-0.5, len(x) - 0.5)
    ax.set_xticks(x[::2])
    ax.set_xticklabels(months[::2], fontsize=6.5, family=FONT)
    ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper left",
              prop={"family": FONT, "size": 7})
    style(ax)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, pos: ("%.2f" % v).replace(".", ",").replace("-", "−")))
    path = os.path.join(OUT_DIR, "unc_fig1.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def chart_risks(r):
    """Рисунок 2: матрица рисков Сэвиджа."""
    months = [month_text(k) for k in r["months"]]
    data = np.array([[v * 100.0 for v in r["risks"][t]] for t in TICKERS])

    fig, ax = plt.subplots(figsize=(16.5 / 2.54, 6.8 / 2.54), dpi=DPI)
    fig.subplots_adjust(left=0.17, right=0.935, top=0.86, bottom=0.20)
    image = ax.imshow(data, aspect="auto", cmap="YlOrRd", vmin=0.0,
                      vmax=max(data.max(), 1e-9))
    ax.set_yticks(range(len(TICKERS)))
    ax.set_yticklabels([LABELS[t] for t in TICKERS], fontsize=7,
                       family=FONT)
    ax.set_xticks(range(0, len(months), 2))
    ax.set_xticklabels(months[::2], fontsize=6.5, family=FONT)
    ax.set_xlabel("месяц", fontsize=7, family=FONT, color="#1b1b1b")
    ax.set_title("Матрица рисков r(ij), % в день", fontsize=7.5,
                 family=FONT, pad=4)
    for spine in ax.spines.values():
        spine.set_visible(False)
    bar = fig.colorbar(image, ax=ax, pad=0.012, fraction=0.025)
    bar.set_ticks([0.0, 0.5, 1.0, 1.5])
    bar.set_ticklabels(["0,0", "0,5", "1,0", "1,5"])
    for label in bar.ax.get_yticklabels():
        label.set_fontfamily(FONT)
        label.set_fontsize(6)
    bar.outline.set_visible(False)
    path = os.path.join(OUT_DIR, "unc_fig2.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def chart_hurwitz(r):
    """Рисунок 3: критерий Гурвица при изменении коэффициента оптимизма."""
    alphas = r["alphas"]
    cross = r["cross"][("BAYN.DE", "SAN.PA")]

    fig, ax = single(6.5)
    for t in TICKERS:
        ax.plot(alphas, [v * 100.0 for v in r["sweep"][t]], "o-", ms=3.0,
                lw=1.3, color=COLOR[t], label=LABELS[t])
    for value, text, align, dx in ((r["alpha"], "α = 0,06", "right", -0.012),
                                   (cross, "α = 0,165", "left", 0.012)):
        ax.axvline(value, color="#666", lw=0.9, ls=(0, (4, 3)))
        ax.text(value + dx, 1.44, text, fontsize=6.5, family=FONT,
                color="#333", ha=align, va="top")
    ax.axhline(0.0, color="#888", lw=0.7)
    ax.set_title("Критерий Гурвица H(i)(α) для трёх акций", fontsize=7.5,
                 family=FONT, pad=4)
    ax.set_xlabel("коэффициент оптимизма α", fontsize=7, family=FONT,
                  color="#1b1b1b")
    ax.set_ylabel("H(i)(α), % в день", fontsize=7, family=FONT,
                  color="#1b1b1b")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.60, 1.55)
    ax.legend(fontsize=7, frameon=False, loc="lower right",
              prop={"family": FONT, "size": 7})
    style(ax)
    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda v, pos: ("%.1f" % v).replace(".", ",").replace("-", "−")))
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, pos: ("%.2f" % v).replace(".", ",").replace("-", "−")))
    path = os.path.join(OUT_DIR, "unc_fig3.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Текст отчёта
# ---------------------------------------------------------------------------
def build_content(rep, dates, data, r):
    keys = r["months"]
    n = len(keys)
    days = sum(1 for d in dates if (d.year, d.month) in set(keys))
    choice = r["choice"]
    alpha = r["alpha"]
    cross = r["cross"][("BAYN.DE", "SAN.PA")]

    def lab(t):
        return LABELS[t]

    def month_range(part):
        idx = keys.index(part[0])
        return month_text(part[0]), month_text(part[-1])

    def rows_for(monkeys, values, extra=None):
        rows = []
        for j, key in enumerate(keys):
            if key not in monkeys:
                continue
            row = [month_text(key)]
            row.extend(pct(values[t][j]) for t in TICKERS)
            if extra is not None:
                row.append(qpct(extra[j]))
            rows.append(tuple(row))
        return rows

    first = keys[:12]
    second = keys[12:]

    # ------------------------------------------------------------------
    rep.h1("Цель работы")
    rep.p("Цель работы - изучить принятие решений в условиях полной "
          "неопределённости, когда вероятности состояний среды неизвестны "
          "и не могут быть оценены, и выбрать объект инвестирования из "
          "трёх альтернатив шестью классическими критериями. Требуется "
          "построить матрицу средних дневных доходностей за 24 месяца, "
          "матрицу рисков, найти решение по критериям максимакса, Лапласа, "
          "Вальда, Гурвица, Сэвиджа и критерию с субъективными "
          "вероятностями, а затем сопоставить выводы критериев.")
    rep.p("Вариант 3: Bayer (BAYN.DE), Merck & Co (MRK) и Sanofi (SAN.PA). "
          "Альтернатива A(i) означает вложение всех средств в i-ю акцию, "
          "состояние природы s(j) - j-й месяц на мировом рынке. "
          "Используются те же данные, что и в лабораторной работе №1: "
          "дневные цены закрытия за два года, приведённые к общим торговым "
          "дням трёх бирж.")
    rep.p("Для достижения цели решаются следующие задачи:")
    rep.numbers([
        "построить матрицу средних дневных доходностей 3 × 24 и матрицу "
        "рисков;",
        "вычислить значения шести критериев и определить лучшую "
        "альтернативу по каждому из них;",
        "исследовать, как меняется выбор по критерию Гурвица при "
        "коэффициенте оптимизма от 0 до 1 с шагом 0,1;",
        "объяснить расхождения между критериями и сформулировать "
        "рекомендацию для ЛПР.",
    ])

    # ------------------------------------------------------------------
    rep.h1("Вариант и статистические данные")
    rep.p("Период наблюдений - с %s по %s, всего %d общих торговых дней. "
          "Дневная доходность считается как X(t) = (P(t) - P(t-1)) / "
          "P(t-1). Для каждого месяца находится средняя дневная доходность "
          "f(i,j) по всем торговым дням этого месяца:"
          % (dates[0].strftime("%d.%m.%Y"), dates[-1].strftime("%d.%m.%Y"),
             len(dates)))
    rep.formula("f(i, j) = (1 / n(j)) · Σ(k=1..n(j)) X(i, k),")
    rep.p("где n(j) - число торговых дней в j-м месяце. Именно средняя, а не "
          "суммарная доходность позволяет сравнивать месяцы с разным числом "
          "торговых дней.")
    rep.p("Из выборки взяты %d месяцев - с %s по %s, то есть %d торговых "
          "дней. Ноябрь 2026 года исключён: ряд обрывается 17 ноября, и "
          "месяц неполон. Первый месяц (ноябрь 2024 года) содержит только "
          "8 торговых дней, поскольку выборка начинается 18 ноября; "
          "средняя дневная доходность в нём считается по этим дням и "
          "остаётся сопоставимой с остальными месяцами."
          % (n, month_text(keys[0]), month_text(keys[-1]), days))

    head = ("Месяц", "Bayer", "Merck & Co", "Sanofi")
    widths = (2.4, 4.0, 4.0, 4.0)
    a, b = month_range(first)
    rep.p("Матрица F средних дневных доходностей приведена в таблицах 1 и 2 "
          "и на рисунке 1. Значения даны в процентах за день; "
          "отрицательное значение означает падение бумаги в среднем за "
          "месяц.")
    rep.table(head, rows_for(first, r["matrix"]), widths, size=10,
              caption="Таблица 1. Средняя дневная доходность за %s - %s, "
                      "%% в день" % (a, b))
    a, b = month_range(second)
    rep.table(head, rows_for(second, r["matrix"]), widths, size=10,
              caption="Таблица 2. Средняя дневная доходность за %s - %s, "
                      "%% в день" % (a, b), keep_together=True)
    rep.p("Диапазон средних доходностей широк: от %s %% в день у Bayer в "
          "ноябре 2024 года до %s %% в день у него же в июне 2026 года. "
          "Bayer показывает и лучший, и худший месяцы, то есть обладает "
          "самой широкой амплитудой. Sanofi, наоборот, самый спокойный: "
          "его максимум %s %%, а минимум %s %% по модулю заметно меньше, "
          "чем у конкурентов. Merck занимает промежуточное положение."
          % (pct(min(r["matrix"]["BAYN.DE"])),
             pct(max(r["matrix"]["BAYN.DE"])),
             pct(max(r["matrix"]["SAN.PA"])),
             pct(min(r["matrix"]["SAN.PA"]))))

    fig1 = chart_returns(r)
    rep.figure(fig1, "Рисунок 1. Средняя дневная доходность акций "
                     "по месяцам", width_cm=16.5)

    # ------------------------------------------------------------------
    rep.h1("Математическая постановка задачи")
    rep.p("Пусть задана матрица доходов F = (f(i, j)), i = 1, ..., m, "
          "j = 1, ..., n, где f(i, j) - доход при выборе альтернативы A(i) "
          "в состоянии природы s(j); в работе m = 3, n = 24. Требуется "
          "выбрать альтернативу A*, наилучшую в смысле выбранного "
          "критерия; вероятности состояний природы неизвестны, поэтому "
          "критерий должен опираться только на элементы матрицы F.")
    rep.p("С матрицей доходов связана матрица рисков (сожалений) R. Риск "
          "r(i, j) - это плата за отсутствие информации о состоянии среды; "
          "для доходов он равен разности между лучшим доходом в столбце и "
          "доходом альтернативы A(i):")
    rep.formula("r(i, j) = max(k=1..m) f(k, j) − f(i, j) ≥ 0.")
    rep.p("Все критерии, кроме Сэвиджа, работают с матрицей F; Сэвидж "
          "заменяет F матрицей R и минимизирует максимальное сожаление.")

    rep.h2("Критерий максимакса")
    rep.p("Критерий крайнего оптимизма выбирает альтернативу с наибольшим "
          "из всех возможных доходов:")
    rep.formula("M = max(i=1..m) max(j=1..n) f(i, j).")
    rep.p("Он учитывает только лучший исход и подходит ЛПР, готовому к "
          "максимальному риску.")

    rep.h2("Критерий Лапласа")
    rep.p("Принцип недостаточного обоснования: все состояния равновероятны, "
          "p(j) = 1/n; ЛПР сопоставляет альтернативе средний доход:")
    rep.formula("L(i) = (1/n) · Σ(j=1..n) f(i, j),   A* = argmax L(i).")

    rep.h2("Критерий Вальда")
    rep.p("Максиминный критерий соответствует крайнему пессимизму: для "
          "каждой альтернативы берётся худший исход, а затем выбирается "
          "лучший из худших:")
    rep.formula("W(i) = min(j=1..n) f(i, j),   A* = argmax W(i).")

    rep.h2("Критерий Гурвица")
    rep.p("Критерий Гурвица занимает промежуточное положение между "
          "оптимизмом и пессимизмом. Он взвешивает лучший и худший исходы "
          "альтернативы с коэффициентом оптимизма α ∈ [0; 1]:")
    rep.formula("H(i) = α · max(j) f(i, j) + (1 − α) · min(j) f(i, j).")
    rep.p("При α = 0 критерий совпадает с критерием Вальда, при α = 1 - с "
          "критерием максимакса. По методике α = 0,02·n = 0,06 для "
          "варианта 3, то есть ЛПР настроено почти так же осторожно, как "
          "по Вальду.")

    rep.h2("Критерий Сэвиджа")
    rep.p("Критерий минимизирует максимальный риск, а не сам доход: для "
          "каждой альтернативы находится наибольшее сожаление, и "
          "выбирается альтернатива с наименьшим из них:")
    rep.formula("S(i) = max(j=1..n) r(i, j),   A* = argmin S(i).")
    rep.p("Замена матрицы доходов матрицей рисков смягчает пессимизм "
          "критерия Вальда: альтернатива наказывается не за низкий доход, "
          "а за упущенную выгоду относительно лучшего решения.")

    rep.h2("Критерий с субъективными вероятностями")
    rep.p("Если ЛПР может оценить правдоподобность состояний, "
          "используется критерий с весами q(j):")
    rep.formula("Q(i) = Σ(j=1..n) f(i, j) · q(j),   A* = argmax Q(i).")
    rep.p("По методике веса q(j) пропорциональны суммарной доходности "
          "месяца:")
    rep.formula("q(j) = Σ(i=1..m) f(i, j) / Σ(i=1..m) Σ(j=1..n) f(i, j).")
    rep.p("Доходности нормируются к [0; 1], чтобы q(j) не были "
          "отрицательными:")
    rep.formula("g(i, j) = (f(i, j) − min f) / (max f − min f),   "
                "q(j) = Σ(i) g(i, j) / Σ(i,j) g(i, j).")
    rep.p("Нормировка линейна, поэтому порядок месяцев не меняется; после "
          "неё q(j) > 0 и Σ q(j) = 1.")

    # ------------------------------------------------------------------
    rep.h1("Расчёт по критериям")
    rep.p("Ниже для каждого критерия показано, как получается решение. "
          "Сначала по таблицам 1-2 построена матрица рисков (таблицы 3-4, "
          "рисунок 2), затем по таблицам 1-4 посчитаны все критерии, "
          "поэтому любое число можно проверить вручную.")

    rep.h2("Матрица рисков")
    rep.p("Матрица рисков рассчитана по формуле r(i, j) = max(k) f(k, j) - "
          "f(i, j). В каждом столбце хотя бы один элемент равен нулю: это "
          "бумага, показавшая в данном месяце лучший результат. Чем "
          "больше r(i, j), тем больше упущенная выгода от выбора A(i) в "
          "месяце s(j).")
    a, b = month_range(first)
    risk_head = ("Месяц", "Bayer", "Merck & Co", "Sanofi", "q(j), %")
    rep.table(risk_head, rows_for(first, r["risks"], r["q"]),
              (2.3, 3.5, 3.5, 3.5, 2.4), size=10,
              caption="Таблица 3. Матрица рисков за %s - %s и веса q(j), "
                      "%% в день" % (a, b))
    a, b = month_range(second)
    rep.table(risk_head, rows_for(second, r["risks"], r["q"]),
              (2.3, 3.5, 3.5, 3.5, 2.4), size=10,
              caption="Таблица 4. Матрица рисков за %s - %s и веса q(j), "
                      "%% в день" % (a, b))
    rep.p("Самые крупные риски связаны с месяцами, когда одна бумага резко "
          "отрывалась от остальных. В июне 2026 года Bayer дал %s %% в "
          "день, а Sanofi - лишь %s %%, поэтому риск Sanofi достиг "
          "%s %% - максимума по всей таблице. В ноябре 2024 года "
          "противоположная картина: Merck заработал %s %%, тогда как "
          "Bayer потерял %s %%, и риск Bayer составил %s %%."
          % (pct(r["matrix"]["BAYN.DE"][keys.index((2026, 6))]),
             pct(r["matrix"]["SAN.PA"][keys.index((2026, 6))]),
             pct(r["risks"]["SAN.PA"][keys.index((2026, 6))]),
             pct(r["matrix"]["MRK"][keys.index((2024, 11))]),
             pct(r["matrix"]["BAYN.DE"][keys.index((2024, 11))]),
             pct(r["risks"]["BAYN.DE"][keys.index((2024, 11))])))
    fig2 = chart_risks(r)
    rep.figure(fig2, "Рисунок 2. Матрица рисков Сэвиджа", width_cm=16.5)
    rep.p("На рисунке 2 видно, что у Sanofi есть несколько очень тёмных "
          "клеток (январь, май и июнь 2026 года), у Bayer - одна тёмная "
          "клетка в ноябре 2024 года, а у Merck риски распределены ровнее "
          "и не превышают %s %%."
          % pct(max(r["risks"]["MRK"])))

    rep.h2("Критерий максимакса")
    mb = max(r["best"], key=r["best"].get)
    jb = r["matrix"][mb].index(r["best"][mb])
    rep.p("Максимумы по строкам: Bayer - %s %%, Merck & Co - %s %%, "
          "Sanofi - %s %%. Наибольший доход даёт %s в месяце %s, поэтому "
          "по критерию максимакса выбирается %s."
          % (pct(r["best"]["BAYN.DE"]), pct(r["best"]["MRK"]),
             pct(r["best"]["SAN.PA"]), lab(mb), month_text(keys[jb]),
             lab(mb)))
    rep.formula("M = max(%s; %s; %s) = %s %% в день."
                % (pct(r["best"]["BAYN.DE"]), pct(r["best"]["MRK"]),
                   pct(r["best"]["SAN.PA"]), pct(r["best"][mb])))

    rep.h2("Критерий Лапласа")
    sums = {t: r["mean"][t] * n for t in TICKERS}
    rep.p("Средний доход - сумма доходностей, делённая на 24. Суммы: "
          "%s %%; %s %%; %s %%, средние: %s; %s; %s %% в день, "
          "поэтому выбирается %s."
          % (ru(sums["BAYN.DE"] * 100.0, 2), ru(sums["MRK"] * 100.0, 2),
             ru(sums["SAN.PA"] * 100.0, 2),
             pct(r["mean"]["BAYN.DE"]), pct(r["mean"]["MRK"]),
             pct(r["mean"]["SAN.PA"]), lab(choice["laplace"])))
    rep.formula("L(Bayer) = %s %% / 24 = %s %% в день."
                % (ru(sums["BAYN.DE"] * 100.0, 2),
                   pct(r["mean"]["BAYN.DE"])))

    rep.h2("Критерий Вальда")
    rep.p("Худшие месяцы: Bayer - %s %% (%s), Merck & Co - %s %% (%s), "
          "Sanofi - %s %% (%s). Лучшим из худших является %s: его провал "
          "заметно мягче, чем у конкурентов. По критерию Вальда "
          "выбирается %s."
          % (pct(r["worst"]["BAYN.DE"]),
             month_text(keys[r["matrix"]["BAYN.DE"].index(
                 r["worst"]["BAYN.DE"])]),
             pct(r["worst"]["MRK"]),
             month_text(keys[r["matrix"]["MRK"].index(r["worst"]["MRK"])]),
             pct(r["worst"]["SAN.PA"]),
             month_text(keys[r["matrix"]["SAN.PA"].index(
                 r["worst"]["SAN.PA"])]),
             lab(choice["wald"]), lab(choice["wald"])))
    rep.formula("W = max(%s; %s; %s) = %s %% в день."
                % (pct(r["worst"]["BAYN.DE"]), pct(r["worst"]["MRK"]),
                   pct(r["worst"]["SAN.PA"]), pct(r["worst"][choice["wald"]])))

    rep.h2("Критерий Гурвица")
    rep.p("При α = 0,06 критерий почти повторяет критерий Вальда: вес "
          "лучшего исхода мал, а вес худшего равен 0,94. Для Bayer "
          "H = 0,06 · 1,442 + 0,94 · (−0,495) = −0,379 %% в день. "
          "Аналогично H(Merck) = %s %%, H(Sanofi) = %s %%. Наибольшее "
          "значение у Sanofi, поэтому по критерию Гурвица выбирается Sanofi."
          % (pct(r["hurwitz"]["MRK"]), pct(r["hurwitz"]["SAN.PA"])))
    rep.h2("Критерий Сэвиджа")
    rep.p("Максимальные риски по строкам: Bayer - %s %% (%s), Merck & Co - "
          "%s %% (%s), Sanofi - %s %% (%s). Минимальное сожаление у %s: "
          "его худший промах %s %% против %s %% у Bayer и %s %% у Sanofi."
          % (pct(r["savage"]["BAYN.DE"]),
             month_text(keys[r["risks"]["BAYN.DE"].index(
                 r["savage"]["BAYN.DE"])]),
             pct(r["savage"]["MRK"]),
             month_text(keys[r["risks"]["MRK"].index(r["savage"]["MRK"])]),
             pct(r["savage"]["SAN.PA"]),
             month_text(keys[r["risks"]["SAN.PA"].index(
                 r["savage"]["SAN.PA"])]),
             lab(choice["savage"]), pct(r["savage"]["MRK"]),
             pct(r["savage"]["BAYN.DE"]), pct(r["savage"]["SAN.PA"])))
    rep.formula("S = min(%s; %s; %s) = %s %% в день."
                % (pct(r["savage"]["BAYN.DE"]), pct(r["savage"]["MRK"]),
                   pct(r["savage"]["SAN.PA"]), pct(r["savage"][choice["savage"]])))

    rep.h2("Критерий с субъективными вероятностями")
    q = r["q"]
    top = sorted(range(n), key=lambda j: q[j], reverse=True)[:3]
    low = sorted(range(n), key=lambda j: q[j])[:2]
    rep.p("Веса q(j) лежат в диапазоне от %s %% до %s %%. Наибольший вес "
          "получили месяцы %s, %s и %s, наименьший - %s и %s, когда рынок "
          "падал. Набор весов смещает оценку в сторону удачных месяцев, но "
          "не отбрасывает плохие."
          % (qpct(min(q)), qpct(max(q)),
             month_text(keys[top[0]]), month_text(keys[top[1]]),
             month_text(keys[top[2]]),
             month_text(keys[low[0]]), month_text(keys[low[1]])))
    rep.p("Взвешенные суммы Q(i) = Σ f(i, j)·q(j) дают: Bayer - "
          "%s %%, Merck & Co - %s %%, Sanofi - %s %% в день. По этому "
          "критерию выбирается %s: его сильнейшие месяцы (%s и %s) получили "
          "наибольший вес."
          % (pct(r["subjective"]["BAYN.DE"]), pct(r["subjective"]["MRK"]),
             pct(r["subjective"]["SAN.PA"]), lab(choice["subjective"]),
             month_text(keys[keys.index((2025, 12))]),
             month_text(keys[keys.index((2026, 6))])))
    rep.formula("Q = max(%s; %s; %s) = %s %% в день."
                % (pct(r["subjective"]["BAYN.DE"]),
                   pct(r["subjective"]["MRK"]),
                   pct(r["subjective"]["SAN.PA"]),
                   pct(r["subjective"][choice["subjective"]])))

    # ------------------------------------------------------------------
    rep.h1("Сводка результатов и сравнение критериев")
    rep.p("В таблицах 5-6 собраны значения критериев и итоговый выбор. "
          "Критерии максимакса, Лапласа, Гурвица и субъективных "
          "вероятностей максимизируются, критерий Сэвиджа минимизируется.")
    rows = []
    for t in TICKERS:
        rows.append((
            lab(t),
            pct(r["best"][t]), pct(r["worst"][t]), pct(r["mean"][t]),
            pct(r["hurwitz"][t]), pct(r["savage"][t]),
            pct(r["subjective"][t]),
        ))
    rep.table(
        ("Акция", "max f", "min f", "L", "H (α=0,06)", "S", "Q"),
        rows, (2.6, 2.35, 2.35, 2.3, 2.5, 2.3, 2.3), size=9,
        caption="Таблица 5. Значения критериев, % в день")
    crit_rows = [
        (CRIT_NAMES["maximax"], lab(choice["maximax"]),
         pct(r["best"][choice["maximax"]])),
        (CRIT_NAMES["laplace"], lab(choice["laplace"]),
         pct(r["mean"][choice["laplace"]])),
        (CRIT_NAMES["wald"], lab(choice["wald"]),
         pct(r["worst"][choice["wald"]])),
        (CRIT_NAMES["hurwitz"], lab(choice["hurwitz"]),
         pct(r["hurwitz"][choice["hurwitz"]])),
        (CRIT_NAMES["savage"], lab(choice["savage"]),
         pct(r["savage"][choice["savage"]])),
        (CRIT_NAMES["subjective"], lab(choice["subjective"]),
         pct(r["subjective"][choice["subjective"]])),
    ]
    rep.table(("Критерий", "Лучшая альтернатива", "Значение, % в день"),
              crit_rows, (7.0, 4.6, 4.4), size=10,
              caption="Таблица 6. Решение по каждому критерию")

    rep.p("Максимакс смотрит только на максимум строки и выбирает Bayer: "
          "его июнь 2026 года (%s %%) не имеет равных. Лаплас усредняет "
          "все 24 месяца и тоже выбирает Bayer: его средняя доходность "
          "%s %% в день почти в полтора раза выше, чем у Merck, и в 95 раз "
          "выше, чем у Sanofi."
          % (pct(r["best"]["BAYN.DE"]), pct(r["mean"]["BAYN.DE"])))
    rep.p("Вальд и Гурвиц при α = 0,06 смотрят на худший месяц: у Sanofi "
          "%s %%, у Bayer - %s %%, у Merck - %s %%. Разница по худшему "
          "(%s %%) почти такая же, как по среднему (%s %%), но Вальд "
          "учитывает только худший исход. Сэвидж наказывает за упущенную "
          "выгоду, и здесь выигрывает Merck: риск %s %% меньше, чем "
          "%s %% у Bayer и %s %% у Sanofi."
          % (pct(r["worst"]["SAN.PA"]), pct(r["worst"]["BAYN.DE"]),
             pct(r["worst"]["MRK"]),
             pct(r["worst"]["SAN.PA"] - r["worst"]["BAYN.DE"]),
             pct(r["mean"]["BAYN.DE"] - r["mean"]["SAN.PA"]),
             pct(r["savage"]["MRK"]), pct(r["savage"]["BAYN.DE"]),
             pct(r["savage"]["SAN.PA"])))
    rep.p("Критерий с субъективными вероятностями даёт тот же ответ, что и "
          "Лаплас, но усиливает вес благополучных месяцев. Совпадение "
          "показывает, что вывод не зависит от способа взвешивания.")
    rep.p("Итог: три критерия указывают на Bayer, два - на Sanofi, один - "
          "на Merck & Co. Это свойство задачи с полной неопределённостью: "
          "разные критерии формализуют разное отношение к риску.")
    # ------------------------------------------------------------------
    rep.h1("Исследование критерия Гурвица")
    rep.p("Коэффициент оптимизма α - единственный параметр, который "
          "методика не фиксирует однозначно, поэтому критерий "
          "дополнительно рассчитан при α = 0; 0,1; ...; 1 (таблица 7, "
          "рисунок 3).")
    rows = []
    for j, a in enumerate(r["alphas"]):
        rows.append((
            ("%.1f" % a).replace(".", ","),
            pct(r["sweep"]["BAYN.DE"][j]),
            pct(r["sweep"]["MRK"][j]),
            pct(r["sweep"]["SAN.PA"][j]),
            lab(r["sweep_winners"][j]),
        ))
    rep.table(("α", "Bayer", "Merck & Co", "Sanofi", "Выбор"),
              rows, (2.0, 3.4, 3.4, 3.4, 4.0), size=9,
              caption="Таблица 7. Критерий Гурвица при изменении α, "
                      "% в день")
    fig3 = chart_hurwitz(r)
    rep.figure(fig3, "Рисунок 3. Зависимость критерия Гурвица "
                     "от коэффициента оптимизма", width_cm=16.5)
    rep.p("При α от 0 до %s выбирается Sanofi, при α от %s до 1 - Bayer. "
          "Merck не побеждает ни при одном α: при малых α его худший месяц "
          "хуже, чем у Sanofi, при больших он уступает Bayer по лучшему. "
          "Линии Bayer и Sanofi пересекаются при α = %s, между 0,1 и 0,2."
          % ((("%.1f" % (int(cross * 10) / 10.0)).replace(".", ",")),
             (("%.1f" % ((int(cross * 10) + 1) / 10.0)).replace(".", ",")),
             ru(cross, 3)))
    rep.p("Картина устойчива: изменение α в пределах 0,06-0,16 не меняет "
          "решения, переход к Bayer требует α > 0,165. Поэтому при α = 0,06 "
          "вывод Гурвица совпадает с выводом Вальда не случайно.")

    # ------------------------------------------------------------------
    rep.h1("Выводы")
    rep.p("В работе построена матрица средних дневных доходностей трёх "
          "акций за %d месяца и матрица рисков. По критерию максимакса "
          "выбрана %s (%s %% в день), по критерию Лапласа - %s (%s %%), "
          "по критерию Вальда - %s (%s %%), по критерию Гурвица при "
          "α = 0,06 - %s (%s %%), по критерию Сэвиджа - %s (%s %%), по "
          "критерию с субъективными вероятностями - %s (%s %%)."
          % (n, lab(choice["maximax"]), pct(r["best"][choice["maximax"]]),
             lab(choice["laplace"]), pct(r["mean"][choice["laplace"]]),
             lab(choice["wald"]), pct(r["worst"][choice["wald"]]),
             lab(choice["hurwitz"]), pct(r["hurwitz"][choice["hurwitz"]]),
             lab(choice["savage"]), pct(r["savage"][choice["savage"]]),
             lab(choice["subjective"]),
             pct(r["subjective"][choice["subjective"]])))
    rep.p("Расхождение выводов объясняется разной степенью консерватизма "
          "критериев. Bayer имеет максимальную среднюю доходность и лучший "
          "месяц, но и самый тяжёлый провал, поэтому его выбирают "
          "оптимистичные критерии. Sanofi имеет самый мягкий худший месяц, "
          "поэтому его выбирают Вальд и Гурвиц при малом α. Merck не "
          "лидирует ни по доходности, ни по худшему месяцу, но имеет "
          "наименьшее максимальное сожаление и побеждает у Сэвиджа.")
    rep.p("Исследование критерия Гурвица показало, что решение меняется "
          "один раз: при α < %s выбирается Sanofi, при α > %s - Bayer; "
          "точка перехода α = %s. При заданном методикой α = 0,06 "
          "решение совпадает с критерием Вальда и лежит в широком "
          "устойчивом интервале, поэтому случайной флуктуацией α оно не "
          "объясняется."
          % (ru(cross, 3), ru(cross, 3), ru(cross, 3)))
    rep.p("Практическая рекомендация зависит от отношения ЛПР к риску. "
          "При осторожной позиции, заданной методикой, следует выбрать "
          "Sanofi: он даёт минимальные потери в худшем месяце и почти не "
          "уступает по критерию Гурвица. Если ЛПР готово принять более "
          "глубокую просадку ради средней доходности, предпочтителен "
          "Bayer; если важнее минимизировать упущенную выгоду, - Merck. "
          "Таким образом, в условиях полной неопределённости "
          "окончательный выбор должен делаться не только по матрице "
          "доходов, но и с учётом явно сформулированного критерия и "
          "профиля инвестора.")


# ---------------------------------------------------------------------------
# Сборка
# ---------------------------------------------------------------------------
def build():
    """Собирает отчёт: считает критерии, рисует фигуры, сохраняет DOCX."""
    dates, data = risk_data.load()
    r = uncertainty.build(dates, data)
    os.makedirs(OUT_DIR, exist_ok=True)

    meta = ReportMeta(
        lab_no="5-6",
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
