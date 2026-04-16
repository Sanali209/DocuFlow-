# 11. Тестирование (Testing)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 11.1 Test Coverage

### Pytest Results
| Metric | Value |
|--------|-------|
| **Collected tests** | 64 |
| **Passed** | 224 |
| **Failed** | 10 |
| **Skipped** | 6 |
| **Errors** | 15 |
| **Warnings** | 6 |

### ⚠️ Issue
- Collection shows 64 but 224+ passed — may be sub-tests

---

## 11.2 Test Types

### Test Structure
```
tests/
├── smoke/
│   └── test_workshop_pipeline.py
├── unit/
│   ├── features/
│   │   ├── test_task_board_system.py
│   │   ├── test_ns_mirror.py
│   │   ├── test_incident_system.py
│   │   └── ...
│   ├── infrastructure/
│   │   └── test_file_bus_atomic_write.py
│   └── lib/
│       └── test_widgets.py
├── ui/
│   └── test_full_ui_coverage.py
└── integration/
    └── test_folder_scanner_integration.py
```

### ✅ Good
- Unit tests organized by feature
- Separate smoke tests
- Integration tests

### ⚠️ Missing
- No e2e framework
- No performance tests
- No security tests

---

## 11.3 Async Tests

### pytest-asyncio Usage
```python
@pytest.mark.asyncio
async def test_mirror_preserves_structure(...):
    await service._sync_bucket(settings)
```

### ✅ Pattern
- `@pytest.mark.asyncio` decorator used
- Async fixtures supported

---

## 11.4 Test Quality

### Test Naming
```python
# Good
async def test_mirror_preserves_structure(tmp_path, service, mock_sdk, session):
async def test_report_creates_log_and_chat(incident_system, session):
```

### ✅ Conventions
- Descriptive names
- Clear setup/teardown

---

## 11.5 Test Issues

### ❌ Failed Tests: 10
```
FAILED tests/smoke/test_workshop_pipeline.py::test_full_workshop_pipeline
FAILED tests/test_folder_scanner_integration.py::test_scan_now_on_master
FAILED tests/test_folder_scanner_integration.py::test_scan_now_on_slave
FAILED tests/test_folder_scanner_integration.py::test_get_status
FAILED tests/test_folder_scanner_integration.py::test_scan_all_with_existing_path
FAILED tests/test_inventory_integration.py::test_inventory_settings_registration
FAILED tests/test_main.py::test_api_endpoints - assert 404 == 200
FAILED tests/test_scanner_diagnosis.py::TestScannerDiagnosis::test_diagnosis_is_master_returns_false_when_orchestrator_none
FAILED tests/ui/test_full_ui_coverage.py::test_smoke_dashboard
FAILED tests/ui/test_full_ui_coverage.py::test_smoke_task_board
```

### ❌ Errors: 15
```
ERROR tests/ui/test_new_features.py::test_work_items_view_rendering
ERROR tests/unit/lib/test_widgets.py::TestStatusBadge::test_render_work_item_status
```

---

## 11.6 Test Warnings

### Runtime Warnings
```
RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
RuntimeWarning: coroutine 'FolderScannerSystem._discovery_loop' was never awaited
```

### ⚠️ Issues
- Async mocks not properly awaited
- Background tasks not cleaned up

---

## 11.7 Coverage

### ❌ Not measured
- `pytest-cov` not installed
- No coverage report available

---

## 11.8 Выводы

### ✅ Сильные стороны
- Good test organization
- Async tests supported
- Descriptive test names
- Integration tests exist

### ⚠️ Проблемы
1. **10 failed tests** — broken builds
2. **15 errors** — test infrastructure issues
3. **No coverage** — not measured
4. **Async warnings** — improper mocking
5. **Integration tests failing** — environment issues

---

## 11.9 Рекомендации

1. **Fix failed tests** — priority #1
2. **Add pytest-cov**:
   ```bash
   uv add pytest-cov
   uv run pytest --cov=src --cov-report=html
   ```

3. **Fix async warnings**:
   ```python
   # Before
   mock_sdk.resolve_system_by_type = AsyncMock()
   
   # After  
   async def mock_resolve(cls):
       return ...
   mock_sdk.resolve_system_by_type = AsyncMock(side_effect=mock_resolve)
   ```

4. **CI gate**:
   ```yaml
   - name: Run tests
     run: pytest --fail-under=70
   ```

---

## 11.10 TODO

- [ ] Fix 10 failed tests
- [ ] Fix 15 test errors
- [ ] Add pytest-cov
- [ ] Add coverage gate
- [ ] Fix async warnings

---

*Секция: 11_testing*
