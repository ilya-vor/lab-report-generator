# -*- coding: utf-8 -*-
"""Сборка DOCX по шаблону кафедры.

Титульный лист, рамка-штамп (``header1.xml``/``header2.xml``), стили и
автосодержание клонируются из ``report_template.docx``: структуру шаблона
не перерисовываем, меняем только наполнение.

Титул правится не по индексам элементов, а по тексту-маркеру шаблона
(``TPL``), поэтому правки в шаблоне не ломают сборку. Замена текста
выполняется сквозь runs: Word часто дробит «МО-426Б» на «МО-» + «4» + «26Б».

Минимальный пример:

    from labkit.docxgen import Report, ReportMeta
    rep = Report(ReportMeta(lab_no="2", page_title="Тема", full_title="Тема",
                            out_name="lab2.docx"))
    rep.prepare()
    rep.h1("Цель работы")
    rep.p("Текст.")
    rep.save()
"""
import copy
import os
import posixpath
import re
import zipfile
from dataclasses import dataclass, field

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "report_template.docx")
OUT_DIR = os.path.join(ROOT, "out")

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
TNR = "Times New Roman"

# Тексты, которые стоят в шаблоне. По ним ищутся места замены; менять их
# нужно, только если поменялся сам report_template.docx.
TPL = {
    "lab_no": "1",
    "page_title": "СТЕГАНОГРАФИЯ",
    "dept": "Кафедра Информатики",
    "discipline": "Методы и средства защиты информации",
    "teacher": "Узбекова Л. Я.",
    "group": "МО-426Б",
    "student": "Воробьев И. С.",
    "header_title": "Стеганография",
}

# Ширины колонок штампа на титуле (значения из шаблона -> нужные).
# «Группа» расширена, «Фамилия И.О.» сужена: иначе КАИД-104М переносится
# и титул уезжает на вторую страницу.
STAMP_WIDTHS = {1534: 2169, 273: 283, 2603: 1958, 2757: 3402}

# Пустые колонтитулы для отчётов без ГОСТ-рамки: рамка и штамп живут в
# шапке шаблона, поэтому при frame=False шапки заменяются на пустые, а номер
# страницы переносится в нижний колонтитул.
BLANK_HDR = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<w:p/></w:hdr>'
)

PAGE_FTR = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<w:p><w:pPr><w:jc w:val="center"/>'
    '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>'
    '<w:sz w:val="24"/></w:rPr></w:pPr>'
    '<w:fldSimple w:instr=" PAGE "><w:r><w:rPr>'
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>'
    '<w:sz w:val="24"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple></w:p></w:ftr>'
)



@dataclass
class ReportMeta:
    """Данные, которые подставляются в титульный лист и в шапку."""
    lab_no: str = "1"
    page_title: str = ""            # тема на титуле (как в шаблоне, капсом)
    full_title: str = ""            # тема в штампе колонтитула (кратко)
    frame_title: str = ""           # тема в рамке штампа (если короче full_title)
    frame_teacher: str = ""         # ФИО в штампе рамки (кратко, без пробела)
    dept: str = TPL["dept"]
    discipline: str = TPL["discipline"]
    teacher: str = TPL["teacher"]
    group: str = TPL["group"]
    student: str = TPL["student"]
    frame: bool = True              # ГОСТ-рамка со штампом в колонтитулах
    out_name: str = "report.docx"
    template: str = TEMPLATE
    out_dir: str = OUT_DIR
    stamp_widths: dict = field(default_factory=lambda: dict(STAMP_WIDTHS))

    @property
    def out_path(self):
        return os.path.join(self.out_dir, self.out_name)


# ---------------------------------------------------------------------------
# Работа с XML: замена текста сквозь runs
# ---------------------------------------------------------------------------
def para_text(p):
    return "".join(t.text or "" for t in p.iter(qn("w:t")))


