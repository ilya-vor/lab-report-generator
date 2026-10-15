# Новая лабораторная

1. Скопируйте папку репозитория (например, в `lab2`).
2. В `generate_scheme.py` отредактируйте `LANES`, `NODES`, `FLOWS`,
   `PROBLEM_STYLE` и геометрию при необходимости. Запуск: `python generate_scheme.py`.
3. В `build_report_docx.py` блок `НАСТРОЙКИ`: `FULL_TITLE`, `SHORT_TITLE`,
   `DEPT`, `DISCIPLINE`, `TEACHER`, `GROUP`, `OLD_*`, `OUT`, `IMG`.
   Текст отчёта правится в `build_content(doc)`.
4. Сборка:
   ```
   python build_report_docx.py
   powershell -NoProfile -ExecutionPolicy Bypass -File update_fields.ps1 -Path "ваш_отчет.docx"
   ```
5. Опционально правка в Camunda: правите `.bpmn`, `File -> Export As -> PNG`
   поверх `IMG`, пересобираете отчёт.

## Чек-лист

- [ ] Есть начальное/конечное события, узлы по дорожкам, исключения через XOR,
      покрытие >= 80 %.
- [ ] Есть минимум 3 проблемные точки с обоснованием.
- [ ] Титул на одной странице (группа не переносится).
- [ ] Оглавление обновлено.
- [ ] Нет длинных тире.
