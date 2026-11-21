# -*- coding: utf-8 -*-
"""Стохастическое доминирование для лабораторной работы №2.

Сравниваются эмпирические законы распределения дневных доходностей трёх
акций, построенные в лабораторной работе №1 как интервальные вариационные
ряды. Внутри интервала распределение считается равномерным, поэтому
функция распределения F линейна на каждом интервале, а её интеграл S -
квадратичен.

Для пары (A, B):

    F_A(x) = P(A <= x);
    S_A(x) = интеграл F_A от -oo до x = E[(x - A)_+].

A стохастически доминирует B в первом порядке, если F_A(x) <= F_B(x) при
всех x; во втором порядке - если S_A(x) <= S_B(x) при всех x. Разности
D1 = F_A - F_B и D2 = S_A - S_B отрицательны там, где A предпочтительнее;
смена знака означает отсутствие доминирования.

Модуль не импортирует matplotlib и python-docx.
"""
import bisect


# ---------------------------------------------------------------------------
# Эмпирический закон из интервального ряда
# ---------------------------------------------------------------------------
class Distribution:
    """Кусочно-линейная функция распределения по интервальному ряду."""

    def __init__(self, series):
        self.edges = list(series["edges"])
        self.freq = list(series["freq"])
        self.cum = [0.0]
        for p in self.freq:
            self.cum.append(self.cum[-1] + p)
        self.lo = self.edges[0]
        self.hi = self.edges[-1]
        self._full = 0.0
        for i in range(len(self.freq)):
            step = self.edges[i + 1] - self.edges[i]
            self._full += self.cum[i] * step + self.freq[i] * step / 2.0

    def _bin(self, x):
        """Номер интервала, в который попадает x."""
        return bisect.bisect_right(self.edges, x) - 1

    def F(self, x):
        """Функция распределения F(x)."""
        if x <= self.lo:
            return 0.0
        if x >= self.hi:
            return 1.0
        j = self._bin(x)
        width = self.edges[j + 1] - self.edges[j]
        return self.cum[j] + self.freq[j] * (x - self.edges[j]) / width

    def S(self, x):
        """Интеграл F от -oo до x (ожидаемый недобор (x - X)_+)."""
        if x <= self.lo:
            return 0.0
        if x >= self.hi:
            return self._full + (x - self.hi)
        j = self._bin(x)
        width = self.edges[j + 1] - self.edges[j]
        tail = x - self.edges[j]
        total = 0.0
        for i in range(j):
            step = self.edges[i + 1] - self.edges[i]
            total += self.cum[i] * step + self.freq[i] * step / 2.0
        return total + self.cum[j] * tail + self.freq[j] * tail ** 2 / (2.0 * width)


# ---------------------------------------------------------------------------
# Анализ разности функций
# ---------------------------------------------------------------------------
def analyse(diffs, grid, tol=1e-9):
    """Сводка по разности: экстремумы и точки перемены знака.

    ``crossings`` - список (x, глубина) для каждого перехода через ноль;
    глубина считается как наибольшее отклонение разности на участке до
    этого перехода.
    """
    lo = min(range(len(diffs)), key=lambda i: diffs[i])
    hi = max(range(len(diffs)), key=lambda i: diffs[i])
    signs = []
    for value in diffs:
        signs.append(1 if value > tol else (-1 if value < -tol else 0))

    crossings = []
    previous = None
    last_cross = 0
    for i, sign in enumerate(signs):
        if not sign:
            continue
        if previous is not None and sign != previous[1]:
            depth = max(abs(v) for v in diffs[last_cross:i]) if i > last_cross else 0.0
            span = diffs[i] - diffs[i - 1]
            ratio = -diffs[i - 1] / span if span else 0.0
            point = grid[i - 1] + ratio * (grid[i] - grid[i - 1])
            crossings.append((point, depth))
            last_cross = i
        previous = (i, sign)

    if max(diffs) <= tol:
        verdict = "a"
    elif min(diffs) >= -tol:
        verdict = "b"
    else:
        verdict = "none"
    return {
        "min": diffs[lo],
        "max": diffs[hi],
        "argmin": grid[lo],
        "argmax": grid[hi],
        "crossings": crossings,
        "verdict": verdict,
    }


def significant(crossings, threshold):
    """Переходы через ноль, глубина которых больше порога."""
    return [point for point, depth in crossings if depth >= threshold]


# ---------------------------------------------------------------------------
# Сравнение пары распределений
# ---------------------------------------------------------------------------
def compare(dist_a, dist_b, points=1600):
    """Разности D1 и D2 на общей сетке.

    Сетка включает все границы интервалов обоих рядов и равномерное
    заполнение между ними: на таких отрезках D1 линейна, D2 квадратична,
    поэтому знак функции проверяется с достаточной точностью.
    """
    lo = min(dist_a.lo, dist_b.lo)
    hi = max(dist_a.hi, dist_b.hi)
    grid = sorted(set(dist_a.edges) | set(dist_b.edges)
                  | {lo + (hi - lo) * i / float(points)
                     for i in range(points + 1)})
    d1 = [dist_a.F(x) - dist_b.F(x) for x in grid]
    d2 = [dist_a.S(x) - dist_b.S(x) for x in grid]
    return {
        "grid": grid,
        "d1": d1,
        "d2": d2,
        "first": analyse(d1, grid),
        "second": analyse(d2, grid),
    }


def build(tickers, series):
    """Строит распределения и сравнивает все пары.

    ``series`` - {тикер: интервальный ряд из лабораторной работы №1}.
    Возвращает (distributions, comparisons, pairs).
    """
    dists = {t: Distribution(series[t]) for t in tickers}
    pairs = []
    comparisons = {}
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            a, b = tickers[i], tickers[j]
            comparisons[(a, b)] = compare(dists[a], dists[b])
            pairs.append((a, b))
    return dists, comparisons, pairs


# ---------------------------------------------------------------------------
# Сводка по выборке
# ---------------------------------------------------------------------------
def describe_sample(values):
    """Среднее, стандартное отклонение и вероятности для таблицы."""
    ordered = sorted(values)
    n = len(ordered)
    mean = sum(ordered) / n
    var = sum((x - mean) ** 2 for x in ordered) / n
    return {
        "n": n,
        "min": ordered[0],
        "max": ordered[-1],
        "mean": mean,
        "std": var ** 0.5,
        "p_neg": sum(1 for x in ordered if x <= 0.0) / n,
        "p_drop": sum(1 for x in ordered if x <= -0.03) / n,
    }
