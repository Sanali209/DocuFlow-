# 12. Качество кода (Code Quality)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 12.1 Ruff Analysis

### Results
| Category | Count |
|----------|-------|
| **Total errors (src)** | 272 |
| **Fixable** | 10 |
| **Fixable (unsafe)** | 36 |

### Error Categories
| Rule | Description | Count |
|------|-------------|-------|
| E402 | Module level import not at top | ~20 |
| E501 | Line too long (>100) | ~50 |
| F401 | Unused import | ~30 |
| F841 | Unused variable | ~40 |
| I100 | Import order | ~50 |
| S101 | assert statements | ~15 |
| UP | Pyupgrade | ~30 |

---

## 12.2 Line Length

### Violations: ~50
```python
# Line too long (117 > 100)
gnc_file = repo_root / "data_sample/sidra/SIDRA-353203-SHLAV-2-07.07.2025/12-06-SIDRA-353203-SHLAV-2-07.07.2025-AA 5052-H32-3.GNC"
```

### ⚠️ Impact
- Hard to read
- Side-scrolling required
- Violates project conventions

---

## 12.3 Import Order

### Issues: ~50
```python
# Should be grouped by stdlib, third-party, local
import json          # stdlib
from passlib...      # third-party
from docuflow...    # local
```

---

## 12.4 Unused Code

### Unused Imports: ~30
### Unused Variables: ~40

### ⚠️ Examples
```python
E402: from docuflow.features.folder_scanner.parsers.gnc import GncParser
     # Import not at top of file

F841: sdk1 = await request_container.get(SDK)
     # Assigned to unused variable
```

---

## 12.5 MyPy

### Configuration
```toml
[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = ["nicegui.*", "sqlmodel.*"]
ignore_missing_imports = true
```

### ⚠️ Issues
- No MyPy errors reported yet
- `ignore_missing_imports = true` — may hide real issues

---

## 12.6 Patterns

### ✅ Good Patterns
- Vertical slices with system.py/view.py
- BaseSystem inheritance
- Type hints on public methods
- Docstrings on classes

### ⚠️ Issues
- Magic strings/values
- Inconsistent naming
- Long functions

---

## 12.7 Docstrings

### Coverage: Partial
```python
class BaseSystem:
    """Base class for all DocuFlow infrastructure..."""

    def __init__(self, config: Config, session: Session | None = None):
        self._config = config
        self.session = session
```

### ⚠️ Issues
- Not all methods documented
- Some docstrings are just titles

---

## 12.8 Выводы

### ✅ Сильные стороны
- Ruff configured
- MyPy configured
- Type hints used
- Vertical slice pattern

### ⚠️ Проблемы
1. **272 ruff errors** — needs cleanup
2. **~50 line length violations** — hard to read
3. **~30 unused imports** — dead code
4. **~40 unused variables** — sloppy
5. **No pre-commit enforcement** — violations slip in

---

## 12.9 Рекомендации

1. **Auto-fix easy issues**:
   ```bash
   uv run ruff check --fix .
   ```

2. **Format imports**:
   ```bash
   uv run ruff check --select=I --fix .
   ```

3. **Add pre-commit hook**:
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: local
       hooks:
         - id: ruff
           name: ruff
           entry: uv run ruff check
           types: [python]
         - id: mypy
           name: mypy
           entry: uv run mypy src
           types: [python]
   ```

4. **CI gate**:
   ```yaml
   - name: Lint
     run: ruff check src/ --exit-non-zero-on-change
   ```

---

## 12.10 TODO

- [ ] Auto-fix ruff errors
- [ ] Fix line length manually
- [ ] Remove unused imports
- [ ] Fix unused variables
- [ ] Add pre-commit hooks
- [ ] Enforce in CI

---

*Секция: 12_code_quality*
