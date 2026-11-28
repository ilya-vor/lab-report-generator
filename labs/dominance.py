# -*- coding: utf-8 -*-
"""Стохастическое доминирование для лабораторной работы №2.

Сравниваются эмпирические законы распределения дневных доходностей трёх
акций, построенные в лабораторной работе №1 как интервальные вариационные
ряды. Закон задаётся дискретной случайной величиной: значениями служат
середины интервалов x_j, вероятностями - относительные частоты p_j.
Поэтому функция распределения F ступенчата (кусочно-постоянна), а её
интеграл G - непрерывная кусочно-линейная функция.

Для пары (A, B):

    F_A(x) = P(A <= x) = сумма p_j по всем x_j <= x;
    G_A(x) = интеграл F_A от -oo до x.

A доминирует B в первом порядке, если F_A(x) <= F_B(x) при всех x;
во втором порядке - если G_A(x) <= G_B(x) при всех x. Разность
D1 = F_A - F_B ступенчата, её интеграл D2 = G_A - G_B линеен на участках
между серединами интервалов. Смена знака разности означает отсутствие
доминирования.

Модуль не импортирует matplotlib и python-docx.
"""
import bisect


# ---------------------------------------------------------------------------
# Эмпирический закон из интервального ряда
# ---------------------------------------------------------------------------
class Distribution:
    """Дискретная величина по серединам интервалов вариационного ряда."""

    def __init__(self, series):
        self.edges = list(series["edges"])
        self.x = list(series["mids"])
        self.p = list(series["freq"])
        self.cum = []
        total = 0.0
        for prob in self.p:
            total += prob
            self.cum.append(total)
        self.lo = self.x[0]
        self.hi = self.x[-1]

    def F(self, x):
        """Функция распределения F(x) - ступенчатая, непрерывна справа."""
        j = bisect.bisect_right(self.x, x)
        return self.cum[j - 1] if j else 0.0

    def F_left(self, x):
        """Предел F слева от x (для величины скачка в точке x)."""
        j = bisect.bisect_left(self.x, x)
        return self.cum[j - 1] if j else 0.0

    def jump(self, x):
        """Скачок функции распределения в точке x."""
        return self.F(x) - self.F_left(x)

    def S(self, x):
        """Интеграл F от -oo до x: непрерывная кусочно-линейная функция."""
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

    def terms(self):
        """Слагаемые F(x) = сумма p_j * 1[x_j <= x]."""
        return [(value, prob) for value, prob in zip(self.x, self.p)]


# ---------------------------------------------------------------------------
# Анализ разности функций
# ---------------------------------------------------------------------------
def analyse(diffs, grid, tol=1e-9, step=False):
    """Сводка по разности: экстремумы и точки перемены знака.

    ``step`` = True для ступенчатой разности: переход через ноль происходит
    в узле сетки, а не между узлами.
    """
    lo = min(range(len(diffs)), key=lambda i: diffs[i])
    hi = max(range(len(diffs)), key=lambda i: diffs[i])
    signs = [1 if v > tol else (-1 if v < -tol else 0) for v in diffs]

    crossings = []
    previous = None
    for i, sign in enumerate(signs):
        if not sign:
            continue
        if previous is not None and sign != previous:
            span = diffs[i] - diffs[i - 1]
            ratio = -diffs[i - 1] / span if span else 0.0
            point = (grid[i] if step
                     else grid[i - 1] + ratio * (grid[i] - grid[i - 1]))
            crossings.append(point)
        previous = sign

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


# ---------------------------------------------------------------------------
# Сравнение пары распределений
# ---------------------------------------------------------------------------
def integral_terms(dist_a, dist_b):
    """Слагаемые интеграла разности: D2(t) = сумма c_u * (t - u)_+.

    Разность F_A - F_B ступенчата, её скачок в точке u равен разности
    скачков функций распределения. Интеграл такой разности - непрерывная
    кусочно-линейная функция с изломами в серединах интервалов.
    """
    terms = []
    for u in sorted(set(dist_a.x) | set(dist_b.x)):
        coef = dist_a.jump(u) - dist_b.jump(u)
        if abs(coef) > 1e-12:
            terms.append((u, coef))
    return terms


def compare(dist_a, dist_b, points=1600):
    """Разности D1 и D2 на общей сетке."""
    lo = min(dist_a.lo, dist_b.lo)
    hi = max(dist_a.hi, dist_b.hi)
    grid = sorted(set(dist_a.x) | set(dist_b.x)
                  | {lo + (hi - lo) * i / float(points)
                     for i in range(points + 1)})
    d1 = [dist_a.F(x) - dist_b.F(x) for x in grid]
    d2 = [dist_a.S(x) - dist_b.S(x) for x in grid]
    return {
        "grid": grid,
        "d1": d1,
        "d2": d2,
        "terms": integral_terms(dist_a, dist_b),
        "first": analyse(d1, grid, step=True),
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
