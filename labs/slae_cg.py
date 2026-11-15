# -*- coding: utf-8 -*-
"""СЛАУ методом сопряжённых градиентов: варианты и замеры (ЛР2-5).

Во всех четырёх вариантах исполняется один и тот же метод сопряжённых
градиентов. Отличается только реализация двух массовых операций:

* умножения матрицы на вектор ``y = A x``;
* скалярного произведения векторов ``(x, y)``.

Поэтому разница во времени связана со способом исполнения, а не с разными
алгоритмами: все варианты делают одинаковое число итераций и дают один и
тот же вектор решения.

Модуль сознательно не импортирует matplotlib и python-docx: его загружают
рабочие процессы пула, и лишние импорты исказили бы время старта.

Запуск замеров отдельно::

    python -m labs.slae_cg --force
"""
import json
import math
import os
import platform
import random
import statistics
import time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(HERE, "out")
CACHE = os.path.join(OUT_DIR, "slae_timings.json")

SIZES = (300, 600, 1200)
WORKERS = 4
REPEATS = 3
SEED = 42
SPREAD = 100.0          # разброс диагонали: от 1 до SPREAD
TOL = 1e-8              # допуск по относительной невязке
MAXIT = 500
CPU_NAME = "AMD Ryzen 5 7500F"


# ---------------------------------------------------------------------------
# Тестовая система
# ---------------------------------------------------------------------------
def make_system(n, seed=SEED, spread=SPREAD):
    """Симметричная положительно определённая матрица и правая часть.

    Матрица строится как диагональ с логарифмическим разбросом значений
    (от 1 до ``spread``) плюс малая симметричная связь между всеми парами
    индексов. Диагональ строго доминирует, поэтому матрица положительно
    определена, а число обусловленности близко к ``spread``: метод
    сопряжённых градиентов сходится за десятки итераций, а не за одну.

    Правая часть берётся как ``b = A * (1, ..., 1)``, поэтому точное решение
    известно и его можно проверить.
    """
    rnd = random.Random(seed)
    a = [[0.0] * n for _ in range(n)]
    for i in range(n):
        a[i][i] = 1.0 + (spread - 1.0) * i / (n - 1)
    for i in range(n - 1):
        for j in range(i + 1, n):
            v = 0.5 * (rnd.random() + rnd.random()) / n
            a[i][j] = v
            a[j][i] = v
    b = [sum(row) for row in a]          # A * (1, ..., 1)
    return a, b


# ---------------------------------------------------------------------------
# Две массовые операции
# ---------------------------------------------------------------------------
def dot(x, y):
    """Последовательное скалярное произведение: (x, y) = sum x_i y_i."""
    s = 0.0
    for a, b in zip(x, y):
        s += a * b
    return s


def matvec(a, x):
    """Последовательное умножение матрицы на вектор: y_i = (a_i, x)."""
    return [sum(ai * xj for ai, xj in zip(row, x)) for row in a]


# ---------------------------------------------------------------------------
# Рабочие процессы
# ---------------------------------------------------------------------------
_STATE = {}


def _init_worker(matrix):
    """Кладёт матрицу в память рабочего процесса (один раз за пул).

    Матрица пересылается один раз при создании пула, а не на каждой
    итерации: иначе накладные расходы на pickle были бы больше полезной
    работы. Вектор передаётся с каждой задачей, но он в n раз короче.
    """
    _STATE["a"] = matrix


def _matvec_block(task):
    """Задача 1: строки i0..i1 матрицы, умноженные на вектор x."""
    i0, i1, x = task
    a = _STATE["a"]
    out = []
    for i in range(i0, i1):
        s = 0.0
        for ai, xj in zip(a[i], x):
            s += ai * xj
        out.append(s)
    return out


def _dot_block(task):
    """Задача 2: частичное скалярное произведение блоков x и y."""
    i0, i1, x, y = task
    s = 0.0
    for i in range(i0, i1):
        s += x[i] * y[i]
    return s


def _blocks(n, parts):
    """Границы равных блоков: [(0, n/k), (n/k, 2n/k), ...]."""
    step = n // parts
    return [(i * step, (i + 1) * step) for i in range(parts - 1)] + \
           [((parts - 1) * step, n)]


def parallel_matvec(pool, parts):
    """Умножение матрицы на вектор, разбитое по строкам между процессами."""
    def run(x):
        tasks = [(i0, i1, x) for i0, i1 in _blocks(len(x), parts)]
        return [v for chunk in pool.map(_matvec_block, tasks) for v in chunk]
    return run


def parallel_dot(pool, parts):
    """Скалярное произведение, разбитое на блоки с досчётом суммы."""
    def run(x, y):
        tasks = [(i0, i1, x, y) for i0, i1 in _blocks(len(x), parts)]
        return math.fsum(pool.map(_dot_block, tasks))
    return run


