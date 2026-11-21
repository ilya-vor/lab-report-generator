# -*- coding: utf-8 -*-
"""Грубый просмотр картинки в текстовом виде: python -m labs.img_peek file.png.

Печатает карту плотности символов. Нужен только чтобы поймать явные промахи
вёрстки (обрезанная подпись, наложение блоков), а не для оценки качества.
"""
import sys

from PIL import Image


def peek(path, width=100, height=34):
    image = Image.open(path).convert("L")
    small = image.resize((width, height), Image.LANCZOS)
    pixels = list(small.getdata())
    chars = " .:-=+*#%@"
    for row in range(height):
        line = []
        for col in range(width):
            value = pixels[row * width + col]
            idx = int((255 - value) / 255.0 * (len(chars) - 1))
            line.append(chars[idx])
        print("".join(line))
    print("%s: %dx%d px" % (path, image.width, image.height))


if __name__ == "__main__":
    peek(sys.argv[1])
