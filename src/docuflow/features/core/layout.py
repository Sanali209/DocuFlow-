import json
import logging
from collections.abc import Callable
from typing import Any

from nicegui import app as nicegui_app
from nicegui import ui

from docuflow.domain.entities.identity import User, Workplace

logger = logging.getLogger(__name__)


def check_access(user: User, workplace: Workplace) -> bool:
    """Determine if a specific user is authorized to operate a given workplace."""
    if not user.role:
        return False

    # 1. Admin bypass
    if user.role.name.lower() in ["admin", "админ"]:
        return True

    # 2. Check if workplace.id is in user's allowed_workplaces
    try:
        allowed_ids = user.workplace_ids
        return workplace.id in allowed_ids
    except (json.JSONDecodeError, TypeError, AttributeError):
        return False


def get_active_ui_modules(user: User, workplace: Workplace) -> set[str]:
    """Calculate the intersection of user permissions and workplace capabilities."""
    if not user.role:
        return set()

    wp_mods = set(workplace.modules_list)

    # Admins see everything available on the node
    if user.role.name.lower() in ["admin", "админ"]:
        return wp_mods

    # Intersection of Role permissions and Workplace modules
    try:
        user_perms = set(user.role.permissions_list)
        return user_perms.intersection(wp_mods)
    except (json.JSONDecodeError, TypeError, AttributeError):
        return set()


def get_current_user() -> dict | None:
    """Retrieving the current user session from NiceGUI storage."""
    return nicegui_app.storage.user.get("user")


def double_filter_check(permission: str) -> bool:
    """Enforcing the 'User Permission ∩ Workplace Capability' model.

    Administrator role bypasses all checks and has global access.
    """
    user_data = get_current_user()
    if not user_data:
        return False

    # Administrator has all permissions (supporting English/Russian and case-insensitive check)
    role = str(user_data.get("role", "")).lower()
    if role in ["admin", "админ"]:
        return True

    permissions = user_data.get("permissions", [])
    allowed_workplace_modules = user_data.get("workplace_modules", [])

    # Check if the module is allowed on the physical workplace
    if permission not in allowed_workplace_modules:
        return False

    # Check if the user role has any action (read/full/etc) for this module
    # Permissions are stored as ["module:action", ...]
    return any(p.startswith(f"{permission}:") for p in permissions)