def replace_across_runs(p, old, new):
    """Заменяет ``old`` на ``new`` внутри абзаца, даже если old разбит на runs.

    Возвращает число замен.
    """
    if not old or old == new:
        return 0
    ts = list(p.iter(qn("w:t")))
    if not ts:
        return 0
    count = 0
    while True:
        texts = [t.text or "" for t in ts]
        full = "".join(texts)
        i = full.find(old)
        if i < 0:
            break
        j = i + len(old)
        new_texts = list(texts)
        first = True
        pos = 0
        for k, tx in enumerate(texts):
            start, end = pos, pos + len(tx)
            pos = end
            if end <= i or start >= j:
                continue
            lo = max(i, start) - start
            hi = min(j, end) - start
            if first:
                new_texts[k] = tx[:lo] + new + tx[hi:]
                first = False
            else:
                new_texts[k] = tx[:lo] + tx[hi:]
        for t, txt in zip(ts, new_texts):
            if (t.text or "") != txt:
                t.text = txt
                t.set(XML_SPACE, "preserve")
        count += 1
        if old in new:      # защита от зацикливания
            break
    return count


def find_para(doc, marker):
    for p in doc.element.body.iter(qn("w:p")):
        if marker in para_text(p):
            return p
    return None


def find_table(doc, *markers):
    for tbl in doc.element.body.iter(qn("w:tbl")):
        txt = "".join(t.text or "" for t in tbl.iter(qn("w:t")))
        if all(m in txt for m in markers):
            return tbl
    return None


def _has_visual(p):
    """Есть ли в абзаце картинка или разрыв (такие пустые абзацы не режем)."""
    for tag in ("w:drawing", "w:pict", "w:br"):
        if p.find(".//" + qn(tag)) is not None:
            return True
    return False


