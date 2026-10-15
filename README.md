# lab-report-generator

Тулкit для оформления отчётов по лабораторным работам: построение схемы
бизнес-процесса (BPMN 2.0) и автоматическая сборка пояснительной записки
в DOCX строго по шаблону кафедры.

Идея: типовая часть отчёта (титульный лист, рамка-штамп, стили, автосодержание)
берётся из шаблона `report_template.docx` **без изменения структуры**, а меняется
только предметное наполнение (тема, текст, таблицы, рисунок).

## Возможности

| Файл | Назначение |
|------|-----------|
| `generate_scheme.py` | Строит схему BPMN 2.0 (`.bpmn`) и её визуализацию `.png` / `.svg` (matplotlib). |
| `build_report_docx.py` | Собирает отчёт `.docx`: клонирует титул и колонтитул-рамку из шаблона, добавляет текст, таблицы и рисунок. |
| `update_fields.ps1` | Обновляет поля и оглавление (TOC) через MS Word (COM). |
| `build_all.ps1` | Прогоняет всю цепочку по порядку. |
| `docs/` | Документация: как устроено, как переиспользовать, грабли. |

## Требования

- Windows, Python 3.10+
- Microsoft Word (для `update_fields.ps1`)
- (по желанию) Camunda Modeler - для ручного редактирования `.bpmn`

## Быстрый старт

```powershell
pip install -r requirements.txt

python generate_scheme.py         # -> As-Is_Контроль_СИЗ.bpmn / .png / .svg
python build_report_docx.py       # -> Воробьев_И_С_отчет_по_1_ЛР_As-Is.docx
powershell -NoProfile -ExecutionPolicy Bypass -File update_fields.ps1 `
    -Path "Воробьев_И_С_отчет_по_1_ЛР_As-Is.docx"
```

Или одной командой:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build_all.ps1
```

## Структура

```
lab-report-generator/
├── generate_scheme.py        # схема: BPMN + PNG + SVG (единые данные LANES/NODES/FLOWS)
├── build_report_docx.py      # сборка DOCX из шаблона
├── report_template.docx      # шаблон-эталон (титул, рамка, стили, TOC)
├── update_fields.ps1         # обновление полей/TOC в Word
├── build_all.ps1             # вся цепочка
├── requirements.txt
├── docs/
│   ├── workflow.md           # как устроен конвейер
│   ├── next-lab.md           # пошагово для следующей лабораторной
│   └── pitfalls.md           # известные проблемы и решения
├── HISTORY.md                # журнал разработки (история чата)
├── CHANGELOG.md              # версии
├── As-Is_Контроль_СИЗ.bpmn   # результат Lab 1 (редактируется в Camunda)
├── As-Is_Контроль_СИЗ.png    # результат Lab 1 (идёт в отчёт)
├── As-Is_Контроль_СИЗ.svg    # результат Lab 1 (вектор)
├── Лабораторная_работа_1_Отчет.md
└── Воробьев_И_С_отчет_по_1_ЛР_As-Is.docx
```

## Главные правила (кратко)

1. **Титул и рамку не перерисовываем** - они клонируются из `report_template.docx`.
2. **Порядок в `build()`**: `clear_content` -> `patch_title_page` -> `build_content`.
   Иначе сдвигаются индексы узлов титула и наполнение дублируется.
3. **Схема - один источник данных**: правьте `LANES/NODES/FLOWS` в
   `generate_scheme.py`, тогда и BPMN, и картинка согласованы.
4. **Поля/TOC** в DOCX обновляет Word; в headless-режиме это делает `update_fields.ps1`.
5. **Длинные тире** в тексте отчёта заменяются смысловыми связками
   (диапазоны `4-8` и знак минус в формулах - оставляем).

Подробности - в `docs/`.
