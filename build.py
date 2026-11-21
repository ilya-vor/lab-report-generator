# -*- coding: utf-8 -*-
"""Единая точка сборки отчётов по лабораторным работам.

    python build.py --lab 2            # схемы + DOCX
    python build.py --lab 2 --pdf      # то же и PDF (нужен установленный Word)
    python build.py --lab 2 --no-fields  # не трогать поля и TOC
    python build.py --compact out/x.docx  # выкинуть неиспользуемые картинки

Каждая лаба - модуль из пакета ``labs`` с функцией ``build()``.
Новая лаба: создайте ``labs/labN_<тема>.py`` (см. ``docs/next-lab.md``),
допишите пару ``LABS`` - и всё, других правок не нужно.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# номер лабы -> модуль пакета labs с функцией build()
LABS = {
    "2": "labs.lab2_siz",
    "3": "labs.lab3_sppr",
    "4": "labs.lab4_ontology",
    "5": "labs.lab5_models",
    "6": "labs.lab6_efficiency",
    "pm1": "labs.lab_pm1",
    "risk1": "labs.lab_risk",
    "risk2": "labs.lab_dominance",
    "slae": "labs.lab_slae",
}


def run(lab):
    mod = __import__(LABS[lab], fromlist=["build"])
    return [mod.build()]


def update_fields(path):
    """Обновляет поля и содержание через Word."""
    ps = os.path.join(HERE, "update_fields.ps1")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", ps, "-Path", path], check=False)


def to_pdf(path):
    """Экспорт в PDF через Word (COM)."""
    ps = os.path.join(HERE, "to_pdf.ps1")
    pdf = os.path.splitext(path)[0] + ".pdf"
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", ps, "-Path", path, "-Out", pdf], check=False)
    return pdf


def main(argv=None):
    ap = argparse.ArgumentParser(description="Сборка отчёта по лабораторной")
    ap.add_argument("--compact", action="store_true",
                    help="удалить из DOCX (--labs/файлов) картинки без ссылок")
    ap.add_argument("--lab", default="2", choices=sorted(LABS),
                    help="номер лабораторной работы")
    ap.add_argument("--pdf", action="store_true", help="собрать ещё и PDF")
    ap.add_argument("--no-fields", action="store_true",
                    help="не обновлять поля и содержание")
    ap.add_argument("files", nargs="*", help="файлы DOCX для --compact")
    args = ap.parse_args(argv)

    if args.compact:
        from labkit.docxgen import compact_package
        for path in args.files:
            print("compact: %s -%d" % (path, compact_package(path)))
        return 0

    for path in run(args.lab):
        print("DOCX:", path)
        if not args.no_fields:
            update_fields(path)
        if args.pdf:
            print("PDF :", to_pdf(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