# ---------------------------------------------------------------------------
# Отчёт
# ---------------------------------------------------------------------------
class Report:
    def __init__(self, meta, template=None):
        self.meta = meta
        self.doc = Document(template or meta.template)

    # ---------------- титул ----------------
    def prepare(self):
        """Убирает наполнение шаблона и правит титул."""
        self._clear_content()
        self._enable_h3_numbering()
        self._patch_title_page()
        self._compact_title()
        return self

    def _clear_content(self):
        body = self.doc.element.body
        kids = list(body)
        # 0..22 - титул и содержание (sdt), далее наполнение; последний - sectPr
        for child in kids[23:len(kids) - 1]:
            body.remove(child)

    def _patch_title_page(self):
        m, doc = self.meta, self.doc

        p = find_para(doc, TPL["dept"])
        if p is not None:
            replace_across_runs(p, TPL["dept"], m.dept)

        p = find_para(doc, "Лабораторная работа")
        if p is not None and m.lab_no:
            replace_across_runs(p, "№" + TPL["lab_no"], "№" + m.lab_no)

        tbl = find_table(doc, "Лабораторная работа")
        if tbl is not None and m.page_title:
            paras = [x for x in tbl.iter(qn("w:p")) if para_text(x).strip()]
            for p in paras:
                if TPL["page_title"] in para_text(p):
                    replace_across_runs(p, TPL["page_title"], m.page_title)

        p = find_para(doc, TPL["discipline"])
        if p is not None:
            replace_across_runs(p, TPL["discipline"], m.discipline)
            self._fit_discipline(p, m.discipline)

        tbl = find_table(doc, "Группа", "Оценка")
        if tbl is not None:
            subs = []
            if m.group:
                subs.append((TPL["group"], m.group))
            if m.student:
                subs.append((TPL["student"], " " + m.student))
            if m.teacher:
                subs.append((TPL["teacher"], " " + m.teacher))
            for p in tbl.iter(qn("w:p")):
                for old, new in subs:
                    if replace_across_runs(p, old, new) and len(new.strip()) > 15:
                        self._fit_title_cell(p, old, new)
            self._fix_stamp_widths(tbl)

    def _fit_discipline(self, paragraph, text):
        """Уменьшает кегль длинной дисциплины, чтобы она не лезла на рамку.

        В шаблоне дисциплина набрана 14 pt полужирным в узкой ячейке; при
        длинном названии (больше 30 символов) строка наезжает на линию
        подчёркивания. Кегль приводится к 12 pt, тогда текст ложится в две
        строки.
        """
        if len(text) <= 30:
            return
        for run in paragraph.findall(qn("w:r")):
            rpr = run.find(qn("w:rPr"))
            if rpr is None:
                continue
            sz = rpr.find(qn("w:sz"))
            if sz is not None and sz.get(qn("w:val")) == "28":
                sz.set(qn("w:val"), "24")

    def _fit_title_cell(self, paragraph, old, new):
        """Уменьшает кегль ФИО на титуле, чтобы оно не переносилось.

        Колонка «Фамилия И.О.» узкая: длинная фамилия с инициалами
        («Абдрахманова Р. П.») при 12 pt вылезает за границу ячейки.
        """
        from docx.text.paragraph import Paragraph
        size = max(9.0, 12.0 * len(old) / max(len(new), 1))
        par = Paragraph(paragraph, self.doc._body)
        for run in par.runs:
            run.font.size = Pt(size)

    def _fix_stamp_widths(self, tbl):
        mapping = self.meta.stamp_widths or {}
        grid = tbl.find(qn("w:tblGrid"))
        if grid is not None:
            for gc in grid.findall(qn("w:gridCol")):
                try:
                    w = int(gc.get(qn("w:w")))
                except (TypeError, ValueError):
                    continue
                if w in mapping:
                    gc.set(qn("w:w"), str(mapping[w]))
        for tw in tbl.iter(qn("w:tcW")):
            try:
                w = int(tw.get(qn("w:w")))
            except (TypeError, ValueError):
                continue
            if w in mapping:
                tw.set(qn("w:w"), str(mapping[w]))

    def _compact_title(self):
        """Сжимает титул до одной страницы: режет пустые абзацы у штампа."""
        body = self.doc.element.body
        kids = list(body)
        i_stamp = next((i for i, ch in enumerate(kids)
                        if ch.tag == qn("w:tbl")
                        and "Оценка" in "".join(t.text or "" for t in ch.iter(qn("w:t")))),
                       None)
        if i_stamp is None:
            return
        i_toc = next((i for i in range(i_stamp + 1, len(kids))
                      if kids[i].tag == qn("w:sdt")), len(kids))
        for ch in kids[i_stamp + 1:i_toc]:
            if ch.tag == qn("w:p") and not para_text(ch).strip() and not _has_visual(ch):
                body.remove(ch)

    # ---------------- наполнение ----------------
    def h1(self, text, page_break=True):
        par = self.doc.add_heading(text, level=1)
        if not page_break:
            par.paragraph_format.page_break_before = False
        return par

    def h2(self, text):
        self.doc.add_heading(text, level=2)

    def h3(self, text):
        self.doc.add_heading(text, level=3)

    def _enable_h3_numbering(self):
        """Приводит «Heading 3» к виду второго уровня и нумерует его.

        В шаблоне третий уровень заголовков не пронумерован и оформлен
        иначе (синий, 12 пт, без полужирного). Копируем оформление второго
        уровня и подключаем тот же список с ilvl = 2, чтобы подразделы
        получали номера вида 2.2.1.
        """
        styles = self.doc.styles
        try:
            st2, st3 = styles["Heading 2"], styles["Heading 3"]
        except KeyError:
            return
        pPr2 = st2.element.find(qn("w:pPr"))
        numPr = pPr2.find(qn("w:numPr")) if pPr2 is not None else None
        if numPr is None:
            return
        new = copy.deepcopy(numPr)
        ilvl = new.find(qn("w:ilvl"))
        if ilvl is not None:
            ilvl.set(qn("w:val"), "2")

        old_ppr = st3.element.find(qn("w:pPr"))
        if old_ppr is not None:
            st3.element.remove(old_ppr)
        pPr3 = copy.deepcopy(pPr2)
        keep = pPr3.find(qn("w:numPr"))
        if keep is not None:
            pPr3.remove(keep)
        pPr3.append(new)
        st3.element.append(pPr3)

        old_rpr = st3.element.find(qn("w:rPr"))
        if old_rpr is not None:
            st3.element.remove(old_rpr)
        rPr2 = st2.element.find(qn("w:rPr"))
        if rPr2 is not None:
            st3.element.append(copy.deepcopy(rPr2))

    def p(self, text, first_line_indent=True, keep_with_next=False):
        par = self.doc.add_paragraph(style="Основной_ЛР")
        par.add_run(text)
        if keep_with_next:
            par.paragraph_format.keep_with_next = True
        return par

    def bullets(self, items):
        for item in items:
            par = self.doc.add_paragraph(style="Основной_ЛР")
            self._hang(par)
            # неразрывный пробел после маркера не растягивается выключкой
            par.add_run("\u2013\u00a0" + item)

    def numbers(self, items):
        for i, item in enumerate(items, 1):
            par = self.doc.add_paragraph(style="Основной_ЛР")
            self._hang(par)
            par.add_run("%d)\u00a0" % i + item)

    @staticmethod
    def _hang(par, indent_cm=1.25, hang_cm=0.7):
        """Висячий отступ для списков: переносы выравниваются по тексту."""
        pf = par.paragraph_format
        pf.left_indent = Cm(indent_cm)
        pf.first_line_indent = Cm(-hang_cm)

    def spacer(self, pt=10):
        """Пустой абзац-отбивка заданной высоты."""
        par = self.doc.add_paragraph()
        pf = par.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing = Pt(pt)
        run = par.add_run("")
        run.font.size = Pt(2)
        return par

    def table(self, headers, rows, widths, caption=None, size=11, note=None,
              keep_together=False):
        """Таблица по ГОСТ: подпись сверху, шапка жирным, ширины в см.

        ``keep_together`` переносит таблицу на следующую страницу целиком,
        если она не влезает: без этого от таблицы остаётся одна-две строки,
        а на предыдущей странице появляется пустое место.
        """
        if caption:
            cp = self.doc.add_paragraph()
            cp.paragraph_format.space_before = Pt(12)
            cp.paragraph_format.space_after = Pt(6)
            cp.paragraph_format.first_line_indent = Cm(0)
            cp.paragraph_format.keep_with_next = True
            cr = cp.add_run(caption)
            cr.font.name = TNR
            cr.font.size = Pt(12)
        tbl = self.doc.add_table(rows=1, cols=len(headers))
        tbl.style = "Table Grid"
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, head in enumerate(headers):
            self._set_cell(tbl.rows[0].cells[i], head, size, bold=True,
                           align=WD_ALIGN_PARAGRAPH.CENTER)
        self._header_row(tbl.rows[0])
        for row in rows:
            cells = tbl.add_row().cells
            for i, val in enumerate(row):
                self._set_cell(cells[i], str(val), size)
        for row in tbl.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
        if keep_together:
            for row in tbl.rows[:-1]:
                for cell in row.cells:
                    for par in cell.paragraphs:
                        par.paragraph_format.keep_with_next = True
        if note:
            np_ = self.doc.add_paragraph()
            nr = np_.add_run(note)
            nr.font.name = TNR
            nr.font.size = Pt(11)
        self.spacer(10)
        return tbl

    @staticmethod
    def _header_row(row):
        """Шапка повторяется на каждой странице, строки не разрываются."""
        trPr = row._tr.get_or_add_trPr()
        for tag in ("w:tblHeader", "w:cantSplit"):
            el = trPr.makeelement(qn(tag), {})
            trPr.append(el)

    @staticmethod
    def _set_cell(cell, text, size=12, bold=False, align=None):
        cell.text = ""
        par = cell.paragraphs[0]
        if align is not None:
            par.alignment = align
        run = par.add_run(text)
        run.font.name = TNR
        run.font.size = Pt(size)
        run.bold = bold

    def figure(self, image, caption, width_cm=17.0):
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.first_line_indent = Cm(0)
        par.paragraph_format.space_before = Pt(10)
        par.paragraph_format.space_after = Pt(2)
        par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(image, width=Cm(width_cm))
        cap = self.doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.first_line_indent = Cm(0)
        cap.paragraph_format.space_after = Pt(12)
        run = cap.add_run(caption)
        run.font.name = TNR
        run.font.size = Pt(12)

    def formula(self, text, size=12):
        """Формула отдельной строкой: по центру, без отступа, курсивом.

        Абзац с формулой не выключается по ширине: иначе короткая строка
        растягивается пробелами до полной ширины страницы.
        """
        par = self.doc.add_paragraph()
        pf = par.paragraph_format
        pf.first_line_indent = Cm(0)
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.space_before = Pt(6)
        pf.space_after = Pt(6)
        run = par.add_run(text)
        run.font.name = TNR
        run.font.size = Pt(size)
        run.italic = True

    def formula_block(self, lines, size=10, indent_cm=1.2):
        """Блок формул: строки без отступа первой строки, курсивом.

        Нужен для многострочных кусочно-заданных записей и длинных сумм.
        """
        lines = list(lines)
        for i, line in enumerate(lines):
            par = self.doc.add_paragraph()
            pf = par.paragraph_format
            pf.first_line_indent = Cm(0)
            pf.left_indent = Cm(indent_cm)
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.space_before = Pt(2 if i == 0 else 0)
            pf.space_after = Pt(2 if i == len(lines) - 1 else 0)
            pf.line_spacing = 1.0
            pf.keep_with_next = i < len(lines) - 1
            run = par.add_run(line)
            run.font.name = TNR
            run.font.size = Pt(size)
            run.italic = True

    def code(self, text, size=9.5, indent_cm=0.6):
        """Листинг: монотипный шрифт, без отступа первой строки.

        Строки листинга склеиваются абзацами с ``keep_with_next``, чтобы
        фрагмент не разрывался между страницами.
        """
        lines = text.strip("\n").split("\n")
        for i, line in enumerate(lines):
            par = self.doc.add_paragraph()
            pf = par.paragraph_format
            pf.first_line_indent = Cm(0)
            pf.left_indent = Cm(indent_cm)
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.space_before = Pt(0)
            pf.space_after = Pt(0)
            pf.line_spacing = 1.0
            pf.keep_with_next = i < len(lines) - 1
            run = par.add_run(line if line.strip() else " ")
            run.font.name = "Courier New"
            run.font.size = Pt(size)
        self.spacer(10)

    def listing(self, text, caption=None, size=9):
        """Листинг программы: подпись сверху, монотипный шрифт."""
        if caption:
            cp = self.doc.add_paragraph()
            pf = cp.paragraph_format
            pf.first_line_indent = Cm(0)
            pf.space_before = Pt(10)
            pf.space_after = Pt(3)
            pf.keep_with_next = True
            cr = cp.add_run(caption)
            cr.font.name = TNR
            cr.font.size = Pt(11)
        self.code(text, size=size)

    # ---------------- сохранение ----------------
    def save(self):
        out = self.meta.out_path
        os.makedirs(os.path.dirname(out), exist_ok=True)
        self.doc.save(out)
        self._patch_package(out)
        compact_package(out)
        return out

    def _patch_package(self, path):
        """Правит header1.xml (тема, преподаватель, группа) и updateFields."""
        m = self.meta
        tmp = path + ".tmp"
        zin = zipfile.ZipFile(path)
        zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
        for item in zin.infolist():
            data = zin.read(item.filename)
            if not m.frame and item.filename in ("word/header1.xml",
                                                 "word/header2.xml"):
                data = BLANK_HDR.encode("utf-8")
            elif not m.frame and item.filename == "word/footer1.xml":
                data = PAGE_FTR.encode("utf-8")
            elif item.filename == "word/header1.xml":
                s = data.decode("utf-8")
                if m.lab_no and m.lab_no != TPL["lab_no"]:
                    s = s.replace("работа №" + TPL["lab_no"],
                                  "работа №" + m.lab_no)
                title = m.frame_title or m.full_title
                if title:
                    s = _fit_frame_title(s, TPL["header_title"], title)
                if m.teacher:
                    s = _fit_frame_text(s, TPL["teacher"],
                                        m.frame_teacher or m.teacher)
                if m.group:
                    s = _fit_frame_group(s, TPL["group"], m.group)
                data = s.encode("utf-8")
            elif item.filename == "word/numbering.xml":
                s = data.decode("utf-8")
                # Двузначные номера разделов («11») прижимаются к заголовку:
                # табуляция стоит слишком близко к краю номера.
                s = s.replace('<w:tab w:val="num" w:pos="717"/>',
                              '<w:tab w:val="num" w:pos="920"/>', 1)
                # Третий уровень заголовков в шаблоне идёт с точкой на
                # конце («2.2.1.»); убираем её, чтобы нумерация была
                # единообразной.
                s = s.replace('<w:lvlText w:val="%1.%2.%3."/>',
                              '<w:lvlText w:val="%1.%2.%3"/>', 1)
                s = s.replace(
                    '<w:ind w:left="720" w:hanging="360"/></w:pPr>'
                    '<w:rPr><w:rFonts w:hint="default"/></w:rPr></w:lvl>',
                    '<w:ind w:left="920" w:hanging="560"/></w:pPr>'
                    '<w:rPr><w:rFonts w:hint="default"/></w:rPr></w:lvl>', 1)
                data = s.encode("utf-8")
            elif item.filename == "word/settings.xml":
                s = data.decode("utf-8")
                if "<w:updateFields" not in s:
                    ins = '<w:updateFields w:val="true"/>'
                    idx = s.find("<w:hdrShapeDefaults")
                    if idx >= 0:
                        s = s[:idx] + ins + s[idx:]
                    else:
                        s = s.replace("</w:settings>", ins + "</w:settings>", 1)
                data = s.encode("utf-8")
            zout.writestr(item, data)
        zout.close()
        zin.close()
        os.replace(tmp, path)


