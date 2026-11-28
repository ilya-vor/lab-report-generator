# -*- coding: utf-8 -*-
"""Ожидаемая полезность для лабораторной работы №3.

Модуль считает критерий ожидаемой полезности Vu(X) = E[u(X)] по
интервальному вариационному ряду из лабораторной работы №1. Никаких
matplotlib и docx: его загружают и отчёт, и отдельный расчёт.

Две функции полезности:

* аналитическая по варианту 3 (нечётный номер, n = 3):
  ``u(x) = x ** (1 / (n + 2)) = x ** 0.2`` - вогнутая возрастающая функция,
  для отрицательных x берётся нечётный корень: ``sign(x) * |x| ** 0.2``.
  Аргумент - доходность в процентах.
* эмпирическая: точки (x_j, u_j) строятся по процедуре деления пополам
  (лекции), затем соединяются монотонным кубическим сплайном
  Фрича-Карлсона (PCHIP) без scipy. Модель ЛПР - постоянная абсолютная
  несклонность к риску ``u0(x) = 1 - exp(-lam * x)``, поэтому
  эквивалент уверенности пары (a, b) считается аналитически.

Ожидание берётся по интервальному ряду: внутри интервала распределение
равномерно, интеграл от u считается квадратурой Гаусса-Лежандра (8 узлов).
Середины интервалов не годятся: у ``x ** 0.2`` бесконечная производная в
нуле, и интервал, содержащий 0, дал бы грубую ошибку.
"""
import bisect
import math

# --- вариант 3: нечётный n, u(x) = x ** (1 / (n + 2)) -----------------------
VARIANT = 3
POWER = 1.0 / (VARIANT + 2)          # 0.2

# --- модель ЛПР для эмпирической полезности ---------------------------------
LAMBDA = 0.20                         # 1 / процент, CARA
KNOT_LEVELS = 8                       # 8 шагов -> 9 точек (0, 1/8, ..., 1)

# --- квадратура Гаусса-Лежандра, 8 узлов ------------------------------------
GAUSS_X = (-0.9602898564975363, -0.7966664774136267,
           -0.5255324099163290, -0.1834346424956498,
           0.1834346424956498, 0.5255324099163290,
           0.7966664774136267, 0.9602898564975363)
GAUSS_W = (0.1012285362903763, 0.2223810344533745,
           0.3137066458778873, 0.3626837833783620,
           0.3626837833783620, 0.3137066458778873,
           0.2223810344533745, 0.1012285362903763)


# ---------------------------------------------------------------------------
# Аналитическая функция полезности варианта
# ---------------------------------------------------------------------------
def power_utility(x):
    """u(x) = sign(x) * |x| ** POWER, x - доходность в процентах."""
    if x == 0.0:
        return 0.0
    return math.copysign(abs(x) ** POWER, x)


def power_derivatives(x):
    """u'(x) и u''(x) для аналитической функции."""
    ax = abs(x)
    first = POWER * ax ** (POWER - 1.0)
    second = POWER * (POWER - 1.0) * ax ** (POWER - 2.0)
    return first, second


def absolute_risk_aversion(x):
    """ARA(x) = -u''(x) / u'(x) = (1 - POWER) / |x|."""
    return (1.0 - POWER) / abs(x)


def power_integral(a, b):
    """Точный интеграл u(x) = sign(x)|x|^0,2 на отрезке [a; b].

    Первообразная равна |x|^1,2 / 1,2: при x > 0 это (x^1,2)/1,2, при x < 0
    она также положительна, но с обратным знаком аргумента, поэтому
    производная равна sign(x)·|x|^0,2. Интегрирование по интервалу
    вариационного ряда выполняется без квадратуры: подынтегральная функция
    имеет бесконечную производную в нуле, и любой численный метод на
    интервале, содержащем нуль, сходится медленно.
    """
    def antiderivative(x):
        return abs(x) ** (POWER + 1.0) / (POWER + 1.0)

    return antiderivative(b) - antiderivative(a)


def normalize(func, lo, hi):
    """Аффинное приведение полезности к отрезку [0; 1].

    Для критерия это преобразование безразлично: Vu сдвигается и
    растягивается так же, как u, а порядок альтернатив не меняется.
    """
    u_lo, u_hi = func(lo), func(hi)
    span = u_hi - u_lo

    def scaled(x):
        return (func(x) - u_lo) / span

    scaled.raw = func
    scaled.lo = lo
    scaled.hi = hi
    return scaled


# ---------------------------------------------------------------------------
# Ожидание по интервальному ряду
# ---------------------------------------------------------------------------
def interval_integral(func, a, b):
    """Интеграл полезности по отрезку [a; b].

    Если у функции есть точная первообразная, используется она; иначе
    применяется квадратура Гаусса-Лежандра с восемью узлами.
    """
    exact = getattr(func, "integral", None)
    if exact is not None:
        return exact(a, b)
    if func is power_utility:
        return power_integral(a, b)
    center, half = 0.5 * (a + b), 0.5 * (b - a)
    acc = 0.0
    for node, weight in zip(GAUSS_X, GAUSS_W):
        acc += weight * func(center + half * node)
    return 0.5 * half * acc


