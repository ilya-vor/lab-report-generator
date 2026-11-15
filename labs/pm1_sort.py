# -*- coding: utf-8 -*-
"""Параллельные методы сортировки: алгоритмы и замеры (ЛР1, «Параллельные методы»).

Модуль сознательно не импортирует matplotlib и python-docx: его загружают
рабочие процессы пула, и лишние импорты исказили бы время старта.

Все три варианта используют один и тот же алгоритм - сортировку слиянием.
Отличается только способ исполнения: последовательный вызов, пул потоков,
пул процессов. Иначе сравнение времени теряет смысл.

Запуск замеров отдельно::

    python -m labs.pm1_sort --force
"""
import json
import os
import platform
import random
import statistics
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(HERE, "out")
CACHE = os.path.join(OUT_DIR, "pm1_timings.json")

SIZES = (100_000, 300_000, 1_000_000)
WORKERS = 4
REPEATS = 5
SEED = 42
VALUE_MAX = 1_000_000
CPU_NAME = "AMD Ryzen 5 7500F"


# ---------------------------------------------------------------------------
# Алгоритм: сортировка слиянием
# ---------------------------------------------------------------------------
def merge(a, b):
    """Слияние двух упорядоченных списков за один проход."""
    out = []
    i = j = 0
    la, lb = len(a), len(b)
    while i < la and j < lb:
        if a[i] <= b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append(b[j])
            j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out


def merge_sort(data):
    """Последовательная сортировка слиянием: деление пополам и слияние."""
    n = len(data)
    if n <= 1:
        return list(data)
    m = n // 2
    return merge(merge_sort(data[:m]), merge_sort(data[m:]))


def split_parts(data, parts):
    """Делит ряд на равные части (последняя забирает остаток)."""
    step = len(data) // parts
    return [data[i * step:(i + 1) * step] for i in range(parts - 1)] + \
           [data[(parts - 1) * step:]]


def _sort_part(part):
    """Задача для рабочего потока или процесса."""
    return merge_sort(part)


def _merge_pair(pair):
    """Задача слияния пары частей."""
    return merge(pair[0], pair[1])


def _merge_rounds(parts, submit):
    """Попарное слияние частей: каждый раунд уменьшает их число вдвое.

    ``submit`` - функция, исполняющая список задач и возвращающая список
    результатов (``ex.map`` пула потоков или процессов).
    """
    while len(parts) > 1:
        pairs = [(parts[i], parts[i + 1])
                 for i in range(0, len(parts), 2)]
        parts = list(submit(_merge_pair, pairs))
    return parts[0]


# ---------------------------------------------------------------------------
# Параллельные варианты
# ---------------------------------------------------------------------------
def sort_threads(data, workers=WORKERS):
    """Сортировка слиянием в пуле потоков: части сортируются параллельно.

    Потоки делят одно адресное пространство и один интерпретатор, поэтому
    сортировка (циклы на Python) упирается в GIL.
    """
    with ThreadPoolExecutor(workers) as ex:
        parts = list(ex.map(_sort_part, split_parts(data, workers)))
        return _merge_rounds(parts, ex.map)


def sort_processes(data, workers=WORKERS):
    """Сортировка слиянием в пуле процессов: части уходят в отдельные ядра.

    Пул создаётся внутри вызова, поэтому в замер входит и накладные расходы
    на запуск рабочих процессов, и пересылка частей через pickle.
    """
    with ProcessPoolExecutor(workers) as ex:
        parts = list(ex.map(_sort_part, split_parts(data, workers)))
        return _merge_rounds(parts, ex.map)


METHODS = (
    ("sequential", merge_sort, "Последовательный"),
    ("threads", sort_threads, "Потоки"),
    ("processes", sort_processes, "Процессы"),
)


# ---------------------------------------------------------------------------
# Замеры
# ---------------------------------------------------------------------------
def _median_ms(func, data, repeats):
    """Времена прогонов и результат последнего: медиана устойчива к просадкам."""
    times, result = [], None
    for _ in range(repeats):
        t0 = time.perf_counter()
        result = func(data)
        times.append((time.perf_counter() - t0) * 1000.0)
    return times, result


def _check(result, data):
    """Проверка результата: все методы должны дать один и тот же ряд."""
    return result == sorted(data)


def run_benchmark(force=False):
    """Выполняет замеры и сохраняет их в ``out/pm1_timings.json``.

    Повторный запуск читает кэш: сборка отчёта не должна каждый раз ждать
    сортировку миллиона чисел. Пересчитать - ``run_benchmark(force=True)``.
    """
    config = dict(sizes=list(SIZES), workers=WORKERS, repeats=REPEATS,
                  seed=SEED, value_max=VALUE_MAX)
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
    results = []
    for n in SIZES:
        rnd = random.Random(SEED)
        data = [rnd.randrange(VALUE_MAX) for _ in range(n)]
        reference = sorted(data)

        # прогрев: первый вызов компилирует и прогревает кэши интерпретатора
        merge_sort(data[:1000])
        row = {"n": n, "methods": {}}
        ok = len(reference) == n
        for key, func, _title in METHODS:
            times, result = _median_ms(func, data, REPEATS)
            ok = ok and _check(result, data)
            row["methods"][key] = {
                "median_ms": statistics.median(times),
                "min_ms": min(times),
                "runs_ms": times,
            }
        row["ok"] = ok
        results.append(row)
        print("N = %d: %s" % (n, ", ".join(
            "%s %.0f мс" % (title, row["methods"][key]["median_ms"])
            for key, _f, title in METHODS)))

    data = {"config": config, "env": env, "rows": results}
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


def load_benchmark():
    """Читает готовые замеры (для сборки отчёта)."""
    with open(CACHE, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    import sys
    run_benchmark(force="--force" in sys.argv)
    print(CACHE)