def _rels_owner(rels_name):
    """Путь части, которой принадлежит файл связей.

    ``word/_rels/document.xml.rels`` -> ``word/document.xml``.
    """
    folder, base = posixpath.split(rels_name)
    if not folder.endswith("_rels"):
        return None
    owner_dir = posixpath.dirname(folder)
    return posixpath.join(owner_dir, base[:-len(".rels")])


_REL = re.compile(r"<Relationship\b[^>]*/>")
_ATTR = re.compile(r'([\w:]+)="([^"]*)"')


def compact_package(path):
    """Выкидывает из DOCX картинки, на которые уже никто не ссылается.

    Шаблон кафедры приходит вместе с демонстрационным наполнением (скриншоты
    примера отчёта). ``Report.prepare()`` вырезает это наполнение из
    ``document.xml``, но сами файлы остаются в пакете: в готовом отчёте
    3.4 МБ из 4.5 - мусор. Функция удаляет связи ``media/*`` без ссылок в
    XML-владельце, а затем и сами файлы без оставшихся связей.

    Возвращает число удалённых частей пакета.
    """
    zin = zipfile.ZipFile(path)
    infos = zin.infolist()
    parts = {i.filename: zin.read(i.filename) for i in infos}
    zin.close()

    dropped = 0
    for rels_name in [n for n in parts if n.endswith(".rels")]:
        owner = _rels_owner(rels_name)
        if owner not in parts:
            continue
        owner_xml = parts[owner].decode("utf-8")

        def keep(match, owner_xml=owner_xml):
            attrs = dict(_ATTR.findall(match.group(0)))
            target = attrs.get("Target", "")
            if attrs.get("TargetMode") == "External" or "media/" not in target:
                return match.group(0)
            if '"%s"' % attrs.get("Id") in owner_xml:
                return match.group(0)
            return ""

        rels = parts[rels_name].decode("utf-8")
        new_rels = _REL.sub(keep, rels)
        if new_rels != rels:
            parts[rels_name] = new_rels.encode("utf-8")

    # что осталось нужным после чистки связей
    used = set()
    for rels_name, data in parts.items():
        if not rels_name.endswith(".rels"):
            continue
        owner = _rels_owner(rels_name)
        if owner is None:
            continue
        base = posixpath.dirname(owner)
        for target in re.findall(r'Target="([^"]*media/[^"]*)"',
                                 data.decode("utf-8")):
            used.add(posixpath.normpath(posixpath.join(base, target)))

    media = [n for n in parts
             if "/media/" in n and posixpath.normpath(n) not in used]
    for name in media:
        del parts[name]
        dropped += 1

    if dropped:
        tmp = path + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in infos:
                if item.filename in parts:
                    zout.writestr(item, parts[item.filename])
        os.replace(tmp, path)
    return dropped


