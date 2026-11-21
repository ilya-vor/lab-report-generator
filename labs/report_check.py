# -*- coding: utf-8 -*-
"""Проверка вёрстки готового PDF.

    python -m labs.report_check out/report.pdf          # сводка по страницам
    python -m labs.report_check out/report.pdf 4 5      # дамп страниц 4 и 5

Сводка показывает, чем начинается и заканчивается каждая страница и сколько
свободного места осталось до штампа: так видно «пустые хвосты» разделов и
картинки, которые не поместились.
"""
import sys

import fitz

STAMP_Y = 790.0


def summary(path):
    doc = fitz.open(path)
    print("страниц:", doc.page_count)
    for i, page in enumerate(doc):
        blocks = [b for b in page.get_text("blocks")
                  if b[4].strip() and b[1] < STAMP_Y]
        blocks.sort(key=lambda b: b[1])
        if not blocks:
            print("%2d: пусто" % (i + 1))
            continue
        first = " ".join(blocks[0][4].split())[:60]
        last = " ".join(blocks[-1][4].split())[:60]
        free = STAMP_Y - blocks[-1][3]
        print("%2d: y=%.0f-%.0f свободно %.0f pt | %s ... %s"
              % (i + 1, blocks[0][1], blocks[-1][3], free, first, last))
    return 0


def dump(path, pages=None):
    doc = fitz.open(path)
    wanted = pages or range(1, doc.page_count + 1)
    for number in wanted:
        page = doc[number - 1]
        print("========== СТРАНИЦА %d ==========" % number)
        blocks = page.get_text("blocks")
        for block in sorted(blocks, key=lambda b: (round(b[1], 1), b[0])):
            x0, y0, x1, y1, text = block[:5]
            text = " ".join(text.split())
            if text:
                print("y=%.0f x=%.0f | %s" % (y0, x0, text[:110]))
        print("картинок:", len(page.get_images(full=True)))
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) > 1:
        raise SystemExit(dump(args[0], [int(a) for a in args[1:]]))
    raise SystemExit(summary(args[0]))
