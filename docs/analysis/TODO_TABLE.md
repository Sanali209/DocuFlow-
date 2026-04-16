# 📋 Сводная таблица TODO — по срочности

**Обновлено**: 2026-04-15  
**Всего задач**: 50  
**Источник**: Комплексный анализ `docs/analysis/reports/SUMMARY.md`

---

## 🔴 КРИТИЧЕСКИЕ (Немедленно)

| # | TODO | Описание | Секция | Статус | Решение |
|---|------|---------|--------|--------|---------|
| 1 | Исправить 226 ruff errors | `uv run ruff check --fix src/` | [12_code_quality](./reports/12_code_quality/report.md) | ✅ Готово | |
| 2 | Починить failed tests | 5 failed, 15 errors | [11_testing](./reports/11_testing/report.md) | 🔴 Не начато | |
| 3 | Изменить STORAGE_SECRET | Убрать default `docuflow_secret_change_me` | [07_security](./reports/07_security/report.md) | ⏸️ Отложено | **Отложено** |
| 4 | Создать CI pipeline | `.github/workflows/ci.yml` | [14_cicd](./reports/14_cicd/report.md) | ✅ Готово | |
| 5 | Удалить .\_archive/ | Мёртвый код в репозитории | [16_technical_debt](./reports/16_technical_debt/report.md) | ✅ Не делаем | **Не трогаем** |
| 6 | Починить test errors | Runtime mock issues | [11_testing](./reports/11_testing/report.md) | 🔴 Не начато | |
| 7 | Убрать .db из репозитория | В .gitignore уже есть | [04_database](./reports/04_database/report.md) | ✅ Готово | |

---

## 🟠 ВЫСОКИЙ ПРИОРИТЕТ (Эта неделя)

| # | TODO | Описание | Секция | Статус | Решение |
|---|------|---------|--------|--------|---------|
| 8 | Добавить Alembic migrations | `alembic init migrations` | [04_database](./reports/04_database/report.md) | 🔴 Не начато | |
| 9 | Установить pytest-cov | `uv add pytest-cov` | [11_testing](./reports/11_testing/report.md) | ✅ Готово | |
| 10 | Создать pre-commit hooks | `.pre-commit-config.yaml` | [14_cicd](./reports/14_cicd/report.md) | ✅ Готово | |
| 11 | Убрать bare `except:` | Заменить на конкретные типы | [08_error_handling](./reports/08_error_handling/report.md) | ✅ Готово | |
| 12 | Добавить secret validation | Минимум 32 символа, не default | [07_security](./reports/07_security/report.md) | ⏸️ Отложено | **Отложено** |
| 13 | Добавить password policy | Min length, complexity | [07_security](./reports/07_security/report.md) | ⏸️ Отложено | **Отложено** |
| 14 | Создать Dockerfile | Контейнеризация | [14_cicd](./reports/14_cicd/report.md) | ✅ Готово | |
| 15 | Добавить line length fixes | Длинные строки > 100 символов | [12_code_quality](./reports/12_code_quality/report.md) | 🔴 Не начато | |

---

## 🟡 СРЕДНИЙ ПРИОРИТЕТ (Этот месяц)

| # | TODO | Описание | Секция | Статус | Решение |
|---|------|---------|--------|--------|---------|
| 16 | Добавить retry logic | @retry decorator | [08_error_handling](./reports/08_error_handling/report.md) | ⏸️ Отложено | **Отложено** |
| 17 | Persist sequence state | Сохранять в БД | [06_p2p_clustering](./reports/06_p2p_clustering/report.md) | ⏸️ Отложено | **Отложено** |
| 18 | Уменьшить failover time | 45s → 20s | [06_p2p_clustering](./reports/06_p2p_clustering/report.md) | ✅ Готово | |
| 19 | Добавить eager loading | joinedload для N+1 | [10_performance](./reports/10_performance/report.md) | ⏸️ Отложено | **Отложено** |
| 20 | Добавить pagination | Limit/offset | [10_performance](./reports/10_performance/report.md) | 🔴 Не начато | |
| 21 | Увеличить polling intervals | 2s → 5s, 5s → 10s | [10_performance](./reports/10_performance/report.md) | ✅ Готово | |
| 22 | Добавить health endpoint | `/health` route | [13_observability](./reports/13_observability/report.md) | 🔴 Не начато | |
| 23 | Добавить log rotation | Loguru rotation | [13_observability](./reports/13_observability/report.md) | 🔴 Не начато | |
| 24 | Добавить soft deletes | `is_deleted` field | [04_database](./reports/04_database/report.md) | ⏸️ Отложено | **Отложено** |
| 25 | Enforce status transitions | WorkItem lifecycle | [20_business_logic](./reports/20_business_logic/report.md) | ⏸️ Отложено | **Отложено** |
| 26 | Заменить sync file I/O | aiofiles | [09_concurrency](./reports/09_concurrency/report.md) | 🔴 Не начато | |
| 27 | Добавить task monitoring | Отслеживание orphan tasks | [09_concurrency](./reports/09_concurrency/report.md) | 🔴 Не начато | |
| 28 | Изменить extra="ignore" | extra="forbid" | [08_error_handling](./reports/08_error_handling/report.md) | 🔴 Не начато | |
| 29 | Добавить complexity tools | radon/xenon | [16_technical_debt](./reports/16_technical_debt/report.md) | 🔴 Не начато | |
| 30 | Deprecate legacy aliases | warnings.warn() | [16_technical_debt](./reports/16_technical_debt/report.md) | 🔴 Не начато | |

---

## 🟢 НИЗКИЙ ПРИОРИТЕТ (Следующий квартал)