def _para_chunks(xml):
    """Делит XML на куски по абзацам: (фрагмент, текст абзаца)."""
    parts = re.split(r"(<w:p\b.*?</w:p>)", xml, flags=re.S)
    out = []
    for chunk in parts:
        if chunk.startswith("<w:p"):
            ts = re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", chunk, re.S)
            out.append((chunk, "".join(ts)))
        else:
            out.append((chunk, None))
    return out


def _scale_sizes(chunk, ratio, minimum=10):
    """Уменьшает кегль в абзаце (w:sz задан в полупунктах)."""

    def sub(m):
        val = int(m.group(2))
        new = max(minimum, int(round(val * ratio)))
        return m.group(1) + str(new) + m.group(3)

    return re.sub(r"(<w:sz(?:Cs)? w:val=\")(\d+)(\")", sub, chunk)


def _fit_frame_title(xml, old, new):
    """Меняет тему в штампе рамки, уменьшая кегль длинного названия."""
    out = []
    for chunk, txt in _para_chunks(xml):
        if txt is not None and old in txt:
            ratio = min(1.0, (len(old) + 8.0) / max(len(new), 1))
            if ratio < 1.0:
                chunk = _scale_sizes(chunk, ratio, minimum=13)
            chunk = chunk.replace(old, new)
        out.append(chunk)
    return "".join(out)


