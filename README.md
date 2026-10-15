# lab-report-generator

Тулкит для отчётов по лабам: схема BPMN 2.0 (`.bpmn` + `.png`/`.svg`) и сборка
DOCX строго по шаблону кафедры.

Типовая часть (титул, рамка-штамп, стили, содержание) клонируется из
`report_template.docx` без изменения структуры; меняется только наполнение.

## Файлы

| Файл | Назначение |
|------|-----------|
| `generate_scheme.py` | BPMN + PNG/SVG из единых `LANES/NODES/FLOWS`. |
| `build_report_docx.py` | Сборка отчёта из шаблона. |
| `update_fields.ps1` | Обновление полей/TOC через Word. |
| `build_all.ps1` | Вся цепочка сразу. |

## Запуск

```powershell
pip install -r requirements.txt
powershell -NoProfile -ExecutionPolicy Bypass -File build_all.ps1
```

По шагам: `python generate_scheme.py` -> `python build_report_docx.py` ->
`update_fields.ps1 -Path <отчёт>.docx`.

## Правила

1. Титул и рамку не перерисовываем, клонируем из шаблона.
2. В `build()` порядок: `clear_content` -> `patch_title_page` -> `build_content`.
3. Схема: правьте `LANES/NODES/FLOWS` в `generate_scheme.py`.
4. Поля/TOC обновляет Word (`update_fields.ps1`).
5. Без длинных тире; диапазоны (`4-8`) и минус в формулах сохраняем.

Детали: `docs/`. История: `HISTORY.md`.
