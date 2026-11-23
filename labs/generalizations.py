# -*- coding: utf-8 -*-
"""Обобщения теории ожидаемой полезности для лабораторной работы №4.

Модуль считает два критерия, которые обобщают ожидаемую полезность на
случай, когда ЛПР не сводит предпочтения к линейному по вероятностям
функционалу:

* критерий взвешенной полезности

      Vw(X) = E[w(X)·v(X)] / E[v(X)],

  где w(x) - непрерывная возрастающая вогнутая функция полезности, а
  v(x) - непрерывная убывающая выпуклая положительная весовая функция.
  Убывающая v придаёт больший вес неблагоприятным исходам, поэтому Vw
  описывает «пессимистичное» отношение к риску: это ожидаемая полезность,
  посчитанная по искажённому (взвешенному) распределению.

* критерий ранговой полезности (rank-dependent utility, Куиггин)

      Vr(X) = Σ_i u(x_i)·(g(F_i) − g(F_(i-1))),

  где x_1 < ... < x_k - значения дискретной величины, F_i - накопленная
  вероятность, g: [0; 1] → [0; 1] - непрерывная возрастающая вогнутая
  функция искажения вероятностей с g(0) = 0, g(1) = 1.

Никаких matplotlib и docx: модуль загружают и отчёт, и отдельный расчёт.
Данные приходят в долях, но обе функции полезности определены на
процентной шкале, поэтому внутри все доходности умножаются на 100.
"""
import math

from labs import utility

# --- параметры выбранных функций (подобраны в отчёте) -----------------------
ALPHA = 0.30       # кривизна w(x) = 1 − exp(−α·x)
BETA = 0.25        # сила веса v(x) = exp(−β·x)
GAMMA = 0.60       # кривизна g(t) = t^γ

# --- квадратура Гаусса-Лежандра на [0; 1], 8 узлов --------------------------
GAUSS_X = utility.GAUSS_X
GAUSS_W = utility.GAUSS_W


# ---------------------------------------------------------------------------
# Выбранные функции
# ---------------------------------------------------------------------------
def utility_w(x, alpha=ALPHA):
    """w(x) = 1 − exp(−α·x): возрастает, вогнута, w(0) = 0."""
    return 1.0 - math.exp(-alpha * x)


def weight_v(x, beta=BETA):
    """v(x) = exp(−β·x): положительна, убывает, выпукла вниз."""
    return math.exp(-beta * x)


def distortion_g(t, gamma=GAMMA):
    """g(t) = t^γ: отображает [0; 1] в себя, возрастает, вогнута."""
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return t ** gamma


def distortion_deriv(t, gamma=GAMMA):
    """g′(t) = γ·t^(γ−1)."""
    if t <= 0.0:
        return float("inf")
    return gamma * t ** (gamma - 1.0)


# ---------------------------------------------------------------------------
# Ожидание по интервальному ряду
# ---------------------------------------------------------------------------
def expected(func, series, scale=100.0):
    """E[f(X)] при равномерном распределении внутри интервалов ряда.

    Вклад интервала равен p_j · (1 / h_j) · ∫ f(x) dx; интеграл берётся
    квадратурой Гаусса-Лежандра с восемью узлами. Функции w, v, w·v
    гладкие, поэтому квадратура даёт машинную точность.
    """
    total = 0.0
    for j, p in enumerate(series["freq"]):
        a = series["edges"][j] * scale
        b = series["edges"][j + 1] * scale
        center, half = 0.5 * (a + b), 0.5 * (b - a)
        acc = 0.0
        for node, weight in zip(GAUSS_X, GAUSS_W):
            acc += weight * func(center + half * node)
        total += p * (0.5 * acc)          # (1 / h)·∫ = 0,5·Σ узлов
    return total


# ---------------------------------------------------------------------------
# Критерий взвешенной полезности
# ---------------------------------------------------------------------------
def weighted_utility(series, alpha=ALPHA, beta=BETA, scale=100.0):
    """Vw = E[w·v] / E[v] по интервальному ряду."""
    num = expected(lambda x: utility_w(x, alpha) * weight_v(x, beta),
                   series, scale)
    den = expected(lambda x: weight_v(x, beta), series, scale)
    return num / den


def weighted_mean(series, beta=BETA, scale=100.0):
    """Среднее доходности по распределению, взвешенному v(x).

    Плотность вероятности, пропорциональная v(x)·f(x), нормируется на
    E[v(X)], и математическое ожидание по ней равно E[X·v(X)] / E[v(X)].
    Сравнение с обычным средним показывает, насколько «пессимистично»
    сдвигается распределение при убывающем весе.
    """
    num = expected(lambda x: x * weight_v(x, beta), series, scale)
    den = expected(lambda x: weight_v(x, beta), series, scale)
    return num / den