def _fit_frame_text(xml, old, new):
    """Меняет текст в штампе, подгоняя кегль, если новое значение длиннее.

    Поля штампа (Пров., Рецен., Утв.) узкие и разной ширины, поэтому
    кегль уменьшается с запасом: иначе ФИО переносится и вылезает за рамку.
    """
    out = []
    for chunk, txt in _para_chunks(xml):
        if txt is not None and old in txt:
            ratio = min(1.0, float(len(old)) / max(len(new), 1)) * 0.85
            if ratio < 1.0:
                chunk = _scale_sizes(chunk, ratio, minimum=12)
            chunk = chunk.replace(old, new)
        out.append(chunk)
    return "".join(out)


def _fit_frame_group(xml, old, new):
    """Меняет группу в штампе, подгоняя кегль под ширину поля."""
    out = []
    for chunk, txt in _para_chunks(xml):
        if txt is not None and old in txt:
            ratio = min(1.0, float(len(old)) / max(len(new), 1))
            if ratio < 1.0:
                chunk = _scale_sizes(chunk, ratio, minimum=12)
            chunk = _replace_group_runs(chunk, old, new)
        out.append(chunk)
    return "".join(out)


def _replace_group_runs(xml, old, new):
    """Замена группы в header1.xml, где текст разбит на несколько w:t.

    Делает то же, что :func:`replace_across_runs`, но на уровне XML-строки:
    внутри одного w:p собирает w:t, находит old, раскладывает new.
    Разбиение по абзацам сохраняется.
    """
    parts = re.split(r"(</w:p>)", xml)
    out = []
    for chunk in parts:
        if not chunk.startswith("<w:p") and "<w:t" not in chunk:
            out.append(chunk)
            continue
        ts = list(re.finditer(r"(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)", chunk, re.S))
        if not ts:
            out.append(chunk)
            continue
        texts = [t.group(2) for t in ts]
        full = "".join(texts)
        if old not in full:
            out.append(chunk)
            continue
        i = full.find(old)
        j = i + len(old)
        new_texts = list(texts)
        first = True
        pos = 0
        for k, tx in enumerate(texts):
            start, end = pos, pos + len(tx)
            pos = end
            if end <= i or start >= j:
                continue
            lo = max(i, start) - start
            hi = min(j, end) - start
            if first:
                new_texts[k] = tx[:lo] + new + tx[hi:]
                first = False
            else:
                new_texts[k] = tx[:lo] + tx[hi:]
        pieces, last = [], 0
        for t, txt in zip(ts, new_texts):
            pieces.append(chunk[last:t.start(2)])
            pieces.append(txt)
            last = t.end(2)
        pieces.append(chunk[last:])
        out.append("".join(pieces))
    return "".join(out)
