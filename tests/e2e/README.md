# Playwright E2E Тесты для DocuFlow

## Установка

```bash
# Установить зависимости
uv sync

# Установить браузеры для Playwright
uv run playwright install chromium
```

## Запуск

### 1. Запустить приложение (в отдельном терминале)

```bash
uv run python -m docuflow.main
```

Приложение будет доступно по адресу: http://localhost:8080

### 2. Запустить E2E тесты

```bash
# С отображением браузера (headed)
uv run pytest tests/e2e/ -v --headed

# Headless режим (для CI)
uv run pytest tests/e2e/ -v

# Конкретный тест
uv run pytest tests/e2e/test_playwright_smoke.py::TestSmokeViews::test_login_page_loads -v --headed
```

## Структура тестов

| Файл | Описание |
|------|----------|
| `conftest.py` | Фикстуры: app_url, viewport |
| `test_playwright_smoke.py` | Smoke тесты всех views |

### Test Classes

- **TestSmokeViews** — проверка доступности страниц
- **TestTaskBoardWorkflow** — проверка элементов Task Board
- **TestResponsiveDesign** — адаптивный дизайн
- **TestNavigation** — навигация между страницами

## Требования

- Приложение должно быть запущено на localhost:8080
- Chromium браузер (устанавливается через `playwright install`)

## Отладка

```bash
# Запустить с tracing
uv run pytest tests/e2e/ -v --tracing on

# Скриншоты при ошибках
uv run pytest tests/e2e/ -v --screenshot on
```
