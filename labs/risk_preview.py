# -*- coding: utf-8 -*-
"""Числа «на глаз» без сборки отчёта: python -m labs.risk_preview.

Печатает по каждой акции вариационный ряд и все меры риска. Нужен, чтобы
сверить значения с ручным расчётом или с таблицами отчёта, не тратя время
на сборку DOCX и экспорт в PDF.
"""
from labs import risk_data, risk_measures

dates, data = risk_data.load()
res = risk_measures.compute(data)
for ticker, item in res.items():
    p = item["profile"]
    s = item["series"]
    print("== %s  n=%d k=%d h=%.5f" % (ticker, p["n"], s["k"], s["h"]))
    print("   mean=%+.5f std=%.5f LVar=%.8f Lstd=%.6f mass=%.6f"
          % (p["mean"], p["std"], p["lvar"], p["lstd"], p["left_mass"]))
    print("   min=%+.4f max=%+.4f" % (p["min"], p["max"]))
    print("   VaR : %s" % {a: round(v, 5) for a, v in p["var_"].items()})
    print("   CVaR: %s  хвост: %s"
          % ({a: round(v, 5) for a, v in p["cvar"].items()},
             p["tail_mass"]))
    print("   частоты: %s" % s["counts"])
