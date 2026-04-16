# 16. Технический долг (Technical Debt)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 16.1 Code Smells

### Found: 272 ruff errors
| Category | Count |
|----------|-------|
| Line too long | ~50 |
| Unused imports | ~30 |
| Unused variables | ~40 |
| Import order | ~50 |
| Pyupgrade | ~30 |

### ⚠️ Impact
- Hard to read
- Maintenance overhead
- Cognitive load

---

## 16.2 Magic Values

### Examples
```python
COORDINATOR_TIMEOUT_SECONDS = 45.0  # OK - named
COORDINATOR_STALE_NODE_SECONDS = 60

# But some are hidden
"admin"  # Default username
"admin"  # Default password
```

### ⚠️ Issues
- Default credentials in code
- Magic numbers not extracted

---

## 16.3 Long Functions

### Example
```python
# features/admin/view.py:689
except Exception as e:
    # Very long function
```

### ⚠️ Detection
- No cyclomatic complexity tools
- Ruff doesn't check this

---

## 16.4 Deprecated Code

### Found
```python
# auth/system.py:94
def bootstrap_admin(self, default_password: str | None = None) -> User | None:
    """Legacy alias for get_or_create_admin."""
    return self.get_or_create_admin(default_password)
```

### ⚠️ Issues
- Legacy aliases remain
- No deprecation warnings

---

## 16.5 Dead Code

### Archive Found
```
._archive/
├── old mvp/
│   └── backend/  # Old implementation
```

### ⚠️ Issues
- Archive not cleaned
- May confuse developers

---

## 16.6 Architecture Debt

### Issues from Architecture Report
1. **SDK singleton guard** — non-standard pattern
2. **No Repository pattern** — queries scattered
3. **Session RuntimeError** — fragile
4. **chat.incidents** — strange import structure

---

## 16.7 Выводы

### ✅ Сильные стороны
- Code smells tracked by ruff
- Constants named
- Archive exists

### ⚠️ Критические проблемы
1. **272 lint errors** — accumulated debt
2. **Default secrets** — security debt
3. **Archive not cleaned** — dead code
4. **Legacy aliases** — confusion
5. **No complexity metrics** — hidden issues

---

## 16.8 Рекомендации

1. **Fix lint errors**:
   ```bash
   uv run ruff check --fix .
   ```

2. **Remove archive**:
   ```bash
   rm -rf ._archive/
   ```

3. **Add complexity check**:
   ```yaml
   # .github/workflows/ci.yml
   - name: Check complexity
     run: |
       uv run radon cc src/ -a -j
       uv run xenon -b 10 -m 10 src/
   ```

4. **Deprecation cycle**:
   ```python
   import warnings
   
   def legacy_function():
       warnings.warn(
           "legacy_function is deprecated, use new_function instead",
           DeprecationWarning,
           stacklevel=2
       )
   ```

---

## 16.9 TODO

- [ ] Fix all ruff errors
- [ ] Remove ._archive/
- [ ] Add complexity tools
- [ ] Deprecate legacy aliases
- [ ] Document debt items

---

*Секция: 16_technical_debt*