# ---------------------------------------------------------------------------
# Критерий ранговой полезности
# ---------------------------------------------------------------------------
def rank_utility_continuous(series, u, gamma=GAMMA, scale=100.0):
    """Vr = ∫ u(x) dg(F(x)) для интервального ряда.

    Внутри интервала j накопленная вероятность растёт линейно от F_(j−1)
    до F_j, а доходность - линейно от a_j до b_j. Переход к t = F_(j−1) +
    p_j·s даёт вклад p_j·∫₀¹ u(x(s))·g′(t(s)) ds, который берётся
    квадратурой Гаусса-Лежандра.
    """
    total = 0.0
    cum = 0.0
    for j, p in enumerate(series["freq"]):
        a = series["edges"][j] * scale
        b = series["edges"][j + 1] * scale
        lo_t = cum
        acc = 0.0
        for node, weight in zip(GAUSS_X, GAUSS_W):
            s = 0.5 * (node + 1.0)
            x = a + (b - a) * s
            t = lo_t + p * s
            acc += weight * u(x) * distortion_deriv(t, gamma)
        total += p * 0.5 * acc
        cum += p
    return total


def rank_utility_midpoint(series, u, gamma=GAMMA, scale=100.0):
    """Vr по дискретной формуле: атомы в серединах интервалов.

    Это буквальная запись формулы методики для дискретной величины
    x_1 < ... < x_k с вероятностями p_i: Vr = Σ u(x_i)·(g(F_i) −
    g(F_(i−1))). Служит проверкой непрерывного варианта.
    """
    total = 0.0
    cum = 0.0
    for j, p in enumerate(series["freq"]):
        mid = 0.5 * (series["edges"][j] + series["edges"][j + 1]) * scale
        total += u(mid) * (distortion_g(cum + p, gamma) - distortion_g(cum, gamma))
        cum += p
    return total


def rank_utility_sample(values, u, gamma=GAMMA):
    """Vr по исходной выборке: все n наблюдений - атомы с весом 1/n."""
    ordered = sorted(values)
    n = len(ordered)
    total = 0.0
    for i, x in enumerate(ordered):
        total += u(x * 100.0) * (distortion_g((i + 1.0) / n, gamma)
                                 - distortion_g(i / n, gamma))
    return total


# ---------------------------------------------------------------------------
# Полный расчёт
# ---------------------------------------------------------------------------
def build(tickers, data, r3=None):
    """Считает оба критерия и проверки устойчивости.

    ``r3`` - результат ``utility.build`` для лабораторной работы №3; если
    он не передан, считается заново. Возвращает словарь с полями ``r3``,
    ``vw``/``vr`` - {тикер: значение}, ``vr_mid``/``vr_raw`` - проверки,
    ``sens_vw``/``sens_vr`` - таблицы чувствительности к параметрам.
    """
    if r3 is None:
        r3 = utility.build(tickers, data)
    series = r3["series"]
    u = r3["u_emp"]

    vw, vr, vr_mid, vr_raw = {}, {}, {}, {}
    wmean, vw_parts = {}, {}
    for t in tickers:
        vw[t] = weighted_utility(series[t])
        wmean[t] = weighted_mean(series[t])
        num = expected(lambda x: utility_w(x) * weight_v(x), series[t])
        den = expected(lambda x: weight_v(x), series[t])
        vw_parts[t] = (num, den)
        vr[t] = rank_utility_continuous(series[t], u)
        vr_mid[t] = rank_utility_midpoint(series[t], u)
        vr_raw[t] = rank_utility_sample(data[t], u)

    # чувствительность Vw к силе пессимизма beta и кривизне alpha
    betas = (0.10, 0.25, 0.40)
    alphas = (0.15, 0.30, 0.45)
    sens_vw = {}
    for beta in betas:
        sens_vw[("b", beta)] = {t: weighted_utility(series[t], ALPHA, beta)
                                for t in tickers}
    for alpha in alphas:
        sens_vw[("a", alpha)] = {t: weighted_utility(series[t], alpha, BETA)
                                 for t in tickers}

    # чувствительность Vr к кривизне функции искажения gamma
    gammas = (0.40, 0.60, 0.80)
    sens_vr = {g: {t: rank_utility_continuous(series[t], u, g)
                   for t in tickers} for g in gammas}

    return {
        "r3": r3,
        "u_emp": u,
        "lo": r3["lo"],
        "hi": r3["hi"],
        "alpha": ALPHA,
        "beta": BETA,
        "gamma": GAMMA,
        "vw": vw,
        "wmean": wmean,
        "vw_parts": vw_parts,
        "vr": vr,
        "vr_mid": vr_mid,
        "vr_raw": vr_raw,
        "sens_vw": sens_vw,
        "sens_vr": sens_vr,
        "betas": betas,
        "alphas": alphas,
        "gammas": gammas,
    }
