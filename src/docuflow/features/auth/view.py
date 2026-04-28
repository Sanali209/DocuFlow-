import json
from collections.abc import Callable

from nicegui import app as nicegui_app
from nicegui import ui

from docuflow.features.admin.system import AdminSystem
from docuflow.features.auth.system import AuthSystem
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.ui_utils import NotifyHelper


def login_view(system_scope: Callable, node_id: str):
    """Providing the centralized, glassmorphic login screen for the DocuFlow node."""
    view = LoginView(system_scope, node_id)
    view.render()


class LoginView(BaseDocuWidget):
    """
    Providing the centralized, glassmorphic login screen for the DocuFlow node.
    """

    def __init__(self, system_scope: Callable, node_id: str):
        super().__init__(system_scope)
        self.node_id = node_id

    def render(self):
        """Render the login UI."""

        async def try_login():
            async with self.scope() as req:
                auth_system = await req.get(AuthSystem)
                admin_system = await req.get(AdminSystem)

                user = await auth_system.authenticate_user(username.value, password.value)
                if user:
                    # 1. Retrieve Workplace capabilities for this node
                    workplace_modules = []
                    workplace = admin_system.get_workplace_by_node_id(self.node_id)
                    if workplace:
                        try:
                            workplace_modules = json.loads(workplace.allowed_modules)
                        except (json.JSONDecodeError, TypeError):
                            workplace_modules = []

                    # 2. Storing session info
                    nicegui_app.storage.user.update(
                        {
                            "user": {
                                "username": user.username,
                                "role": user.role.name if user.role else "Worker",
                                "permissions": user.role.permissions_list if user.role else [],
                                "workplace_modules": workplace_modules,
                            }
                        }
                    )
                    ui.navigate.to("/")
                else:
                    NotifyHelper.error("Invalid Credentials")

        with ui.column().classes("w-full min-h-screen items-center justify-center bg-slate-900"):
            with ui.column().classes(
                "w-[450px] p-12 rounded-3xl card items-center gap-10 relative z-10"
            ):
                with ui.column().classes("items-center gap-4"):
                    ui.icon("waves", size="64px", color="teal-400").classes("")
                    ui.label("DocuFlow").classes(
                        "text-4xl font-extrabold tracking-tight text-white"
                    )
                    ui.label("P2P ORCHESTRATION ENGINE").classes(
                        "text-[10px] tracking-[0.4em] text-slate-500 font-bold"
                    )

                with ui.column().classes("w-full gap-5"):
                    username = (
                        ui.input("Username")
                        .classes("w-full")
                        .props("dark rounded standout color=teal")
                    )
                    password = (
                        ui.input("Password", password=True)
                        .classes("w-full")
                        .props("dark rounded standout color=indigo")
                    )

                    ui.button("AUTHORIZE NODE", on_click=try_login).classes(
                        "w-full h-14 vibrant-btn text-white font-bold rounded-2xl shadow-lg mt-4"
                    )

                ui.label("DECENTRALIZED WORKPLACE IDENTITY").classes(
                    "text-[10px] text-slate-600 font-medium"
                )
