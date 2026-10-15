# Changelog

## [1.0.0] - 2026-10-15

### Added
- `generate_scheme.py`: BPMN + PNG/SVG (As-Is контроль СИЗ).
- `build_report_docx.py`: сборка отчёта из шаблона.
- `docs/`, `HISTORY.md`, `README.md`, `update_fields.ps1`, `build_all.ps1`.

### Fixed
- Порядок `clear_content` -> `patch_title_page` -> `build_content`.
- Ширины колонок штампа (перенос длинной группы).
- Замена группы, разбитой на runs, в `header1.xml`.
- Зеркалирование координат BPMN под ось Y Camunda.
- Цвета проблемных зон в BPMN (`bioc:fill`/`bioc:stroke`).
- Убрано имя пула в BPMN.

### Changed
- Схема компактнее; подписи таблиц без курсива.
