# Конвейер

```
generate_scheme.py   ->  .bpmn / .png / .svg
build_report_docx.py ->  .docx (титул и рамка из report_template.docx)
update_fields.ps1    ->  обновление полей и TOC в Word
```

## generate_scheme.py

Единый источник данных:

- `LANES` - дорожки;
- `NODES` - `(id, type, name, lane, col, offset)`, type = `task|xor|start|end|timer`;
- `FLOWS` - `(id, source, target, label, cond)`;
- `PROBLEM_STYLE` - подсветка проблемных зон.

Из них строятся BPMN-XML (`generate_bpmn`) и картинка matplotlib (`draw_diagram`).

Важное:
- Ось Y в BPMN направлена вниз, в matplotlib вверх -> координаты BPMN
  зеркалятся (`flip_y`), иначе дорожки идут наоборот.
- Цвета проблемных зон переносятся в BPMN через `bioc:fill`/`bioc:stroke`.

## build_report_docx.py

- Надёжнее клонировать шаблон, чем строить с нуля (специфичные титул/рамка/стили).
- Порядок: `clear_content` -> `patch_title_page` -> `build_content`
  (иначе сдвиг индексов узлов титула и дублирование).
- Титул: `kids[1]` институт, `kids[6]` тема, `kids[11]` дисциплина, `kids[16]` штамп.
- Настройки в блоке `НАСТРОЙКИ`: `FULL_TITLE`, `SHORT_TITLE`, `DEPT`,
  `DISCIPLINE`, `TEACHER`, `GROUP`, `OLD_*`, `OUT`, `IMG`.

## update_fields.ps1

Word (COM) обновляет `Fields` и `TablesOfContents` и сохраняет файл.
