# 17. Конфигурация (Configuration)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 17.1 Environment Variables

### Config (config.py)
```python
class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DOCUFLOW_",
        env_file_encoding="utf-8",
        extra="ignore"
    )
```

### Variables
| Variable | Default | Required |
|----------|---------|----------|
| DOCUFLOW_NODE_ID | "node_01" | No |
| DOCUFLOW_APP_NAME | "DocuFlow" | No |
| DOCUFLOW_DEBUG | false | No |
| DOCUFLOW_LOG_LEVEL | "INFO" | No |
| DOCUFLOW_SHARED_PATH | "./shared_network" | No |
| DOCUFLOW_DATABASE_URL | "sqlite:///./local.db" | No |
| DOCUFLOW_HEARTBEAT_INTERVAL | 15.0 | No |
| DOCUFLOW_COORDINATOR_TIMEOUT | 45.0 | No |
| DOCUFLOW_STORAGE_SECRET | "docuflow_secret_change_me" | No ⚠️ |

---

## 17.2 .env Template

### Content (.env.template)
```
NODE_ID=node_01
APP_NAME=DocuFlow
DEBUG=true
LOG_LEVEL=INFO
SHARED_PATH=./shared_network
DATABASE_URL=sqlite:///./local.db
HEARTBEAT_INTERVAL=15
COORDINATOR_TIMEOUT=45
BUS_POLL_INTERVAL=5
SYNC_CHECK_INTERVAL=60
GC_INTERVAL=3600
STORAGE_SECRET=docuflow_secret_change_me
```

### ✅ Good
- Template provided
- All variables documented
- Defaults sensible

### ⚠️ Issues
- Secret in template
- No validation
- No required flag

---

## 17.3 Feature Flags

### ❌ NOT FOUND
- No feature flags system
- No runtime toggles

### ⚠️ Impact
- All features always on
- Can't disable features per deployment

---

## 17.4 Secrets Management

### Current
```python
storage_secret: str = "docuflow_secret_change_me"  # noqa: S105
```

### ⚠️ Issues
1. Default in code
2. S105 ignored
3. No validation
4. No rotation

---

## 17.5 Config Validation

### Current
- Pydantic type validation
- No custom validators
- `extra="ignore"` — unknown vars silently ignored

### ⚠️ Issues
- No format validation
- No range validation
- No required secrets

---

## 17.6 Выводы

### ✅ Сильные стороны
- Pydantic-based config
- .env.template provided
- Sensible defaults
- Prefix isolation

### ⚠️ Проблемы
1. **Default secrets** — security risk
2. **No feature flags** — no flexibility
3. **No validation** — invalid config accepted
4. **S105 ignored** — secrets in code
5. **No rotation** — stale secrets

---

## 17.7 Рекомендации

1. **Validate secrets**:
   ```python
   @field_validator('storage_secret')
   @classmethod
   def validate_secret(cls, v):
       if v == "docuflow_secret_change_me":
           raise ValueError("STORAGE_SECRET must be changed!")
       if len(v) < 32:
           raise ValueError("STORAGE_SECRET must be at least 32 chars")
       return v
   ```

2. **Add feature flags**:
   ```python
   class Config(BaseSettings):
       feature_scanner: bool = True
       feature_chat: bool = True
       feature_reports: bool = True
   ```

3. **Strict validation**:
   ```python
   model_config = SettingsConfigDict(
       extra="forbid",  # Reject unknown vars
       env_file=".env",  # Require .env
   )
   ```

---

## 17.8 TODO

- [ ] Remove default secrets
- [ ] Add secret validation
- [ ] Consider feature flags
- [ ] Use extra="forbid"
- [ ] Document secrets rotation

---

*Секция: 17_configuration*