def mean_utility(series, func, index, scale=100.0):
    """Среднее значение полезности на интервале с номером ``index``.

    Внутри интервала распределение равномерно, поэтому среднее равно
    (1 / h_j) · ∫ u(x) dx. Именно оно, а не значение в середине, входит
    в критерий Vu(X).
    """
    a = series["edges"][index] * scale
    b = series["edges"][index + 1] * scale
    return interval_integral(func, a, b) / (b - a)


def expected_utility(series, func, scale=100.0):
    """Vu = E[u(X)] по интервальному ряду.

    ``series`` - словарь ``variation_series``; границы интервалов заданы в
    долях, поэтому перед подстановкой в u они умножаются на ``scale``, то
    есть функция полезности определена на процентах. Внутри интервала
    распределение равномерно, поэтому вклад интервала равен
    p_j · (1 / h_j) · ∫ u(x) dx.
    """
    total = 0.0
    for j, p in enumerate(series["freq"]):
        total += p * mean_utility(series, func, j, scale)
    return total


def midpoint_utility(series, func, scale=100.0):
    """Vu при замене интервала его серединой (метод середин).

    Так считают, когда интеграла под рукой нет: Vu = Σ p_j · u(x_j).
    Для функции варианта метод даёт систематическую ошибку, потому что
    среднее корня по интервалу не равно корню из середины.
    """
    total = 0.0
    for j, p in enumerate(series["freq"]):
        total += p * func(series["mids"][j] * scale)
    return total


# ---------------------------------------------------------------------------
# Эмпирическая функция полезности по точкам
# ---------------------------------------------------------------------------
def certainty_equivalent(a, b, lam=LAMBDA):
    """Эквивалент уверенности 50/50-лотереи между a и b для CARA.

    u0(x) = 1 - exp(-lam x), угроза (a, 0.5; b, 0.5) имеет ожидаемую
    полезность (u0(a) + u0(b)) / 2, обратная функция даёт
    x = -ln((exp(-lam a) + exp(-lam b)) / 2) / lam.
    """
    target = 0.5 * (math.exp(-lam * a) + math.exp(-lam * b))
    # target > 1 законно: при x < 0 полезность u0(x) < 0, и логарифм
    # автоматически даёт отрицательный эквивалент уверенности.
    return -math.log(max(target, 1e-300)) / lam


def utility_knots(lo, hi, lam=LAMBDA, levels=KNOT_LEVELS):
    """Точки эмпирической полезности: u(lo) = 0, u(hi) = 1.

    Процедура деления пополам: для отрезка [a, b] с полезностями [ua, ub]
    находится эквивалент уверенности m лотереи 50/50 и полагается
    u(m) = (ua + ub) / 2. Уровни получаются равномерными: 1/8, 2/8, ...
    Возвращается список пар (x, u), отсортированный по x.
    """
    points = [(lo, 0.0), (hi, 1.0)]
    queue = [(lo, hi, 0.0, 1.0)]
    for _ in range(int(math.log2(levels))):
        nxt = []
        for a, b, ua, ub in queue:
            m = certainty_equivalent(a, b, lam)
            um = 0.5 * (ua + ub)
            points.append((m, um))
            nxt.append((a, m, ua, um))
            nxt.append((m, b, um, ub))
        queue = nxt
    points.sort()
    return points


class InterpolatedUtility:
    """Монотонный кубический сплайн (Фрич-Карлсон) по точкам полезности.

    Устойчивее обычного кубического сплайна: между узлами нет выбросов,
    поэтому интерполированная полезность остаётся возрастающей и вогнутой
    там, где этого требуют точки.
    """

    def __init__(self, points):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        n = len(xs)
        d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
        m = [0.0] * n
        m[0], m[-1] = d[0], d[-1]
        for i in range(1, n - 1):
            if d[i - 1] * d[i] <= 0.0:
                m[i] = 0.0
            else:
                w1 = 2.0 * (xs[i + 1] - xs[i]) + (xs[i] - xs[i - 1])
                w2 = (xs[i + 1] - xs[i]) + 2.0 * (xs[i] - xs[i - 1])
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        self.xs, self.ys, self.ms = xs, ys, m

    def __call__(self, x):
        xs, ys, ms = self.xs, self.ys, self.ms
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = bisect.bisect_right(xs, x) - 1
        h = xs[i + 1] - xs[i]
        t = (x - xs[i]) / h
        return ((2 * t ** 3 - 3 * t ** 2 + 1) * ys[i]
                + (t ** 3 - 2 * t ** 2 + t) * h * ms[i]
                + (-2 * t ** 3 + 3 * t ** 2) * ys[i + 1]
                + (t ** 3 - t ** 2) * h * ms[i + 1])

    def integral(self, a, b):
        """Интеграл сплайна по отрезку [a; b] точно по его сегментам.

        На каждом сегменте между узлами функция - кубический многочлен,
        поэтому формула Симпсона по трём точкам даёт точное значение.
        """
        if b < a:
            a, b = b, a
        xs = self.xs
        bounds = [a]
        for x in xs:
            if a < x < b:
                bounds.append(x)
        bounds.append(b)
        total = 0.0
        for left, right in zip(bounds, bounds[1:]):
            if right <= left:
                continue
            mid = 0.5 * (left + right)
            total += (right - left) / 6.0 * (self(left) + 4.0 * self(mid)
                                             + self(right))
        return total

    def inverse(self, value):
        """x, при котором u(x) = value (обратная интерполяция по сетке)."""
        grid = [self.xs[0] + (self.xs[-1] - self.xs[0]) * i / 4000.0
                for i in range(4001)]
        lo, hi = 0, len(grid) - 1
        if value <= self(grid[0]):
            return grid[0]
        if value >= self(grid[-1]):
            return grid[-1]
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self(grid[mid]) < value:
                lo = mid
            else:
                hi = mid
        a, b = grid[lo], grid[hi]
        fa, fb = self(a), self(b)
        return a + (b - a) * (value - fa) / (fb - fa) if fb != fa else a


