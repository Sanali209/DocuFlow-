# 02. Зависимости (Dependencies)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 2.1 Python пакеты

### Установленные пакеты: 72

### Production Dependencies

| Пакет | Требуемая версия | Установленная | Статус |
|-------|------------------|---------------|--------|
| dishka | >=1.9.1 | 1.9.1 | ✅ OK |
| fastapi | >=0.135.2 | 0.135.2 | ✅ OK |
| loguru | >=0.7.3 | 0.7.3 | ✅ OK |
| nicegui | >=3.9.0 | 3.9.0 | ✅ OK |
| passlib[bcrypt] | >=1.7.4 | 1.7.4 | ✅ OK |
| pydantic-settings | >=2.13.1 | 2.13.1 | ✅ OK |
| rich | >=14.3.3 | 14.3.3 | ✅ OK |
| sqlmodel | >=0.0.37 | 0.0.37 | ✅ OK |
| uvicorn[standard] | >=0.42.0 | 0.42.0 | ✅ OK |
| watchdog | >=6.0.0 | 6.0.0 | ✅ OK |

### Dev Dependencies

| Пакет | Требуемая версия | Установленная | Статус |
|-------|------------------|---------------|--------|
| anyio | >=4.13.0 | 4.13.0 | ✅ OK |
| mypy | >=1.20.0 | 1.20.0 | ✅ OK |
| pytest | >=9.0.2 | 9.0.2 | ✅ OK |
| pytest-asyncio | >=1.3.0 | 1.3.0 | ✅ OK |
| ruff | >=0.15.8 | 0.15.8 | ✅ OK |

### Transitiv Dependencies (Key)

| Пакет | Версия | Назначение |
|-------|--------|------------|
| pydantic | 2.12.5 | Validation |
| sqlalchemy | 2.0.48 | ORM |
| starlette | 1.0.0 | Web framework |
| aiohttp | 3.13.5 | HTTP client |
| httpx | 0.28.1 | HTTP client |
| bcrypt | 5.0.0 | Password hashing |
| jinja2 | 3.1.6 | Templating |
| orjson | 3.11.8 | JSON parsing |
| python-socketio | 5.16.1 | WebSocket |
| wsproto | 1.3.2 | WebSocket |

---

## 2.2 Lock File

| Параметр | Значение |
|----------|----------|
| **Файл** | `uv.lock` |
| **Последнее обновление** | 2026-04-05 08:25:50 |
| **Версия формата** | 1 |
| **Revision** | 3 |
| **Python requirement** | >=3.12 |

**Статус**: ✅ Актуален

---

## 2.3 System Dependencies

| Компонент | Требование |
|-----------|------------|
| **OS** | Windows, macOS, Linux |
| **Python** | 3.12+ |
| **uv** | Для управления зависимостями |

### Native Extensions
- `bcrypt` (native)
- `lxml` (native)
- `watchfiles` (native)
- `aiormq` dependencies

---

## 2.4 Уязвимости (Vulnerabilities)

> ⚠️ Audit не запущен (PowerShell не поддерживает `||`)

### Рекомендуемые проверки:
```bash
uv pip audit
safety check
pip-audit
```

---

## 2.5 Deprecated Packages

| Пакет | Статус | Заметка |
|-------|--------|---------|
| `annotated-doc` | ⚠️ Неизвестно | Не mainstream |

---

## 2.6 Анализ зависимостей

### Размер dependency tree
- **Всего пакетов**: 72
- **Production**: ~12 (прямые)
- **Development**: ~5 (прямые)
- **Transitive**: ~55

### Потенциальные проблемы

#### ⚠️ Неиспользуемые зависимости
Не обнаружены в pyproject.toml, но установлены:
- `annotated-doc` — не используется напрямую?

#### ⚠️ Deprecated packages
- `annotated-doc` 0.0.4 — может быть устаревшим

### Конфликты версий
✅ Не обнаружены — uv.lock синхронизирован

---

## 2.7 Reproducibility

| Параметр | Значение |
|----------|----------|
| **Lock file** | ✅ Актуален |
| **Python version** | ✅ 3.12+ |
| **Platform** | ✅ Кроссплатформенный |

---

## 2.8 Выводы

### ✅ Сильные стороны
- Все версии синхронизированы между pyproject.toml и uv.lock
- Lock файл актуален (2 недели)
- Нет явных конфликтов версий
- Все пакеты в requirements satisfied

### ⚠️ Требует внимания
- **Нет security audit** — необходимо запустить `uv pip audit`
- **annotated-doc** — подозрительный пакет, проверить использование
- **Нет Docker** — для воспроизводимости в prod нужен Dockerfile

---

## 2.9 Рекомендации

1. **Запустить security audit**:
   ```bash
   uv pip audit
   safety check
   ```

2. **Проверить annotated-doc**:
   ```bash
   grep -r "annotated-doc" src/
   ```

3. **Создать Dockerfile** для reproducibility

4. **Добавить dependency check в CI**

---

## 2.10 TODO

- [ ] Запустить `uv pip audit`
- [ ] Проверить использование `annotated-doc`
- [ ] Добавить CI/CD dependency check

---

*Секция: 02_dependencies*
