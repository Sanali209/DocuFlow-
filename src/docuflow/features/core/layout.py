from collections.abc import Callable

from nicegui import app as nicegui_app
from nicegui import ui


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
            body { 
                font-family: 'Outfit', sans-serif; 
                background-color: #020617 !important; 
                color: #f8fafc;
                margin:0; padding:0;
            }
            /* Target Quasar drawers specifically to allow glassmorphism */
            .q-drawer {
                background: transparent !important;
            }
            .q-drawer__content {
                background: transparent !important;
            }
            .glass-card {
                background: rgba(15, 23, 42, 0.7) !important;
                backdrop-filter: blur(24px) saturate(180%);
                -webkit-backdrop-filter: blur(24px) saturate(180%);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .vibrant-btn {
                background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
                transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
            }
            .vibrant-btn:hover {
                transform: scale(1.02) translateY(-1px);
                filter: brightness(1.2);
            }
            .nav-item-active {
                background: rgba(99, 102, 241, 0.2) !important;
                border-left: 4px solid #6366f1;
                color: #fff !important;
            }
        </style>
    """)


class MainLayout:
    """Provides a unified header and sidebar for all DocuFlow features.

    Ensures consistent aesthetics (color matching) and decentralized authorization.
    """

    def __init__(self, title: str, config):
        self.title = title
        self._config = config
        self.content = None

    def build(self, switch_view_fn: Callable):
        """Constructing the unified shell with matched sidebar and header backgrounds."""
        user = get_current_user()
        if not user:
            return

        # Header - Fixed Top
        with ui.header().classes(
            "glass-card items-center justify-between px-8 py-4 fixed top-0 w-full z-50"
        ):
            with ui.row().classes("items-center gap-3"):
                ui.icon("waves", size="32px", color="primary").classes("animate-pulse")
                ui.label("DocuFlow").classes("text-2xl font-bold tracking-tight")

            with ui.row().classes("items-center gap-6"):
                with ui.row().classes(
                    "items-center bg-slate-800/50 rounded-full px-4 py-1 border border-white/5"
                ):
                    ui.icon("sensors", size="16px", color="emerald")
                    ui.label(f"NODE: {self._config.node_id}").classes(
                        "text-xs font-mono text-emerald-400 font-bold"
                    )

                with ui.row().classes("items-center gap-2"):
                    ui.avatar(user["username"][0].upper(), color="indigo").classes(
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
            .classes("glass-card border-r border-white/5 p-6 pt-24")
            .style("background-color: transparent !important")
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
            "w-full min-h-screen pt-28 px-10 pb-12 gap-8 bg-[#020617]"
        )
        return self.content
