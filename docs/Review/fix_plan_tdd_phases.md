# План исправлений DocuFlow — TDD-подход с фазами и тикетами

Дата: 2026-04-05
Составил: Cline

Принципы:
- Test-Driven Development: каждое изменение проверяется тестами
- Атомарные тикеты: один тикет = одна проблема = один коммит
- Фазовые врата: переход к следующей фазе только после прохождения критериев
- Отслеживание прогресса: чек-листы для каждого тикета

---

## ФАЗА 0: Подготовка окружения (БЛОКИРУЮЩАЯ) ✅ ЗАВЕРШЕНА

**Цель:** Сделать проект импортируемым и настроить базовую инфраструктуру для TDD.

**Врата прохождения:**
- ✅ Пакет docuflow импортируется: `python -c "import docuflow"`
- ✅ pytest собирает тесты без ModuleNotFoundError
- ✅ ruff запускается и выдаёт список ошибок
- ✅ .gitignore обновлён, runtime-артефакты удалены из индекса

### Тикет 0.1: Добавить build-system в pyproject.toml ✅ ВЫПОЛНЕН
**Приоритет:** CRITICAL
**Оценка:** 15 мин
**Фактически:** 15 мин
**Коммит:** efde4c8

**Описание:**
Добавить секцию [build-system] для установки пакета в editable-режиме.

**Изменения:**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Тест:**
```bash
python -m pip install -e .
python -c "import docuflow; print(docuflow.__file__)"
```

**Критерий успеха:**
- Команда импорта выполняется без ошибок
- Выводится путь к установленному пакету

**Коммит:** `fix: add build-system to pyproject.toml for editable install`

---

### Тикет 0.2: Обновить .gitignore ✅ ВЫПОЛНЕН
**Приоритет:** HIGH
**Оценка:** 10 мин
**Фактически:** 10 мин
**Коммит:** d038af7

**Описание:**
Добавить правила игнорирования runtime-артефактов.

**Изменения в .gitignore:**
```
# Runtime artifacts
*.db
*.db-shm
*.db-wal
*.env
!.env.template
shared_network/
reproduce_issue.py
```

**Тест:**
```bash
git status
# Проверить, что новые .db/.env файлы не отображаются
```

**Критерий успеха:**
- git status не показывает игнорируемые файлы

**Коммит:** `chore: update .gitignore to exclude runtime artifacts`

---

### Тикет 0.3: Удалить runtime-артефакты из git-индекса ✅ ВЫПОЛНЕН
**Приоритет:** HIGH
**Оценка:** 15 мин
**Фактически:** 15 мин
**Коммит:** 5521780

**Описание:**
Удалить закоммиченные .db, .env, shared_network из репозитория (сохранить локально).

**Команды:**
```bash
git rm --cached *.db *.env src/docuflow/node_01.db
git rm -r --cached shared_network/
git status
```

**Тест:**
```bash
git status
# Проверить, что файлы помечены как deleted в индексе
ls -la *.db
# Проверить, что файлы остались локально
```

**Критерий успеха:**
- Файлы удалены из индекса git
- Файлы остались в рабочей директории

**Коммит:** `chore: remove runtime artifacts from git index`

---

### Тикет 0.4: Установить пакет и запустить базовую диагностику ✅ ВЫПОЛНЕН
**Приоритет:** HIGH
**Оценка:** 20 мин
**Фактически:** 20 мин
**Коммит:** 837d45e

**Описание:**
Установить пакет в editable-режиме и получить baseline метрик.

**Команды:**
```bash
python -m pip install -e .
uv run ruff check src/ --statistics > baseline_ruff.txt
uv run pytest --collect-only -q > baseline_pytest.txt 2>&1
```

**Тест:**
Проверить содержимое baseline файлов.

**Критерий успеха:**
- pytest собирает тесты (может быть с ошибками, но не ModuleNotFoundError)
- ruff выдаёт список ошибок с статистикой
- Baseline файлы сохранены для сравнения

**Коммит:** `chore: install package and capture baseline metrics`

---

## ФАЗА 1: Критические runtime-ошибки (F821) ✅ ЗАВЕРШЕНА

**Цель:** Устранить undefined-name ошибки, которые ломают выполнение кода.

**Врата прохождения:**
- ✅ Все F821 ошибки устранены (ruff check src/ --select F821 выдаёт 0)
- ✅ Импорты logger работают во всех модулях
- ✅ TYPE_CHECKING блоки корректны
- ✅ pytest собирает все тесты без ImportError

