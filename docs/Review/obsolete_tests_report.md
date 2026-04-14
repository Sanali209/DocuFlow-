# Отчёт об устаревших тестах

Дата: 2026-04-05  
Анализ на основе: `pytest -v` результатов

## Категории проблем

### 1. Устаревшие сигнатуры конструкторов (27 ERRORS)

#### AdminSystem: изменён конструктор
**Проблема:** Тесты передают `engine=`, но AdminSystem теперь принимает `session=`

**Затронутые файлы:**
- `tests/test_folder_scanner_integration.py` (7 тестов)
- `tests/test_scanner_diagnosis.py` (10 тестов)

**Пример ошибки:**
```python
# Старый код в тестах:
admin = AdminSystem(engine=mock_engine, orchestrator=orchestrator, signer=signer, config=config)

# Должно быть:
admin = AdminSystem(session=session, orchestrator=orchestrator, signer=signer, config=config)
```

**Файлы для исправления:**
1. `tests/test_folder_scanner_integration.py:60` - фикстура `mock_admin_system`
2. `tests/test_scanner_diagnosis.py:79` - фикстура `admin_with_settings`
3. `tests/test_scanner_diagnosis.py:114` - фикстура `admin_without_settings`

---

#### BatchEngine: изменён конструктор
**Проблема:** Тесты создают `BatchEngine()` без аргументов, но теперь требуется `session`

**Затронутые файлы:**
- `tests/unit/features/test_batch_engine.py` (10 тестов)

**Пример ошибки:**
```python
# Старый код:
return BatchEngine()

# Должно быть:
return BatchEngine(session=session)
```

**Файл для исправления:**
- `tests/unit/features/test_batch_engine.py:39` - фикстура `engine_fixture`

---

### 2. Проблемы с NiceGUI контекстом (10 FAILED)

**Проблема:** Тесты виджетов пытаются создать UI элементы вне NiceGUI контекста

**Затронутые файлы:**
- `tests/unit/lib/test_widgets.py` (10 тестов)

**Ошибка:**
```
RuntimeError: The current slot cannot be determined because the slot stack for this task is empty.
This may happen if you try to create UI from a background task.
```

**Решение:** Обернуть тесты в NiceGUI контекст или использовать моки

**Файлы для исправления:**
- `tests/unit/lib/test_widgets.py` - все тесты классов:
  - `TestStatusBadge` (3 теста)
  - `TestExplorerButton` (3 теста)
  - `TestFileChangedAlert` (2 теста)

---

### 3. Проблемы с базой данных (2 FAILED)

#### MaterialStock: NOT NULL constraint
**Проблема:** Тесты не заполняют обязательное поле `mat_type_id`

**Затронутые файлы:**
- `tests/application/test_inventory_system.py` (2 теста)

**Ошибка:**
```
sqlite3.IntegrityError: NOT NULL constraint failed: materialstock.mat_type_id
```

**Файлы для исправления:**
- `tests/application/test_inventory_system.py:38` - `test_material_creation`
- `tests/application/test_inventory_system.py` - `test_absolute_stock_update`

---

### 4. Проблемы с конфигурацией (5 FAILED)

**Проблема:** Тесты ожидают старое поведение переменных окружения

**Затронутые файлы:**
- `tests/test_config.py:test_config_env_override`
- `tests/test_config_intervals.py:test_config_interval_env_override`
- `tests/test_folder_scanner_integration.py:test_get_settings_without_admin`
- `tests/test_inventory_integration.py:test_inventory_settings_registration`
- `tests/test_scanner_diagnosis.py` (5 тестов)

**Причина:** Изменения в `Config` или `AdminSystem` API

---

### 5. Проблемы с качеством кода (1 FAILED)

**Файл:** `tests/test_code_quality.py:test_no_magic_number_4096_for_md5`

**Проблема:** Тест проверяет отсутствие магического числа 4096, но оно используется в коде

**Решение:** Либо вынести 4096 в константу, либо обновить тест

---

### 6. Прочие проблемы (6 FAILED)

1. **test_orchestrator_failure_propagation** - проблема с async/await
2. **test_full_workshop_pipeline** - интеграционный тест требует обновления
3. **test_health_check** - проблема с потоками FastAPI
4. **test_sdk_is_app_scoped_singleton** - проблема с Dishka scope

---

## Приоритеты исправления

### Высокий приоритет (блокируют 37 тестов)
1. ✅ **AdminSystem constructor** - 17 тестов
2. ✅ **BatchEngine constructor** - 10 тестов
3. ✅ **NiceGUI context** - 10 тестов

### Средний приоритет (блокируют 7 тестов)
4. **MaterialStock constraints** - 2 теста
5. **Config/Settings API** - 5 тестов

### Низкий приоритет (блокируют 7 тестов)
6. **Прочие интеграционные тесты** - 7 тестов

---

## Рекомендации

1. **Немедленно исправить:** AdminSystem и BatchEngine конструкторы (27 тестов)
2. **Рефакторинг:** NiceGUI тесты требуют моков или контекста (10 тестов)
3. **Обновить схему:** MaterialStock требует mat_type_id (2 теста)
4. **Синхронизировать:** Config API изменился (5 тестов)
5. **Проверить:** Интеграционные тесты требуют обновления (7 тестов)

---

## Статистика

- **Всего тестов:** 221
- **Проходят:** 170 (77%)
- **Падают:** 24 (11%)
- **Ошибки:** 27 (12%)
- **Пропущены:** 6

**Устаревшие тесты:** 51 (23%)