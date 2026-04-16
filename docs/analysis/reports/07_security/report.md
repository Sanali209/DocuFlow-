# 07. Безопасность (Security)

**Дата анализа**: 2026-04-15  
**Аналитик**: Automated Analysis

---

## 7.1 Authentication

### Password Hashing (auth/system.py)
```python
class AuthSystem(BaseSystem):
    def __init__(self, ...):
        self._pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)
    
    def verify_password(self, plain: str, hashed: str) -> bool:
        return self._pwd_context.verify(plain, hashed)
```

### ✅ Сильные стороны
- **PBKDF2-SHA256** — стандартный key derivation
- **Passlib context** — проверенная библиотека
- **Deprecated auto** — автоматическая миграция

### ⚠️ Проблемы
- **Default admin password** — "admin"/"admin" по умолчанию
- **No password policy** — нет требований к сложности
- **No account lockout** — brute force возможен
- **No password expiry** — бессрочные пароли

---

## 7.2 P2P Security (HMAC)

### HMACSigner (security.py)
```python
class HMACSigner:
    def sign(self, payload: str) -> str:
        return hmac.new(
            self._secret_bytes,
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
    
    def verify(self, payload: str, signature: str) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)
```

### ✅ Сильные стороны
- **HMAC-SHA256** — cryptographic signature
- **compare_digest** — timing attack protection
- **Secret key** — per-cluster shared secret

### ⚠️ Проблемы
- **Hardcoded default secret** — `"docuflow_secret_change_me"`
- **Shared secret** — все узлы знают ключ
- **No key rotation** — секрет не меняется
- **No per-node keys** — symmetric encryption

---

## 7.3 Secrets Management

### Default Secret (config.py)
```python
class Config(BaseSettings):
    storage_secret: str = "docuflow_secret_change_me"  # noqa: S105
```

### ⚠️ Критические проблемы
1. **Default in code** — секрет в исходниках
2. **No .env check** — не проверяется изменение
3. **S105 ignore** — ruff rule ignored
4. **Пароли в логах** — потенциальная утечка

---

## 7.4 Input Validation

### ✅ Pydantic Validation
```python
class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DOCUFLOW_",
        env_file_encoding="utf-8",
        extra="ignore"
    )
```

### ⚠️ Missing Validations
- **No node_id format** — любые символы
- **No path validation** — path traversal возможен
- **No URL validation** — database_url не проверен

---

## 7.5 Authorization

### Role-Based Access (identity.py)
```python
class Role(BaseEntity, table=True):
    name: str = Field(unique=True)
    permissions: str = Field(default="[]")

class User(BaseEntity, table=True):
    role_id: int = Field(foreign_key="role.id")
    allowed_workplaces: str = Field(default="[]")
```

### Permissions Format
```json
["*:full"]  // Admin
["inventory:read", "inventory:write"]
```

### ⚠️ Проблемы
- **JSON string** — не типизировано
- **No permission checking** — RBAC не реализован в коде
- **Wildcard permissions** — `*:full` too permissive

---

## 7.6 File Operations Security

### Path Validation (bus.py)
```python
def _is_valid_new_message(self, filename: str) -> bool:
    is_json = filename.endswith(constants.BUS_EXTENSION)
    is_not_temp = not filename.startswith(constants.BUS_TEMP_PREFIX)
    return is_json and is_not_temp
```

### ✅ Защита
- **Extension check** — только .json
- **Prefix check** — игнорирует TEMP_

### ⚠️ Уязвимости
- **Path traversal** — `../` не проверяется
- **Symbolic links** — following possible
- **File size limits** — no limits

---

## 7.7 SQL Injection

### ✅ SQLModel Protection
```python
# Parameterized queries via SQLModel
statement = select(User).where(User.username == username)
user = self.db_session.exec(statement).first()
```

### ⚠️ Потенциальные проблемы
- **JSON fields** — `json.loads()` может быть уязвим
- **Dynamic table names** — если есть

---

## 7.8 XSS / CSRF

### NiceGUI Handling
- NiceGUI автоматически экранирует вывод
- Jinja2 autoescape включен (судя по коммиту abb1b7d)

### ✅ Recent Security Fix
```
abb1b7d security: enable Jinja2 autoescape in reports
```

---

## 7.9 Выводы

### ✅ Сильные стороны
- PBKDF2-SHA256 password hashing
- HMAC-SHA256 message signing
- compare_digest protection
- Jinja2 autoescape enabled
- Parameterized SQL queries

### ⚠️ Критические проблемы
1. **Default secrets in code** — "docuflow_secret_change_me"
2. **No password policy** — weak passwords allowed
3. **No RBAC enforcement** — permissions exist but not used
4. **No brute force protection** — rate limiting missing
5. **Path traversal** — not validated

---

## 7.10 Рекомендации

1. **Убрать дефолтные секреты**:
   ```python
   storage_secret: str = Field(min_length=32)
   # Валидация при старте
   if storage_secret == "docuflow_secret_change_me":
       raise ValueError("STORAGE_SECRET must be changed!")
   ```

2. **Добавить password policy**:
   ```python
   PASSWORD_MIN_LENGTH = 8
   PASSWORD_REQUIRE_UPPER = True
   PASSWORD_REQUIRE_DIGIT = True
   ```

3. **Rate limiting**:
   ```python
   MAX_LOGIN_ATTEMPTS = 5
   LOCKOUT_DURATION = 300  # 5 minutes
   ```

4. **Path validation**:
   ```python
   def sanitize_path(path: str) -> str:
       return os.path.normpath(path).replace("..", "")
   ```

5. **Key rotation**:
   ```python
   # Add versioned secrets
   storage_secret_v1: str
   storage_secret_v2: str | None = None
   ```

---

## 7.11 TODO

- [ ] Изменить дефолтный STORAGE_SECRET
- [ ] Добавить password policy
- [ ] Реализовать rate limiting
- [ ] Добавить path validation
- [ ] Документировать RBAC permissions

---

*Секция: 07_security*