**Дата завершения:** 05.04.2026
**Коммиты:** d33564b, bd72298, 7af98a1, ac50e62

### Тикет 1.1: Исправить импорты logger в task_board/system.py ✅ ВЫПОЛНЕН
**Приоритет:** CRITICAL
**Оценка:** 10 мин
**Фактически:** 10 мин
**Коммит:** d33564b

**Описание:**
Добавить импорт logger в модуль, где он используется.

**Изменения:**
```python
# В начало файла src/docuflow/features/task_board/system.py
from loguru import logger
```

**Тест:**
```bash
uv run ruff check src/docuflow/features/task_board/system.py --select F821
python -c "from docuflow.features.task_board.system import TaskBoardSystem"
```

**Критерий успеха:**
- ruff не выдаёт F821 для этого файла
- Импорт модуля работает

**Коммит:** `fix: import logger in task_board/system.py`

---

### Тикет 1.2: Исправить TYPE_CHECKING импорты в sdk.py ✅ ВЫПОЛНЕН
**Приоритет:** CRITICAL
**Оценка:** 20 мин
**Фактически:** 15 мин
**Коммит:** bd72298

**Описание:**
Перенести все forward-reference типы в TYPE_CHECKING блок.

**Изменения в src/docuflow/sdk.py:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docuflow.application.base import BaseSystem
    from docuflow.application.bus.orchestrator import P2POrchestrator
    from docuflow.features.consumables.system import ConsumableSystem
    from docuflow.features.parts.system import PartLibrarySystem
    from docuflow.features.production.system import ProductionSystem
    from docuflow.features.projects.system import ProjectSystem
    from docuflow.infrastructure.config import Config
```

**Тест:**
```bash
uv run ruff check src/docuflow/sdk.py --select F821
uv run mypy src/docuflow/sdk.py --no-error-summary 2>&1 | grep -i error
python -c "from docuflow.sdk import SDK"
```

**Критерий успеха:**
- ruff F821 = 0 для sdk.py
- mypy не выдаёт ошибок типов
- Импорт работает

**Коммит:** `fix: add TYPE_CHECKING imports in sdk.py`

---

### Тикет 1.3: Импортировать PartPreviewWidget в parts/view.py ✅ ВЫПОЛНЕН
**Приоритет:** HIGH
**Оценка:** 10 мин
**Фактически:** 10 мин
**Коммит:** 7af98a1

**Описание:**
Добавить импорт виджета, который используется в view.

**Изменения:**
```python
# В начало src/docuflow/features/parts/view.py
from docuflow.lib.widgets.part_preview import PartPreviewWidget
```

**Тест:**
```bash
uv run ruff check src/docuflow/features/parts/view.py --select F821
python -c "from docuflow.features.parts.view import PartLibraryView"
```

**Критерий успеха:**
- ruff F821 = 0
- Импорт работает

**Коммит:** `fix: import PartPreviewWidget in parts/view.py`

---

### Тикет 1.4: Исправить TYPE_CHECKING в folder_scanner/view.py ✅ ВЫПОЛНЕН
**Приоритет:** HIGH
**Оценка:** 10 мин
**Фактически:** 10 мин
**Коммит:** ac50e62 (часть)

**Описание:**
Добавить SDK в TYPE_CHECKING блок.

**Изменения:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docuflow.sdk import SDK
```

**Тест:**
```bash
uv run ruff check src/docuflow/features/folder_scanner/view.py --select F821
```

**Критерий успеха:**
- ruff F821 = 0

**Коммит:** `fix: add SDK to TYPE_CHECKING in folder_scanner/view.py`

---

### Тикет 1.5: Исправить TYPE_CHECKING в orchestrator.py и admin/system.py ✅ ВЫПОЛНЕН
**Приоритет:** HIGH
**Оценка:** 15 мин
**Фактически:** 15 мин
**Коммит:** ac50e62 (часть)

**Описание:**
Добавить недостающие типы в TYPE_CHECKING блоки.

**Изменения:**
В `src/docuflow/application/bus/orchestrator.py`:
```python
if TYPE_CHECKING:
    from docuflow.infrastructure.housekeeping import HousekeepingSystem
    # ... остальные
```

В `src/docuflow/features/admin/system.py`:
```python
if TYPE_CHECKING:
    from docuflow.application.bus.dispatcher import SecureDispatcher
```

