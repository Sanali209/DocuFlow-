# DocuFlow Design System

## Overview

Teal Industrial Design System for DocuFlow v4.0.

**Целевой вид:** Industrial, high-contrast, flat surfaces — не consumer SaaS.

---

## Color Palette

### Primary Colors

| Token | HEX | Usage |
|-------|-----|-------|
| `--primary` | `#14b8a6` | Buttons, links, active states |
| `--primary-hover` | `#0d9488` | Hover state |
| `--primary-subtle` | `rgba(20, 184, 166, 0.15)` | Backgrounds, highlights |

### Backgrounds

| Token | HEX | Usage |
|-------|-----|-------|
| `--bg-base` | `#0f172a` | Page background (slate-900) |
| `--bg-surface` | `#1e293b` | Card, panel background (slate-800) |
| `--bg-elevated` | `#334155` | Elevated surfaces (slate-700) |

### Text

| Token | HEX | Usage |
|-------|-----|-------|
| `--text-primary` | `#f8fafc` | Main text (slate-50) |
| `--text-secondary` | `#cbd5e1` | Secondary text (slate-300) |
| `--text-muted` | `#64748b` | Muted, labels (slate-500) |

### Borders

| Token | Value | Usage |
|-------|-------|-------|
| `--border-subtle` | `rgba(100, 116, 139, 0.3)` | Card borders |
| `--border-medium` | `rgba(100, 116, 139, 0.5)` | Active borders |

### Semantic

| Token | HEX | Usage |
|-------|-----|-------|
| `--success` | `#10b981` | Emerald — success states |
| `--warning` | `#f59e0b` | Amber — warnings |
| `--danger` | `#ef4444` | Red — errors, critical |

---

## CSS Classes

### `.card`
Solid surface card — replaces `.glass-card`.

```html
<div class="card p-4">Content</div>
```

### `.btn-primary`
Primary button with teal background.

```html
<button class="btn-primary">Action</button>
```

### `.btn-secondary`
Secondary outlined button.

```html
<button class="btn-secondary">Cancel</button>
```

### `.input-field`
Standard input field.

```html
<input class="input-field" />
```

### `.surface`
Container with surface styling.

```html
<div class="surface p-4">Panel</div>
```

---

## Widget Library

### New Components (`lib/widgets/`)

| Component | File | Purpose |
|-----------|------|---------|
| `Card` | card.py | Base card container |
| `CardRow` | card.py | Card with row layout |
| `KPICard` | kpi_card.py | Metric card for dashboard |
| `KPIGrid` | kpi_card.py | Grid of KPI cards |
| `PrimaryBtn` | button.py | Primary teal button |
| `SecondaryBtn` | button.py | Secondary button |
| `GhostBtn` | button.py | Ghost/text button |
| `Surface` | surface.py | Surface container |
| `SurfaceSection` | surface.py | Section with header |
| `SurfaceCard` | surface.py | Card alias |
| `StatusIndicator` | status_indicator.py | Status dot indicator |
| `StatusDot` | status_indicator.py | Simple dot |
| `InfoRow` | info_row.py | Label: value row |
| `InfoGrid` | info_row.py | Grid of rows |
| `InputLabel` | input.py | Input with label |
| `TextareaLabel` | input.py | Textarea with label |
| `SelectLabel` | input.py | Select with label |
| `SwitchLabel` | input.py | Switch with label |
| `CheckboxLabel` | input.py | Checkbox with label |

### Usage Example

```python
from docuflow.lib.widgets import KPICard, PrimaryBtn, Card

# KPI Card
KPICard(
    label="TOTAL WORK ITEMS",
    value="156",
    subtitle="Active in workshop",
    icon="inventory"
).render()

# Primary Button
PrimaryBtn(
    text="Start Task",
    icon="play_arrow",
    on_click=handle_start
).render()

# Card with content
def my_content():
    ui.label("Content")
Card(content=my_content, padding="p-6").render()
```

---

## Migration Guide

### Old → New

| Old | New |
|-----|-----|
| `glass-card` | `.card` |
| `#6366f1` (indigo) | `#14b8a6` (teal) |
| `text-gray-400` | `text-slate-400` |
| `text-gray-500` | `text-slate-500` |
| `text-gray-600` | `text-slate-500` |
| `border-white/5` | `border-slate-700/50` |
| `border-white/10` | `border-slate-700/70` |
| `bg-slate-900/50` | `bg-slate-800/60` |
| `animate-pulse` | (removed) |
| `blur-3xl` | (removed) |

### Files Changed

- `src/docuflow/features/core/layout.py` — theme_setup()
- `src/docuflow/features/dashboard/view.py`
- `src/docuflow/features/analytics/view.py`
- `src/docuflow/features/auth/view.py`
- `src/docuflow/lib/widgets/batch_card.py`
- `src/docuflow/lib/widgets/bucket_panel.py`
- `src/docuflow/lib/widgets/work_item_card.py`
- `src/docuflow/lib/widgets/activity_stream.py`
- `src/docuflow/lib/widgets/ns_mirror_status.py`
- `src/docuflow/lib/widgets/scan_log_panel.py`

---

## Design Principles

1. **No decorative noise** — blur orbs, gradients removed
2. **High contrast** — readable in workshop environment
3. **Flat surfaces** — solid colors, no glassmorphism
4. **Semantic colors** — teal primary, emerald/amber/red for status
5. **Industrial feel** — factory-appropriate, not consumer

---

## Testing

```bash
# UI tests
uv run pytest tests/ui/ -v

# Unit tests  
uv run pytest tests/unit/ -v

# Code quality
uv run ruff check src/docuflow/
```

---

**Last updated:** 2026-04-14
**Version:** 4.0