# -*- coding: utf-8 -*-
"""Расчётная часть лабораторной работы №5-6.

Дисциплина «Принятие решений в условиях неопределённости», тема «Принятие
решений в условиях полной неопределённости».

Вход - дневные доходности трёх акций за два года (те же данные, что в
лабораторной работе №1). Они сводятся к матрице F = (f_ij), где f_ij -
средняя дневная доходность i-й акции в j-м месяце. Строки матрицы - чистые
стратегии A_i (вложить всё в одну бумагу), столбцы - состояния природы s_j
(месяц на мировом рынке).

По матрице F считаются матрица рисков Сэвиджа и шесть критериев: максимакса,
Лапласа, Вальда, Гурвица, Сэвиджа и критерий с субъективными вероятностями,
пропорциональными суммарной доходности месяца. Модуль не импортирует
matplotlib и python-docx: числа можно пересчитать отдельно от отчёта.
"""
import datetime as dt


TICKERS = ("BAYN.DE", "MRK", "SAN.PA")
NAMES = {"BAYN.DE": "Bayer", "MRK": "Merck & Co", "SAN.PA": "Sanofi"}

# Коэффициент оптимизма по методике: alpha = 0.02 * n, n - номер варианта.
VARIANT = 3
ALPHA = 0.02 * VARIANT
MONTHS = 24


def month_key(date):
    return (date.year, date.month)


def month_label(key):
    """Подпись месяца в формате 11.24."""
    return "%02d.%02d" % (key[1], key[0] % 100)


def monthly_matrix(dates, data, months=MONTHS):
    """Матрица средних дневных доходностей по месяцам.

    Берутся последние ``months`` календарных месяцев выборки. Если ряд
    обрывается посреди месяца, этот неполный месяц отбрасывается: средняя
    дневная доходность в нём считалась бы по другому числу наблюдений.
    Возвращаются список ключей месяцев и {тикер: [f_ij, ...]}.
    """
    groups = {}
    for date, *values in zip(dates, *(data[t] for t in TICKERS)):
        groups.setdefault(month_key(date), []).append(tuple(values))

    keys = sorted(groups)
    if len(keys) > months:
        # Последний месяц неполон, если данные кончаются не в конце месяца.
        last_year, last_month = keys[-1]
        if dates[-1].day < 25:
            keys = keys[:-1]
        keys = keys[-months:]

    matrix = {t: [] for t in TICKERS}
    for key in keys:
        rows = groups[key]
        for pos, ticker in enumerate(TICKERS):
            mean = sum(row[pos] for row in rows) / len(rows)
            matrix[ticker].append(mean)
    return keys, matrix


def risk_matrix(matrix):
    """Матрица рисков r_ij = max_k f_kj - f_ij (для доходов)."""
    n = len(matrix[TICKERS[0]])
    best = [max(matrix[t][j] for t in TICKERS) for j in range(n)]
    return {t: [best[j] - matrix[t][j] for j in range(n)] for t in TICKERS}


def normalized(matrix):
    """Нормировка всех доходностей к отрезку [0; 1] (для субъективных q)."""
    values = [x for t in TICKERS for x in matrix[t]]
    lo, hi = min(values), max(values)
    span = hi - lo or 1.0
    return {t: [(x - lo) / span for x in matrix[t]] for t in TICKERS}


def subjective_probabilities(matrix):
    """q_j по методике: доля месяца в суммарной нормированной доходности.

    q_j = sum_i g_ij / sum_ij g_ij, где g - доходности, нормированные к
    [0; 1]. Нормировка гарантирует q_j > 0 и sum_j q_j = 1 даже тогда, когда
    исходные средние доходности отрицательны.
    """
    g = normalized(matrix)
    n = len(matrix[TICKERS[0]])
    column = [sum(g[t][j] for t in TICKERS) for j in range(n)]
    total = sum(column)
    return [x / total for x in column]


