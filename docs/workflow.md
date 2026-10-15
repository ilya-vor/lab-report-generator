# Как устроен конвейер

## Общая схема

```
generate_scheme.py  ──►  As-Is_*.bpmn / .png / .svg
                                │
                                ▼
build_report_docx.py ──►  отчёт .docx  (титул и рамка из report_template.docx)
                                │
                                ▼
update_fields.ps1   ──►  обновление полей и оглавления (TOC) в Word
```

## generate_scheme.py

Единый источник данных:

- `LANES` - дорожки (роли / подразделения);
- `NODES` - узлы, формат `(id, type, name, lane, col, offset)`;
  `type` из `task | xor | start | end | timer`;
- `FLOWS` - потоки, формат `(id, source, target, label, is_conditional)`;
- `PROBLEM_STYLE` - цвет проблемной зоны для подсветки.

Из этих структур строятся:

1. **BPMN 2.0 XML** (`generate_bpmn`): `collaboration` + `participant`,
   `process` с `laneSet`, узлы, `sequenceFlow` с `conditionExpression`,
   и раздел `BPMNDiagram` / `BPMNPlane` с координатами (`dc:Bounds`,
   `di:waypoint`).
2. **Картинка** (`draw_diagram`): matplotlib - дорожки, скруглённые блоки,
   ромбы-шлюзы, круги событий, легенда.

### Важно про координаты

В BPMN ось Y направлена **вниз**, а в matplotlib - **вверх**. Поэтому при
выгрузке BPMN координаты зеркалятся по вертикали функцией `flip_y`, иначе
в Camunda дорожки идут в обратном порядке.

### Цвета проблемных зон

В BPMN переносятся через атрибуты `bioc:fill` / `bioc:stroke`
(namespace `http://bpmn.io/schema/bpmn/biocolor/1.0`) на `bpmndi:BPMNShape`.
Camunda Modeler их понимает и отображает.

## build_report_docx.py

### Почему клонирование, а не создание с нуля

Штамп-рамка, титул из таблиц и стили в шаблоне кафедры очень специфичны.
Надёжнее открыть шаблон через `python-docx` и заменить только нужное.

### Порядок операций (критично)

```
clear_content(doc)      # удалить старое наполнение, оставить титул и sectPr
patch_title_page(doc)   # подменить реквизиты на титуле
build_content(doc)      # добавить текст, таблицы, рисунок
```

Если поменять порядок, удаление пустых абзацев сдвинет индексы узлов титула,
и наполнение продублируется.

### Что подменяется на титуле

Индексы берутся из шаблона (см. `patch_title_page`):

- `kids[1]` - институт / кафедра;
- `kids[6]` - тема работы;
- `kids[11]` - дисциплина;
- `kids[16]` - штамп (группа, ФИО, преподаватель).

### Настройки

Все реквизиты находятся в блоке `НАСТРОЙКИ` в начале файла:
`FULL_TITLE`, `SHORT_TITLE`, `DEPT`, `DISCIPLINE`, `TEACHER`, `GROUP`
и соответствующие «старые» значения для замены (`OLD_*`).

## update_fields.ps1

Word обновляет TOC и поля. Скрипт открывает документ через COM, обновляет
`Fields` и `TablesOfContents`, сохраняет. Без этого в содержании могут
оставаться устаревшие номера страниц.