**Тест:**
```bash
uv run ruff check src/docuflow/application/bus/orchestrator.py --select F821
uv run ruff check src/docuflow/features/admin/system.py --select F821
```

**Критерий успеха:**
- ruff F821 = 0 для обоих файлов

**Коммит:** `fix: add TYPE_CHECKING imports in orchestrator and admin system`

---

### Тикет 1.6: Проверка фазы 1 — запуск тестов ✅ ВЫПОЛНЕН
**Приоритет:** HIGH
**Оценка:** 30 мин
**Фактически:** 10 мин
**Коммит:** ac50e62 (финальный)

**Описание:**
Убедиться, что все F821 устранены и pytest собирает тесты.

**Команды:**
```bash
uv run ruff check src/ --select F821
uv run pytest --collect-only -q
```

**Критерий успеха:**
- ruff F821 = 0 ошибок
- pytest собирает все тесты без ImportError

**Коммит:** (нет, это проверка)

---

## ФАЗА 2: Безопасность

**Цель:** Устранить уязвимости безопасности.

**Врата прохождения:**
- ✅ Нет hardcoded паролей (S107 = 0)
- ✅ Jinja2 с autoescape (S701 = 0)
- ✅ MD5 заменён или документирован (S324 = 0 или обоснован)
- ✅ Секреты в env переменных
- ✅ Тесты безопасности проходят

### Тикет 2.1: Убрать hardcoded пароль из bootstrap_admin
**Приоритет:** HIGH
**Оценка:** 20 мин

**Описание:**
Сделать пароль обязательным параметром или читать из env.

**Изменения в auth.py и system.py:**
```python
def bootstrap_admin(self, default_password: str | None = None) -> User | None:
    if default_password is None:
        default_password = os.getenv("DOCUFLOW_ADMIN_PASSWORD")
        if not default_password:
            logger.warning("DOCUFLOW_ADMIN_PASSWORD not set, skipping admin bootstrap")
            return None
```

**Тест:**
```bash
uv run ruff check src/ --select S107
# Проверить, что предупреждение исчезло
```

**Критерий успеха:**
- S107 = 0
- Функция работает с env переменной

**Коммит:** `security: remove hardcoded password from bootstrap_admin`

---

### Тикет 2.2: Включить autoescape в Jinja2
**Приоритет:** HIGH
**Оценка:** 15 мин

**Описание:**
Защитить от XSS в отчётах.

**Изменения в reports/system.py:**
```python
from jinja2 import Environment, BaseLoader, select_autoescape

env = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(['html', 'xml'])
)
```

**Тест:**
```bash
uv run ruff check src/docuflow/features/reports/system.py --select S701
uv run pytest tests/unit/features/test_report_system.py -v
```

**Критерий успеха:**
- S701 = 0
- Тесты отчётов проходят

**Коммит:** `security: enable Jinja2 autoescape in reports`

---

### Тикет 2.3: Документировать использование MD5
**Приоритет:** MEDIUM
**Оценка:** 15 мин

**Описание:**
Добавить комментарий, объясняющий почему MD5 допустим для checksum.

**Изменения:**
```python
def _calculate_md5(self, path: Path) -> str:
    """Calculate MD5 checksum for file deduplication.

    Note: MD5 is used here only for fast file comparison and deduplication,
    not for cryptographic security. For this use case, MD5 is acceptable.
    """
    h = hashlib.md5()  # noqa: S324
```

**Тест:**
```bash
uv run ruff check src/ --select S324
```

**Критерий успеха:**
- S324 подавлен с обоснованием

**Коммит:** `docs: document MD5 usage for file checksums`

---

### Тикет 2.4: Перенести storage_secret в env
**Приоритет:** HIGH
**Оценка:** 20 мин

**Описание:**
Читать секрет из Config вместо хардкода.

**Изменения в main.py:**
```python
ui.run_with(app, title="DocuFlow Portal", storage_secret=_config.storage_secret)
```

**Тест:**
```bash
export DOCUFLOW_STORAGE_SECRET="test_secret_123"
uv run python -m docuflow.main &
# Проверить запуск
```

**Критерий успеха:**
- Секрет читается из env
- Приложение запускается

**Коммит:** `security: move storage_secret to env config`

---

## ФАЗА 3: Качество кода

**Цель:** Устранить анти-паттерны и улучшить обработку ошибок.

