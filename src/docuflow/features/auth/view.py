import json

from nicegui import app as nicegui_app
from nicegui import ui

from docuflow.features.admin.system import AdminSystem
from docuflow.features.auth.system import AuthSystem


def login_view(auth_system: AuthSystem, admin_system: AdminSystem, node_id: str):
    """Providing the centralized, glassmorphic login screen for the DocuFlow node."""

    async def try_login():
        user = await auth_system.authenticate_user(username.value, password.value)
        if user:
            # 1. Retrieve Workplace capabilities for this node
            workplace_modules = []
            workplace = admin_system.get_workplace_by_node_id(node_id)
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
            ui.notify("Invalid Credentials", color="red", icon="priority_high")

    with ui.column().classes("w-full min-h-screen items-center justify-center bg-slate-900"):
        with ui.column().classes(
            "w-[450px] p-12 rounded-3xl card items-center gap-10 relative z-10"
        ):
            with ui.column().classes("items-center gap-4"):
                ui.icon("waves", size="64px", color="teal-400").classes("")
                ui.label("DocuFlow").classes("text-4xl font-extrabold tracking-tight text-white")
                ui.label("P2P ORCHESTRATION ENGINE").classes(
                    "text-[10px] tracking-[0.4em] text-slate-500 font-bold"
                )

            with ui.column().classes("w-full gap-5"):
                username = (
                    ui.input("Username").classes("w-full").props("dark rounded standout color=teal")
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
