# TICKET_TEMPLATE.md
# Скопировать для нового тикета: cp TICKET_TEMPLATE.md phase{N}/DF-0XX_name.md

# DF-0XX: Название тикета

## Метаданные

| Поле | Значение |
|---|---|
| **Phase** | N |
| **Priority** | 🔴 CRITICAL / 🟡 HIGH / 🟢 MEDIUM |
| **Status** | TODO / IN_PROGRESS / DONE |
| **Зависит от** | [DF-YYY](./phase{N}/DF-YYY_name.md) |
| **Блокирует** | [DF-ZZZ](./phase{N}/DF-ZZZ_name.md) |
| **Архитектура** | [ссылка](../architecture/02_application_architecture.md) |

---

## Контекст

Почему этот тикет существует. Какую проблему решает.
Ссылки на related архитектурные разделы.

---

## Execution Plan

```
Пошаговый план реализации:
  1. Написать тесты ПЕРВЫМИ (TDD!)
  2. Реализовать ...
  3. Проверить ...
```

---

## Подзадачи

- [ ] Подзадача 1
  - [ ] Детальный пункт
- [ ] Подзадача 2

---

## Псевдокод

```python
# Ключевые алгоритмы и структуры

class MySystem(BaseSystem):
    def my_method(self, param: type) -> ReturnType:
        """
        Docstring объясняет архитектурное решение.
        """
        ...
```

---

## TDD: Тесты написать ПЕРВЫМИ

Файл: `tests/unit/phaseN/test_module.py`

```python
def test_happy_path():
    ...

def test_edge_case():
    ...

def test_graceful_fallback():
    ...  # нет raise
```

---

## Definition of Done

```
✓ Критерий 1
✓ Критерий 2
✓ Все тесты проходят
```
