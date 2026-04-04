# Implementation Plan - Iteration 7: Declarative Control Plane

Evolving the DocuFlow Admin Panel into a professional, schema-driven Cluster Control Plane. This iteration focuses on declarative settings (Pydantic), protecting core identities, and stabilizing the User/Role CRUD.

## User Review Required

> [!IMPORTANT]
> This plan introduces a major architectural shift from ad-hoc key-value settings to a **Declarative Settings Registry**. Every module will now be required to define its own `BaseSettings` schema.

> [!WARNING]
> The **'admin'** role will become immutable. Any attempt to modify or delete the root 'admin' identity via the P2P mesh or UI will be hard-blocked to prevent cluster lockout.

## Proposed Changes

### 1. Domain & Settings Registry [NEW]

Introduce a formalized settings domain that allows modules to declare their parameters.

#### [NEW] [settings.py](file:///src/docuflow/domain/settings.py)
- Define `BaseModuleSettings(BaseModel)` as the foundation for all module configurations.
- Support field-level metadata for **Scoped Parameters**:
    - `Field(default=..., json_schema_extra={"scope": "global"})`: Cluster-wide truth.
    - `Field(default=..., json_schema_extra={"scope": "local"})`: Hardware-specific override.
- Implement a `SettingsRegistry` to manage these schemas.

#### [MODIFY] [identity.py](file:///src/docuflow/domain/entities/identity.py)
- Refine `NodeSetting` to allow `node_id=None` for global cluster-wide parameters.

---

### 2. Module Synchronization & Logic

Update the existing features to participate in the new declarative framework.

#### [MODIFY] [system.py (Admin)](file:///src/docuflow/features/admin/system.py)
- **Role Protection**: Add `if role_name == 'admin': return` to `delete_role` and `upsert_role` (for core perms).
- **Registry Integration**: Update `AdminSystem` to introspect the `SettingsRegistry`.
- **Validation**: Ensure `update_node_setting` validates incoming JSON against the registered Pydantic model for that module.

#### [MODIFY] [system.py (Inventory)](file:///src/docuflow/features/inventory/system.py)
- Declare `class InventorySettings(BaseModuleSettings)` with fields like `poll_interval_seconds: int = 5`.
- Register this schema with the central registry upon startup.

---

### 3. High-Fidelity UI Overhaul

Restoring the User/Role functionality and implementing the dynamic Settings Grid.

#### [MODIFY] [view.py (Admin)](file:///src/docuflow/features/admin/view.py)
- **Identity Registry [FIX]**: Restore the functional "Register User" and "Create Role" dialogs.
- **Protected Actions**: Visually disable the 'Delete' button for the 'admin' user and role.
- **Dynamic Scoped Settings**: 
    - Group parameters by **Global** vs **Local** scope.
    - Generate high-fidelity forms based on Pydantic schemas (e.g. `ui.number` for ints).

---

## Open Questions Resolved

- **Global vs Local**: Supported via declarative metadata in the Pydantic models.
- **Settings Persistence**: Stored in the existing `NodeSetting` table with `node_id` as the scope differentiator.

## Verification Plan

### Automated Tests
- `pytest tests/test_admin_security.py`: Verify that 'admin' role cannot be deleted.
- `pytest tests/test_settings_registry.py`: Verify that invalid JSON types are rejected.

### Manual Verification
- Launch Node A and Node B.
- Create a Manager role and verify sync.
- Update Inventory poll interval on Node B from Node A's panel and confirm log activity.
