# -*- coding: utf-8 -*-
"""Меры риска для лабораторной работы №1.

Сначала по выборке строится интервальный вариационный ряд (эмпирический
закон распределения), а затем все меры риска считаются по этому же ряду:
среднее, дисперсия, стандартное отклонение, левосторонние
полудисперсия и полуотклонение, VaR и CVaR. Любое число в отчёте можно
пересчитать вручную по таблице вариационного ряда.

Соглашение о знаке: ``X`` - доходность, ``Y = -X`` - убыточность. Риск живёт
в правом хвосте ``Y``, что соответствует левому хвосту ``X``.

Модуль не импортирует matplotlib и python-docx: его загружают и отчёт, и
отдельный расчёт.
"""
import math


# ---------------------------------------------------------------------------
# Интервальный вариационный ряд
# ---------------------------------------------------------------------------
def sturges_k(n):
    """Число интервалов по формуле Стерджиса."""
    return max(1, int(round(1.0 + 3.322 * math.log10(n))))


def variation_series(values, k=None):
    """Интервальный вариационный ряд с частотами и накопленной частотой."""
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
    freq = [c / n for c in counts]
    cum, acc = [], 0.0
    for p in freq:
        acc += p
        cum.append(acc)
    return {
        "n": n,
        "k": k,
        "h": h,
        "edges": edges,
        "mids": mids,
        "counts": counts,
        "freq": freq,
        "cum": cum,
    }


def grouped_moments(series):
    """Среднее и дисперсия дискретной величины, заданной рядом."""
    mids, freq = series["mids"], series["freq"]
    mean_value = sum(x * p for x, p in zip(mids, freq))
    var_value = sum((x - mean_value) ** 2 * p for x, p in zip(mids, freq))
    return mean_value, var_value


def grouped_left_contribution(series):
    """Левосторонняя полудисперсия LVar.

    Сумма квадратов отклонений берётся только по интервалам с серединой
    x_j <= mu:

        LVar(X) = sum_{x_j <= mu} (x_j - mu)^2 * p_j.

    Вероятности уже входят в слагаемые, поэтому LVar - это часть общей
    дисперсии D(X), а не условная дисперсия. Возвращаются LVar и суммарная
    вероятность левой части P(X <= mu).
    """
    mu, _ = grouped_moments(series)
    contrib, mass = 0.0, 0.0
    for x, p in zip(series["mids"], series["freq"]):
        if x <= mu:
            contrib += (x - mu) ** 2 * p
            mass += p
    return contrib, mass


def grouped_loss_series(series):
    """Преобразование ряда доходности X в ряд убыточности Y = -X.

    Интервалы переставляются по возрастанию убытка, вероятности сохраняются.
    Возвращаются середины y_j, вероятности p_j и накопленная вероятность.
    """
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
    """VaR: минимальный y, для которого P(Y <= y) >= alpha."""
    for y, acc in zip(loss_series["mids"], loss_series["cum"]):
        if acc >= alpha - 1e-15:
            return y
    return loss_series["mids"][-1]


def grouped_cvar(loss_series, alpha):
    """CVaR: E[Y | Y > VaR] по вероятностям хвостовых интервалов."""
    threshold = grouped_var(loss_series, alpha)
    num, den = 0.0, 0.0
    for y, p in zip(loss_series["mids"], loss_series["freq"]):
        if y > threshold + 1e-15:
            num += y * p
            den += p
    if den == 0.0:
        return threshold, 0.0
    return num / den, den


# ---------------------------------------------------------------------------
# Полный расчёт по всем бумагам
# ---------------------------------------------------------------------------
def compute(data, alphas=(0.95, 0.97, 0.99)):
    """Считает все меры риска по интервальному ряду каждой бумаги."""
    result = {}
    for ticker, values in data.items():
        series = variation_series(values)
        mean_value, var_value = grouped_moments(series)
        left_contrib, left_mass = grouped_left_contribution(series)
        losses = grouped_loss_series(series)
        result[ticker] = {
            "returns": values,
            "series": series,
            "loss_series": losses,
            "profile": {
                "n": series["n"],
                "min": min(values),
                "max": max(values),
                "mean": mean_value,
                "var": var_value,
                "std": math.sqrt(var_value),
                "left_contrib": left_contrib,
                "left_share": (left_contrib / var_value
                               if var_value else 0.0),
                "lvar": left_contrib,
                "lstd": math.sqrt(left_contrib),
                "left_mass": left_mass,
                "var_": {a: grouped_var(losses, a) for a in alphas},
                "cvar": {a: grouped_cvar(losses, a)[0] for a in alphas},
                "tail_mass": {a: grouped_cvar(losses, a)[1] for a in alphas},
            },
        }
    return result
