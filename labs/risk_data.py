# -*- coding: utf-8 -*-
"""Данные для лабораторной работы «Меры риска».

Модуль скачивает дневные цены закрытия трёх акций за два года и складывает
их в ``labs/data/risk_quotes.csv``. Файл лежит в репозитории, поэтому отчёт
пересобирается без сети и с теми же числами: сеть нужна только для
обновления выборки (``python -m labs.risk_data --force``).

Тикеры: Bayer AG - Xetra (BAYN.DE, евро), Merck & Co - NYSE (MRK, доллар),
Sanofi - Euronext Paris (SAN.PA, евро).

Биржи работают по своим календарям, поэтому ряды приводятся к общим датам:
остаются только дни, когда торговались все три бумаги. Иначе доходности
соседних строк считались бы за разное число календарных дней и сравнение
дисперсий потеряло бы смысл.

Модуль сознательно не импортирует matplotlib и python-docx: его загружают
и отчёт, и отдельный расчёт.
"""
import argparse
import csv
import datetime as dt
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
CSV_PATH = os.path.join(DATA_DIR, "risk_quotes.csv")

TICKERS = ("BAYN.DE", "MRK", "SAN.PA")
NAMES = {"BAYN.DE": "Bayer", "MRK": "Merck & Co", "SAN.PA": "Sanofi"}
CURRENCY = {"BAYN.DE": "EUR", "MRK": "USD", "SAN.PA": "EUR"}
EXCHANGE = {"BAYN.DE": "Xetra", "MRK": "NYSE", "SAN.PA": "Euronext Paris"}

# Период выборки: два календарных года. Дата конца закреплена, чтобы отчёт
# не менялся от запуска к запуску.
END = dt.date(2026, 11, 17)
START = dt.date(2024, 11, 18)


def download(start=START, end=END, tickers=TICKERS):
    """Скачивает цены закрытия и возвращает {дата: {тикер: цена}}."""
    import yfinance as yf

    frames = {}
    for ticker in tickers:
        frame = yf.download(ticker, start=start, end=end, progress=False,
                            auto_adjust=True)
        if frame is None or len(frame) == 0:
            raise RuntimeError("нет данных по тикеру %s" % ticker)
        close = frame["Close"]
        if hasattr(close, "columns"):          # MultiIndex при одном тикере
            close = close.iloc[:, 0]
        frames[ticker] = {d.date() if hasattr(d, "date") else d: float(v)
                          for d, v in close.items()}

    common = set(frames[tickers[0]])
    for ticker in tickers[1:]:
        common &= set(frames[ticker])
    dates = sorted(common)
    if len(dates) < 400:
        raise RuntimeError("общих торговых дней слишком мало: %d" % len(dates))
    return {d: {t: frames[t][d] for t in tickers} for d in dates}


def save_csv(rows, path=CSV_PATH, tickers=TICKERS):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date"] + list(tickers))
        for day in sorted(rows):
            writer.writerow([day.isoformat()]
                            + ["%.4f" % rows[day][t] for t in tickers])
    return path


def load_csv(path=CSV_PATH):
    """Читает цены: (даты, {тикер: [цена, ...]})."""
    dates, series = [], {t: [] for t in TICKERS}
    with open(path, encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        tickers = [h.strip() for h in header[1:]]
        for row in reader:
            dates.append(dt.date.fromisoformat(row[0]))
            for ticker, value in zip(tickers, row[1:]):
                series[ticker].append(float(value))
    return dates, series


def returns(prices):
    """Простые дневные доходности: X_t = (P_t - P_(t-1)) / P_(t-1)."""
    return [(b - a) / a for a, b in zip(prices, prices[1:])]


def load(force=False):
    """Возвращает {тикер: [доходность, ...]} и даты доходностей."""
    if force or not os.path.exists(CSV_PATH):
        save_csv(download())
    dates, prices = load_csv()
    data = {ticker: returns(prices[ticker]) for ticker in prices}
    return dates[1:], data


def main(argv=None):
    parser = argparse.ArgumentParser(description="Данные для мер риска")
    parser.add_argument("--force", action="store_true",
                        help="перекачать котировки из сети")
    parser.add_argument("--show", action="store_true",
                        help="напечатать сводку по выборке")
    args = parser.parse_args(argv)

    dates, data = load(force=args.force)
    print("файл :", CSV_PATH)
    print("период: %s - %s" % (dates[0], dates[-1]))
    if args.show:
        for ticker, values in data.items():
            print("%-8s n=%d  min=%.4f  max=%.4f  mean=%.5f"
                  % (ticker, len(values), min(values), max(values),
                     sum(values) / len(values)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