# ---------------------------------------------------------------------------
# Метод сопряжённых градиентов
# ---------------------------------------------------------------------------
def cg(matvec_op, dot_op, b, tol=TOL, maxit=MAXIT):
    """Метод сопряжённых градиентов для A x = b (A симметрична и СПО).

    ``matvec_op(x)`` - умножение матрицы на вектор, ``dot_op(x, y)`` -
    скалярное произведение. Обе операции передаются параметрами, поэтому
    сам метод записан один раз и не зависит от того, какая из них
    параллельная.

    Возвращает (x, число итераций, относительная невязка).
    """
    n = len(b)
    x = [0.0] * n
    r = list(b)                 # r = b - A x, при x = 0 это b
    p = list(r)                 # первое направление спуска
    rs = dot_op(r, r)
    norm_b = math.sqrt(dot_op(b, b))
    iters = 0
    resid = math.sqrt(rs) / norm_b
    while iters < maxit and resid > tol:
        iters += 1
        ap = matvec_op(p)
        alpha = rs / dot_op(p, ap)
        x = [xi + alpha * pi for xi, pi in zip(x, p)]
        r = [ri - alpha * api for ri, api in zip(r, ap)]
        rs_new = dot_op(r, r)
        resid = math.sqrt(rs_new) / norm_b
        beta = rs_new / rs
        p = [ri + beta * pi for ri, pi in zip(r, p)]
        rs = rs_new
    return x, iters, resid


# ---------------------------------------------------------------------------
# Четыре варианта решения
# ---------------------------------------------------------------------------
def solve_sequential(a, b):
    """Пункт 1: обе массовые операции последовательные."""
    return cg(lambda x: matvec(a, x), dot, b)


def solve_parallel_matvec(a, b, workers=WORKERS):
    """Пункт 2: параллельное умножение матрицы на вектор.

    Пул создаётся один раз на всё решение: платить за запуск процессов на
    каждой итерации бессмысленно.
    """
    with ProcessPoolExecutor(workers, initializer=_init_worker,
                             initargs=(a,)) as pool:
        return cg(parallel_matvec(pool, workers), dot, b)


def solve_parallel_dot(a, b, workers=WORKERS):
    """Пункт 3: параллельное скалярное произведение.

    Матрица рабочим процессам не нужна, поэтому в пул она не пересылается.
    """
    with ProcessPoolExecutor(workers) as pool:
        return cg(lambda x: matvec(a, x), parallel_dot(pool, workers), b)


def solve_parallel_both(a, b, workers=WORKERS):
    """Пункт 4: параллельны и умножение матрицы на вектор, и произведение."""
    with ProcessPoolExecutor(workers, initializer=_init_worker,
                             initargs=(a,)) as pool:
        return cg(parallel_matvec(pool, workers),
                  parallel_dot(pool, workers), b)


METHODS = (
    ("sequential", solve_sequential, "Последовательный"),
    ("matvec", solve_parallel_matvec, "Умножение матрицы на вектор"),
    ("dot", solve_parallel_dot, "Скалярное произведение"),
    ("both", solve_parallel_both, "Полный параллелизм"),
)


# ---------------------------------------------------------------------------
# Замеры
# ---------------------------------------------------------------------------
def _time_ms(func, a, b, repeats):
    """Медиана времени решения и результат последнего прогона."""
    times, out = [], None
    for _ in range(repeats):
        t0 = time.perf_counter()
        out = func(a, b)
        times.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(times), out


def _max_diff(x, y):
    return max(abs(xi - yi) for xi, yi in zip(x, y))


def run_benchmark(force=False):
    """Замеряет четыре варианта на системах трёх размеров.

    Результат кэшируется в ``out/slae_timings.json``: сборка отчёта не
    должна каждый раз ждать все решения. Пересчитать -
    ``run_benchmark(force=True)``.
    """
    config = dict(sizes=list(SIZES), workers=WORKERS, repeats=REPEATS,
                  seed=SEED, spread=SPREAD, tol=TOL, maxit=MAXIT)
    if not force and os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            cached = json.load(f)
        if cached.get("config") == config:
            return cached

    env = {
        "cpu": CPU_NAME,
        "cores": "6",
        "threads": str(os.cpu_count()),
        "ram": "32",
        "python": platform.python_version(),
        "os": platform.platform(terse=True).replace("-", " "),
    }
    rows = []
    for n in SIZES:
        a, b = make_system(n)
        exact = [1.0] * n
        row = {"n": n, "methods": {}}
        reference = None
        for key, func, _title in METHODS:
            ms, (x, iters, resid) = _time_ms(func, a, b, REPEATS)
            if reference is None:
                reference = x
            row["methods"][key] = {
                "median_ms": ms,
                "iterations": iters,
                "residual": resid,
                "error": _max_diff(x, exact),
                "deviation": _max_diff(x, reference),
            }
        row["ok"] = all(m["deviation"] < 1e-6 and m["residual"] < 10 * TOL
                        for m in row["methods"].values())
        rows.append(row)
        print("N = %d: %s" % (n, ", ".join(
            "%s %.0f мс" % (title, row["methods"][key]["median_ms"])
            for key, _f, title in METHODS)))

    data = {"config": config, "env": env, "rows": rows}
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


if __name__ == "__main__":
    import sys
    run_benchmark(force="--force" in sys.argv)
    print(CACHE)
