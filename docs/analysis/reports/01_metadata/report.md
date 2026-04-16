# 01. Метаданные репозитория

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 1.1 Основная информация

| Параметр | Значение |
|----------|----------|
| **Название** | DocuFlow |
| **Описание** | Decentralized Factory Orchestration |
| **Версия** | 0.1.0 |
| **Python** | 3.12+ |
| **License** | Не указана |
| **Stars/Forks** | Не применимо (private) |

---

## 1.2 Git статистика

| Метрика | Значение |
|---------|----------|
| **Всего коммитов** | 155 |
| **Коммитов в 2026** | 154 |
| **Веток локальных** | 1 (main) |
| **Веток remote** | 6 |
| **Последний коммит** | 2026-04-14 13:03:44 |

### Ветки
```
main (активная)
remotes/origin/copilot/set-up-copilot-instructions
remotes/origin/feature/roadmap-implementation-918442099448330876
remotes/origin/feature/settings-view-header-menu-10288534067991935538
remotes/origin/fix-cleanup-warehouse-models-17953549036587788052
remotes/origin/gnc-parser-implementation-11634970649088116768
remotes/origin/gnc-roadmap-11393833172960051165
```

### Contributors
- `copilot-swe-agent[bot]`
- `google-labs-jules[bot]`
- `Sanali209`

---

## 1.3 Размер кодовой базы

| Директория | Файлов | Размер |
|------------|--------|--------|
| `src/` | 285 | 2,863 KB (~2.8 MB) |

---

## 1.4 Структура проекта

### Features (Vertical Slices)
Всего: **40 директорий** в `features/`

| # | Feature | Описание |
|---|---------|----------|
| 1 | admin | Cluster health & Identity management |
| 2 | analytics | Аналитика |
| 3 | auth | RBAC & Session management |
| 4 | chat | Чат |
| 5 | consumables | Расходники |
| 6 | core | Ядро |
| 7 | dashboard | Dashboard |
| 8 | docs | Документация |
| 9 | folder_scanner | Сканер папок |
| 10 | inventory | Decentralized stock tracking |
| 11 | notifications | Уведомления |
| 12 | parts | Библиотека деталей |
| 13 | production | Производство |
| 14 | projects | Проекты |
| 15 | reports | Отчёты |
| 16 | task_board | Доска задач |
| 17 | view_presets | Пресеты видов |
| 18 | work_items | Рабочие элементы |

### Тесты
| Параметр | Значение |
|----------|----------|
| **Тестовых файлов** | 68 |
| **Unit тестов** | ~25+ |

---

## 1.5 Tech Stack

| Компонент | Технология | Версия |
|-----------|------------|--------|
| **UI Framework** | NiceGUI | >=3.9.0 |
| **Web Framework** | FastAPI | >=0.135.2 |
| **DI** | Dishka | >=1.9.1 |
| **ORM** | SQLModel | >=0.0.37 |
| **Database** | SQLite | - |
| **Async** | AnyIO | >=4.13.0 |
| **Security** | passlib[bcrypt] | >=1.7.4 |
| **Config** | pydantic-settings | >=2.13.1 |
| **Logging** | loguru | >=0.7.3 |

---

## 1.6 CI/CD

| Параметр | Статус |
|----------|--------|
| **GitHub Actions** | ❌ Отсутствует |
| **Pre-commit hooks** | ✅ Настроены |
| **Docker** | ⚠️ .dockerignore есть, Dockerfile не найден |

---

## 1.7 Анализ активности

### Коммиты по месяцам (2026)
- **Январь**: ~1 коммит
- **Февраль**: ~0 коммитов
- **Март**: ~0 коммитов
- **Апрель**: ~153 коммита (активная фаза)

### Рефакторинг активность
Последние коммиты указывают на:
- Фиксы F821 (undefined names)
- Security hardening (Jinja2 autoescape, hardcoded password removal)
- Code quality (ruff autofix)
- Documentation updates

---

## 1.8 Выводы

### ✅ Сильные стороны
- Активная разработка в 2026 году
- Хорошая структура features (vertical slices)
- Настроены линтеры и type checking
- Много тестов (68 файлов)

### ⚠️ Требует внимания
- **Нет GitHub Actions** для CI/CD
- **Отсутствует License**
- Несколько веток feature не влиты в main
- Нет Docker конфигурации
- Ограниченное количество contributors (3, включая bots)

---

## 1.9 Рекомендации

1. **Добавить CI/CD pipeline** — GitHub Actions для автоматических тестов
2. **Указать License** — MIT или Apache 2.0
3. **Регулярный merge** feature веток
4. **Создать Dockerfile** для production deployment
5. **Периодический анализ** — согласно плану `docs/analysis/PLAN.md`

---

*Секция: 01_metadata*