| # | TODO | Описание | Секция | Статус | Решение |
|---|------|---------|--------|--------|---------|
| 31 | Добавить Prometheus metrics | Счётчики, гистограммы | [13_observability](./reports/13_observability/report.md) | ⏸️ Отложено | **Не трогаем** |
| 32 | Добавить request IDs | Корреляция логов | [13_observability](./reports/13_observability/report.md) | ⏸️ Отложено | **Не трогаем** |
| 33 | JSON structured logging | machine-readable | [13_observability](./reports/13_observability/report.md) | ⏸️ Отложено | **Не трогаем** |
| 34 | Добавить feature flags | Runtime toggles | [17_configuration](./reports/17_configuration/report.md) | ⏸️ Отложено | **Не трогаем** |
| 35 | Extract design tokens | UI constants | [18_ui_ux](./reports/18_ui_ux/report.md) | ⏸️ Отложено | **Не трогаем** |
| 36 | Добавить breadcrumbs | Навигация | [18_ui_ux](./reports/18_ui_ux/report.md) | ⏸️ Отложено | **Не трогаем** |
| 37 | Рассмотреть optimistic updates | UI state | [18_ui_ux](./reports/18_ui_ux/report.md) | ⏸️ Отложено | **Не трогаем** |
| 38 | Добавить accessibility | ARIA, keyboard nav | [18_ui_ux](./reports/18_ui_ux/report.md) | ⏸️ Отложено | **Не трогаем** |
| 39 | Добавить i18n framework | gettext | [19_i18n](./reports/19_i18n/report.md) | ⏸️ Отложено | **Не трогаем** |
| 40 | Извлечь hardcoded strings | 100+ строк | [19_i18n](./reports/19_i18n/report.md) | ⏸️ Отложено | **Не трогаем** |
| 41 | Создать translation files | ru/en | [19_i18n](./reports/19_i18n/report.md) | ⏸️ Отложено | **Не трогаем** |
| 42 | Добавить optimistic locking | Version field | [20_business_logic](./reports/20_business_logic/report.md) | ⏸️ Отложено | **Не трогаем** |
| 43 | Добавить inventory validation | Business rules | [20_business_logic](./reports/20_business_logic/report.md) | ⏸️ Отложено | **Не трогаем** |
| 44 | Periodic integrity check | PRAGMA integrity_check | [21_integrity](./reports/21_integrity/report.md) | ⏸️ Отложено | **Не трогаем** |
| 45 | Добавить reconciliation | Cross-node sync | [21_integrity](./reports/21_integrity/report.md) | ⏸️ Отложено | **Не трогаем** |
| 46 | Добавить offline queue | Queue messages | [22_failover](./reports/22_failover/report.md) | ⏸️ Отложено | **Не трогаем** |
| 47 | Добавить leader alerting | Уведомления | [22_failover](./reports/22_failover/report.md) | ⏸️ Отложено | **Не трогаем** |
| 48 | Документировать backup | Restore procedure | [22_failover](./reports/22_failover/report.md) | ⏸️ Отложено | **Не трогаем** |
| 49 | Сгенерировать OpenAPI | Swagger docs | [15_documentation](./reports/15_documentation/report.md) | ⏸️ Отложено | **Не трогаем** |
| 50 | Создать CONTRIBUTING.md | Contribution guide | [15_documentation](./reports/15_documentation/report.md) | ⏸️ Отложено | **Не трогаем** |

---

## 📊 Статистика по приоритетам

| Приоритет | Количество | % | Готово | Отложено | Не делаем | Осталось |
|-----------|------------|---|--------|----------|-----------|----------|
| 🔴 Критические | 7 | 14% | 2 | 1 | 1 | 3 |
| 🟠 Высокий | 8 | 16% | 4 | 2 | 0 | 2 |
| 🟡 Средний | 17 | 34% | 4 | 5 | 0 | 6 |
| 🟢 Низкий | 18 | 36% | 0 | 0 | 18 | 0 |

---

## ✅ Выполненные задачи (сессия 2026-04-15)

1. **Исправить ruff errors** — авто-фикс + ручные фиксы (S110)
2. **Создать CI pipeline** — `.github/workflows/ci.yml` с lint, test, build
3. **Создать Dockerfile** — базовый образ для контейнеризации
4. **Убрать bare except:** — заменены на logging
5. **Уменьшить failover time** — 45s → 20s (COORDINATOR_TIMEOUT_SECONDS)
6. **Увеличить polling intervals** — BUS_POLLING_INTERVAL 5s→10s, OBSERVER_POLLING_INTERVAL 2s→5s
7. **Health endpoint** — добавлен `/health` в FastAPI
8. **Log rotation** — добавлена ротация в logs/docuflow.log (10MB, 5 дней)

---

## ✅ Выполненные задачи (сессия 2026-04-15)

1. **Исправить ruff errors** — авто-фикс + ручные фиксы (S110)
2. **Создать CI pipeline** — `.github/workflows/ci.yml` с lint, test, build
3. **Создать Dockerfile** — базовый образ для контейнеризации
4. **Убрать bare except:** — заменены на logging
5. **Уменьшить failover time** — 45s → 20s (COORDINATOR_TIMEOUT_SECONDS)
6. **Увеличить polling intervals** — BUS_POLLING_INTERVAL 5s→10s, OBSERVER_POLLING_INTERVAL 2s→5s

---

## 🔄 Следующие задачи

1. Line length fixes (E501) — 85 строк > 100 символов
2. Починить failed tests — интеграционные тесты
3. Добавить Alembic migrations
4. Health endpoint (`/health`)
5. Log rotation

---

*Список задач генерируется автоматически из комплексного анализа*