def theme_setup():
    """Initializing global design tokens and ensuring dark mode consistency across navigation."""
    ui.dark_mode().enable()
    ui.add_head_html("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
            :root {
                --primary: #14b8a6;
                --primary-hover: #0d9488;
                --primary-subtle: rgba(20, 184, 166, 0.15);
                --bg-base: #0f172a;
                --bg-surface: #1e293b;
                --bg-elevated: #334155;
                --text-primary: #f8fafc;
                --text-secondary: #cbd5e1;
                --text-muted: #64748b;
                --border-subtle: rgba(100, 116, 139, 0.3);
                --border-medium: rgba(100, 116, 139, 0.5);
                --success: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
            }
            body {
                font-family: 'Outfit', sans-serif;
                background-color: var(--bg-base) !important;
                color: var(--text-primary);
                margin:0; padding:0;
            }
            .q-drawer {
                background: var(--bg-surface) !important;
            }
            .q-drawer__content {
                background: var(--bg-surface) !important;
            }
            /* Solid card - no glassmorphism */
            .card {
                background: var(--bg-surface) !important;
                border: 1px solid var(--border-subtle);
                border-radius: 0.75rem;
            }
            /* Primary button - solid teal */
            .btn-primary {
                background: var(--primary) !important;
                border: none;
                transition: transform 0.15s ease, filter 0.15s ease;
            }
            .btn-primary:hover {
                filter: brightness(1.1);
                transform: translateY(-1px);
            }
            /* Secondary button */
            .btn-secondary {
                background: var(--bg-elevated) !important;
                border: 1px solid var(--border-medium);
                color: var(--text-secondary) !important;
            }
            .btn-secondary:hover {
                background: var(--bg-surface) !important;
                border-color: var(--primary);
                color: var(--primary) !important;
            }
            /* Navigation active state - teal */
            .nav-item-active {
                background: var(--primary-subtle) !important;
                border-left: 4px solid var(--primary);
                color: var(--text-primary) !important;
            }
            /* Input field */
            .input-field .q-field__control {
                background: var(--bg-elevated) !important;
                border: 1px solid var(--border-subtle);
                border-radius: 0.5rem;
            }
            .input-field .q-field__control:focus-within {
                border-color: var(--primary);
            }
            /* Divider */
            .divider {
                border-color: var(--border-subtle);
            }
            /* Surface container */
            .surface {
                background: var(--bg-surface);
                border: 1px solid var(--border-subtle);
                border-radius: 0.5rem;
            }
        </style>
    """)


class SessionContext:
    """Управляет глобальным состоянием интерфейса в рамках сессии пользователя."""

    @staticmethod
    def set(key: str, value: Any) -> None:
        nicegui_app.storage.user[f"ctx_{key}"] = value

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        return nicegui_app.storage.user.get(f"ctx_{key}", default)

    @staticmethod
    def clear(key: str) -> None:
        nicegui_app.storage.user.pop(f"ctx_{key}", None)


class MainLayout:
    """Provides a unified header and sidebar for all DocuFlow features.

    Ensures consistent aesthetics (color matching) and decentralized authorization.
    """

    def __init__(self, title: str, config, search_system: Any = None, system_provider: Any = None):
        self.title = title
        self._config = config
        self.search_system = search_system
        self.system_provider = system_provider
        self.content = None
        self._active_timers: list[ui.timer] = []

    def register_timer(self, timer: ui.timer) -> ui.timer:
        """Track a timer for the current view session."""
        self._active_timers.append(timer)
        return timer

    def clear_timers(self):
        """Deactivate all timers registered for the current view session."""
        for t in self._active_timers:
            try:
                t.active = False
                t.deactivate()
            except Exception:
                logger.debug("Timer deactivation failed, ignoring")
        self._active_timers.clear()

    def build(self, switch_view_fn: Callable):
        """Constructing the unified shell with matched sidebar and header backgrounds."""
        user = get_current_user()
        if not user:
            return

        # Header - Fixed Top
        with ui.header().classes(
            "card items-center justify-between px-8 py-4 fixed top-0 w-full z-50"
        ):
            with ui.row().classes("items-center gap-3"):
                ui.icon("waves", size="32px", color="teal").classes("")
                ui.label("DocuFlow").classes("text-2xl font-bold tracking-tight")

            # --- OMNIBAR (Global Search) ---
            if self.search_system:
                self._render_omnibar(switch_view_fn)

            with ui.row().classes("items-center gap-6"):
                with ui.row().classes(
                    "items-center bg-slate-800/60 rounded-full px-4 py-1 border border-slate-700/50"
                ):
                    ui.icon("sensors", size="16px", color="emerald")
                    ui.label(f"NODE: {self._config.node_id}").classes(
                        "text-xs font-mono text-emerald-400 font-bold"
                    )

                with ui.row().classes("items-center gap-2"):
                    ui.avatar(user["username"][0].upper(), color="teal").classes(
                        "text-white font-bold"
                    )
                    ui.label(user["username"]).classes("font-semibold text-slate-200")

                ui.button(
                    icon="logout",
                    on_click=lambda: (nicegui_app.storage.user.clear(), ui.navigate.to("/login")),
                ).props("flat round text-color=slate-400")

        # Sidebar - Fixed Left (Color Matched to Header)
        with (
            ui.left_drawer(value=True)
            .classes("card border-r border-slate-700/50 p-6 pt-24")
            .style("background-color: var(--bg-surface) !important")
            .props("persistent")
        ):
            with ui.column().classes("w-full gap-4"):

                def nav_item(label, icon, view_name):
                    # In this modular approach, we pass view_name to orchestrate routing
                    return (
                        ui.button(label, icon=icon, on_click=lambda: switch_view_fn(view_name))
                        .classes(
                            "w-full justify-start normal-case text-slate-300 hover:text-white px-4 py-3 rounded-xl hover:bg-white/5 transition-all"
                        )
                        .props("flat")
                    )

                nav_item("Dashboard", "dashboard", "dashboard")

                if double_filter_check("workitems"):
                    nav_item("Work Items", "work", "work_items")

                if double_filter_check("board"):
                    nav_item("Task Board", "dashboard", "task_board")

                if double_filter_check("scanner"):
                    nav_item("Folder Scanner", "biotech", "scanner")

                if double_filter_check("inventory"):
                    nav_item("Warehouse", "inventory_2", "warehouse")
                    nav_item("Finished Pallets", "all_inbox", "production")
                    nav_item("Parts Library", "hub", "parts")
                    if double_filter_check("projects"):
                        nav_item("Projects", "folder_special", "projects")
                    nav_item("Supplies", "category", "consumables")

                ui.separator().classes("bg-white/5 my-4")
                nav_item("Workshop Chat", "forum", "chat")
                nav_item("Incidents", "report_problem", "incidents")
                nav_item("Analytics KPIs", "monitoring", "analytics")
                nav_item("Reports & Exports", "analytics", "reports")
                nav_item("Documentation", "auto_stories", "docs")

                if str(user.get("role", "")).lower() in ["admin", "админ"]:
                    ui.separator().classes("bg-white/5 my-4")
                    nav_item("System Admin", "settings", "admin")

        # Main Content Area
        self.content = ui.column().classes(
            "w-full min-h-screen pt-28 px-10 pb-12 gap-8 bg-slate-900"
        )
        return self.content

    def _render_omnibar(self, switch_view_fn: Callable) -> None:
        """Рендерит Omnibar — строку глобального поиска."""
        with ui.row().classes("items-center w-[400px] relative"):
            search_input = (
                ui.input(placeholder="Поиск по нарядам, деталям, паллетам...")
                .props('rounded outlined dense dark prefix="search"')
                .classes("w-full omnibar-input")
            )

            results_menu = ui.menu().props("no-parent-event fit")

            async def handle_search(e):
                query = e.value
                if not query or len(query) < 2:
                    results_menu.close()
                    return

                results = await self.search_system.search(query)
                if not results:
                    results_menu.clear()
                    with results_menu:
                        ui.item("Nothing found").classes("text-slate-500 italic")
                    results_menu.open()
                    return

                results_menu.clear()
                with results_menu:
                    for res in results:
                        with ui.item(
                            on_click=lambda r=res: self._on_search_select(
                                r, switch_view_fn, results_menu
                            )
                        ):
                            with ui.section().props("side"):
                                ui.icon(res.icon, color="primary")
                            with ui.section():
                                ui.item_label(res.title).classes("font-bold")
                                ui.item_label(res.subtitle).props("caption")

                            # --- QUICK ACTION: PULL TO NODE ---
                            if res.type == "work_item":
                                with ui.section().props("side"):
                                    ui.button(
                                        icon="install_desktop",
                                        on_click=lambda r=res: self._pull_to_current_node(
                                            r, switch_view_fn
                                        ),
                                    ).props("flat round color=orange-400").classes("ml-2")
                                    ui.tooltip(f"Забрать на узел {self._config.node_id}")

                results_menu.open()

            search_input.on("update:model-value", handle_search)

    async def _pull_to_current_node(self, result, switch_view_fn: Callable) -> None:
        """Быстрое назначение наряда на текущий физический узел."""
        try:
            ui.notify(
                f"Наряд {result.title} передан на узел {self._config.node_id}", type="warning"
            )
            switch_view_fn("task_board", filter_work_item=result.id)
        except Exception as e:
            ui.notify(f"Ошибка захвата: {e}", type="negative")

    def _on_search_select(self, result, switch_view_fn, menu) -> None:
        """Обработка выбора результата поиска с сохранением контекста и авто-открытием."""
        menu.close()

        # Сохраняем контекст в сессию
        if result.type == "work_item":
            SessionContext.set("active_work_item_id", result.id)
            SessionContext.set("last_search_query", result.title)

            # --- AUTO-OPEN WORK ITEM CARD ---
            async def auto_open():
                from docuflow.domain.entities.production import WorkItem
                from docuflow.features.work_items.system import WorkItemSystem
                from docuflow.lib.widgets.work_item_card import WorkItemCard

                system = (
                    await self.system_provider(WorkItemSystem) if self.system_provider else None
                )
                if system:
                    work_item = system.db_session.get(WorkItem, result.id)
                    if work_item:
                        user_data = get_current_user()
                        WorkItemCard(
                            work_item,
                            system,
                            user_data.get("username", "admin") if user_data else "admin",
                            on_navigate=switch_view_fn,
                            system_provider=self.system_provider,
                        ).render()

            ui.timer(0.1, auto_open, once=True)

        elif result.type == "pallet":
            SessionContext.set("active_pallet_id", result.id)

        ui.notify(f"Результат: {result.title}", type="info")

        # Передаем параметры в роутер
        payload = {}
        if result.type == "work_item":
            payload["filter_work_item"] = result.id

        switch_view_fn(result.view_name, **payload)