**Врата прохождения:**
- ✅ Нет silent except:pass (S110 = 0)
- ✅ Фоновые задачи управляются корректно (RUF006 = 0)
- ✅ Loop variable capture исправлен (B023 = 0)
- ✅ Unit тесты проходят

### Тикет 3.1: Заменить except:pass на логирование в di.py
**Приоритет:** MEDIUM
**Оценка:** 10 мин

**Изменения:**
```python
except Exception:
    logger.debug("Failed to log SDK creation (non-critical)")
```

**Тест:**
```bash
uv run ruff check src/docuflow/infrastructure/di.py --select S110
```

**Критерий успеха:**
- S110 = 0

**Коммит:** `fix: replace silent except with logging in di.py`

---

### Тикет 3.2: Сохранить ссылку на asyncio.create_task
**Приоритет:** MEDIUM
**Оценка:** 15 мин

**Изменения в orchestrator.py:**
```python
self._orchestration_task = asyncio.create_task(self._run_orchestration_master())
```

**Тест:**
```bash
uv run ruff check src/ --select RUF006
```

**Критерий успеха:**
- RUF006 = 0

**Коммит:** `fix: store reference to orchestration background task`

---

### Тикет 3.3: Исправить loop variable capture в admin/view.py
**Приоритет:** MEDIUM
**Оценка:** 15 мин

**Изменения:**
```python
# Использовать default аргументы
lambda nid=new_nid, allow=allowed: system.update_workplace(...)
```

**Тест:**
```bash
uv run ruff check src/docuflow/features/admin/view.py --select B023
```

**Критерий успеха:**
- B023 = 0

**Коммит:** `fix: capture loop variables correctly in admin view callbacks`

---

### Тикет 3.4: Заменить остальные except:pass
**Приоритет:** MEDIUM
**Оценка:** 30 мин

**Описание:**
Пройти по всем оставшимся S110 и добавить логирование.

**Тест:**
```bash
uv run ruff check src/ --select S110
```

**Критерий успеха:**
- S110 = 0

**Коммит:** `fix: replace remaining silent exceptions with logging`

---

## ФАЗА 4: Автофикс и стиль

**Цель:** Автоматически исправить стилевые проблемы.

**Врата прохождения:**
- ✅ ruff --fix применён
- ✅ Изменения проверены вручную
- ✅ Тесты проходят после автофикса

### Тикет 4.1: Запустить ruff --fix
**Приоритет:** LOW
**Оценка:** 30 мин

**Команды:**
```bash
uv run ruff check src/ --fix
git diff
# Ревью изменений
```

**Тест:**
```bash
uv run pytest tests/unit -q
```

**Критерий успеха:**
- Автоисправляемые ошибки устранены
- Тесты проходят

**Коммит:** `style: apply ruff auto-fixes`

---

## ФАЗА 5: Тесты

**Цель:** Добиться прохождения всех тестов.

**Врата прохождения:**
- ✅ Unit тесты проходят (pytest tests/unit)
- ✅ Integration тесты проходят
- ✅ Smoke тесты проходят

### Тикеты 5.x: Создаются по мере обнаружения падений

Каждое падение теста = отдельный тикет с:
- Описанием ошибки
- Изменениями для исправления
- Тестом проверки
- Коммитом

---

## ФАЗА 6: Рефакторинг (опционально)

**Цель:** Улучшить архитектуру.

### Тикет 6.1: Рефакторинг main.py — реестр view
**Приоритет:** LOW
**Оценка:** 2-3 часа

(Детали по запросу)

---

## Отслеживание прогресса

Для каждого тикета:
- [ ] Создан
- [ ] В работе
- [ ] Изменения сделаны
- [ ] Тесты пройдены
- [ ] Коммит создан
- [ ] Закрыт

Для каждой фазы:
- [ ] Все тикеты закрыты
- [ ] Врата прохождения выполнены
- [ ] Переход к следующей фазе

---

## Команды для быстрой проверки

```bash
# Проверка текущей фазы
uv run ruff check src/ --statistics

# Проверка конкретных правил
uv run ruff check src/ --select F821,S107,S701,S324,S110,RUF006,B023

# Запуск тестов по группам
uv run pytest tests/unit -v
uv run pytest tests/integration -v
uv run pytest tests/smoke -v

# Полная проверка
uv run ruff check src/
uv run pytest -q
```

---

Готов начать с Фазы 0, Тикет 0.1. Подтвердите для старта.