def criteria(matrix, alpha=ALPHA):
    """Значения шести критериев и выбор по каждому из них."""
    n = len(matrix[TICKERS[0]])
    r = risk_matrix(matrix)
    q = subjective_probabilities(matrix)

    best = {}
    worst = {}
    mean = {}
    hurwitz = {}
    savage = {}
    subjective = {}
    for t in TICKERS:
        row = matrix[t]
        best[t] = max(row)
        worst[t] = min(row)
        mean[t] = sum(row) / n
        hurwitz[t] = alpha * best[t] + (1.0 - alpha) * worst[t]
        savage[t] = max(r[t])
        subjective[t] = sum(qj * x for qj, x in zip(q, row))

    maximax = max(best, key=best.get)
    laplace = max(mean, key=mean.get)
    wald = max(worst, key=worst.get)
    gurvic = max(hurwitz, key=hurwitz.get)
    savidzh = min(savage, key=savage.get)
    subjective_best = max(subjective, key=subjective.get)

    return {
        "matrix": matrix,
        "risks": r,
        "q": q,
        "best": best,
        "worst": worst,
        "mean": mean,
        "hurwitz": hurwitz,
        "savage": savage,
        "subjective": subjective,
        "alpha": alpha,
        "choice": {
            "maximax": maximax,
            "laplace": laplace,
            "wald": wald,
            "hurwitz": gurvic,
            "savage": savidzh,
            "subjective": subjective_best,
        },
    }


def hurwitz_sweep(matrix, step=0.1):
    """Значения критерия Гурвица при alpha = 0, 0.1, ..., 1."""
    alphas = [round(step * i, 10) for i in range(int(round(1.0 / step)) + 1)]
    rows = {}
    for t in TICKERS:
        lo, hi = min(matrix[t]), max(matrix[t])
        rows[t] = [alpha * hi + (1.0 - alpha) * lo for alpha in alphas]
    winners = []
    for j, _ in enumerate(alphas):
        winners.append(max(TICKERS, key=lambda t: rows[t][j]))
    return alphas, rows, winners


def pairwise_cross(matrix, first, second):
    """Alpha, при котором линии Гурвица двух бумаг пересекаются."""
    d_lo = min(matrix[first]) - min(matrix[second])
    d_hi = max(matrix[first]) - max(matrix[second])
    if abs(d_hi - d_lo) < 1e-15:
        return None
    alpha = -d_lo / (d_hi - d_lo)
    return alpha if 0.0 <= alpha <= 1.0 else None


def switch_points(alphas, rows):
    """Интервалы alpha, на которых выбор критерия Гурвица не меняется."""
    n = len(alphas)
    result = []
    start = 0
    for j in range(1, n):
        if max(TICKERS, key=lambda t: rows[t][start]) != max(
                TICKERS, key=lambda t: rows[t][j]):
            result.append((alphas[start], alphas[j - 1]))
            start = j
    result.append((alphas[start], alphas[-1]))
    return result


def build(dates, data, alpha=ALPHA):
    """Полный расчёт: матрица, риски, критерии, развёртка по alpha."""
    keys, matrix = monthly_matrix(dates, data)
    r = criteria(matrix, alpha)
    alphas, sweep, winners = hurwitz_sweep(matrix)
    r.update({
        "months": keys,
        "cross": {pair: pairwise_cross(matrix, *pair)
                  for pair in (("BAYN.DE", "SAN.PA"),
                               ("BAYN.DE", "MRK"),
                               ("MRK", "SAN.PA"))},
        "alphas": alphas,
        "sweep": sweep,
        "sweep_winners": winners,
        "switch_points": switch_points(alphas, sweep),
    })
    return r


if __name__ == "__main__":
    from labs import risk_data

    dates, data = risk_data.load()
    res = build(dates, data)
    print("месяцы:", month_label(res["months"][0]), "-",
          month_label(res["months"][-1]), "n =", len(res["months"]))
    for t in TICKERS:
        print("%-8s max=%+.4f min=%+.4f mean=%+.4f H=%+.4f S=%.4f Q=%+.4f"
              % (t, res["best"][t] * 100, res["worst"][t] * 100,
                 res["mean"][t] * 100, res["hurwitz"][t] * 100,
                 res["savage"][t] * 100, res["subjective"][t] * 100))
    print("choice:", res["choice"])
    print("switch:", res["switch_points"])