class LinearUtility:
    """Кусочно-линейная интерполяция точек полезности.

    Используется только для сравнения со сплайном: ломаная проходит через
    те же точки, но в узлах имеет изломы, поэтому вторая производная там
    не определена и вогнутость между узлами не гарантирована.
    """

    def __init__(self, points):
        self.xs = [p[0] for p in points]
        self.ys = [p[1] for p in points]

    def __call__(self, x):
        xs, ys = self.xs, self.ys
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = bisect.bisect_right(xs, x) - 1
        h = xs[i + 1] - xs[i]
        return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / h

    def integral(self, a, b):
        """Интеграл ломаной: сумма площадей трапеций по её звеньям."""
        if b < a:
            a, b = b, a
        bounds = [a] + [x for x in self.xs if a < x < b] + [b]
        total = 0.0
        for left, right in zip(bounds, bounds[1:]):
            if right <= left:
                continue
            total += 0.5 * (self(left) + self(right)) * (right - left)
        return total


# ---------------------------------------------------------------------------
# Полный расчёт по всем бумагам
# ---------------------------------------------------------------------------
def build(tickers, data, k0=None, steps=1):
    """Считает оба критерия и анализ чувствительности по k.

    ``data`` - {тикер: [дневная доходность, ...]}. Возвращает словарь:
    ``k0`` - исходное число интервалов (Стерджис), ``ks`` - сетка k,
    ``lo``/``hi`` - границы общей шкалы полезности, ``knots`` - точки
    эмпирической полезности, ``u_pow``/``u_emp``/``u_lin`` - функции, ``series`` -
    {тикер: ряд при k0}, ``vu``/``vu_emp``/``vu_lin`` - {тикер: значение},
    ``vu_mid``/``vu_emp_mid`` - те же критерии методом середин, ``ce`` -
    {тикер: эквивалент уверенности}, ``sens`` - {k: {тикер: (Vu, Vu_emp)}}.
    """
    from labs import risk_measures

    base = {t: risk_measures.variation_series(data[t]) for t in tickers}
    k0 = k0 or base[tickers[0]]["k"]
    lo = min(min(values) for values in data.values()) * 100.0
    hi = max(max(values) for values in data.values()) * 100.0

    u_pow = power_utility
    knots = utility_knots(lo, hi)
    u_emp = InterpolatedUtility(knots)
    u_lin = LinearUtility(knots)

    series = {t: risk_measures.variation_series(data[t], k0) for t in tickers}
    vu = {t: expected_utility(series[t], u_pow) for t in tickers}
    vu_emp = {t: expected_utility(series[t], u_emp) for t in tickers}
    vu_lin = {t: expected_utility(series[t], u_lin) for t in tickers}
    vu_mid = {t: midpoint_utility(series[t], u_pow) for t in tickers}
    vu_emp_mid = {t: midpoint_utility(series[t], u_emp) for t in tickers}
    ce = {t: u_emp.inverse(vu_emp[t]) for t in tickers}

    k_lo = int(round(0.5 * k0))
    k_hi = int(round(1.5 * k0))
    ks = list(range(k_lo, k_hi + 1, steps))
    if k0 not in ks:
        ks.append(k0)
    ks.sort()
    sens = {}
    for k in ks:
        sens[k] = {}
        for t in tickers:
            row = risk_measures.variation_series(data[t], k)
            sens[k][t] = (expected_utility(row, u_pow),
                          expected_utility(row, u_emp))

    return {
        "k0": k0,
        "ks": ks,
        "lo": lo,
        "hi": hi,
        "knots": knots,
        "u_pow": u_pow,
        "u_emp": u_emp,
        "u_lin": u_lin,
        "series": series,
        "vu": vu,
        "vu_emp": vu_emp,
        "vu_lin": vu_lin,
        "vu_mid": vu_mid,
        "vu_emp_mid": vu_emp_mid,
        "ce": ce,
        "sens": sens,
    }
