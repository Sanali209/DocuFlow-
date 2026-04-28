import os
import traceback
from contextlib import asynccontextmanager

from docuflow.lib.utils.os_utils import kill_port_process

_port = int(os.getenv("DOCUFLOW_PORT", "8082"))
if __name__ in {"__main__", "__mp_main__"}:
    kill_port_process(_port)

from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI
from loguru import logger
from nicegui import ui

from docuflow.features.admin.system import AdminSystem
from docuflow.features.auth.system import AuthSystem
from docuflow.features.auth.view import login_view
from docuflow.features.core.layout import MainLayout, SessionContext, get_current_user, theme_setup
from docuflow.features.core.search import SearchSystem
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.di import AppProvider
from docuflow.sdk import SDK

_config = Config()
_app_provider = AppProvider(_config)
_fastapi_provider = FastapiProvider()
_container = make_async_container(_app_provider, _fastapi_provider)


# --- GLOBAL SYSTEM PROVIDERS ---
@asynccontextmanager
async def system_scope():
    """Provides a safe request scope for views to resolve and use systems."""
    async with _container() as request_container:
        yield request_container


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Manage SDK and P2P lifecycle."""
    from sqlalchemy import Engine
    from sqlmodel import SQLModel

    try:
        # 1. Initialize Database Schema
        async with _container() as request_container:
            engine = await request_container.get(Engine)
            SQLModel.metadata.create_all(engine)

            # 2. Resolve SDK
            sdk_instance = await request_container.get(SDK)
            fastapi_app.state.sdk = sdk_instance

        # 3. Initialize SettingsRegistry
        async with _container() as request_container:
            from docuflow.domain.settings import registry

            admin_system = await request_container.get(AdminSystem)
            registry.init(admin_system)
            logger.info("SettingsRegistry initialized.")

        # 4. Bootstrap P2P
        sdk_instance = await _container.get(SDK)
        await sdk_instance.on_startup()

        async with _container() as request_container:
            auth_system = await request_container.get(AuthSystem)
            auth_system.bootstrap_admin()
            auth_system.ensure_default_workplace()
            logger.info("Admin bootstrap check complete.")

    except Exception:
        traceback.print_exc()
        raise
    yield
    await sdk_instance.on_shutdown()


from docuflow.features.core.views import ViewRegistry


def register_all_views():
    from docuflow.features.admin.view import register_admin_view
    from docuflow.features.analytics.view import register_analytics_view
    from docuflow.features.chat.incident_view import register_incidents_view
    from docuflow.features.chat.view import register_chat_view
    from docuflow.features.consumables.view import register_consumables_view
    from docuflow.features.dashboard.view import register_dashboard_view
    from docuflow.features.docs.portal import register_docs_view
    from docuflow.features.folder_scanner.view import register_scanner_view
    from docuflow.features.inventory.view import register_warehouse_view
    from docuflow.features.parts.view import register_parts_view
    from docuflow.features.production.view import register_production_view
    from docuflow.features.projects.view import register_projects_view
    from docuflow.features.reports.view import register_reports_view
    from docuflow.features.task_board.view import register_task_board_view
    from docuflow.features.work_items.view import register_work_items_view

    register_dashboard_view()
    register_warehouse_view()
    register_work_items_view()
    register_admin_view()
    register_task_board_view()
    register_scanner_view()
    register_parts_view()
    register_consumables_view()
    register_chat_view()
    register_incidents_view()
    register_reports_view()
    register_analytics_view()
    register_production_view()
    register_projects_view()
    register_docs_view()


register_all_views()

app = FastAPI(lifespan=lifespan)
setup_dishka(_container, app)


# --- HEALTH ENDPOINT ---
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "docuflow", "version": "0.1.0"}


@ui.page("/login")
async def login_page():
    theme_setup()
    login_view(system_scope, _config.node_id)


@ui.page("/")
async def index_page():
    user = get_current_user()
    if not user:
        return ui.navigate.to("/login")

    theme_setup()

    async with _container() as request_container:
        search_system = await request_container.get(SearchSystem)
        layout = MainLayout(
            title="DocuFlow Portal",
            config=_config,
            search_system=search_system,
            system_scope=system_scope,
        )

    async def switch_view(view_name: str, **kwargs):
        # 0. Prevent Timer Zombies & State Leaks
        layout.clear_timers()
        content_area.clear()

        # 1. Persist Navigation State (Deep Link Survival)
        SessionContext.set("active_view", view_name)
        if "filter_work_item" in kwargs:
            SessionContext.set("active_filter_work_item", kwargs["filter_work_item"])
        else:
            SessionContext.clear("active_filter_work_item")

        with content_area:
            view_info = ViewRegistry.get_view(view_name)
            if not view_info:
                ui.label(f"View '{view_name}' not found.").classes("text-red-500 p-8")
                return

            async with system_scope() as request_container:
                # 1. Resolve Dependencies
                resolved_deps = []
                for dep_type in view_info.dependencies:
                    resolved_deps.append(await request_container.get(dep_type))

                # 2. Add extra parameters
                if view_info.pass_user:
                    resolved_deps.append(user.get("username", "admin"))
                if view_info.pass_switch_view:
                    resolved_deps.append(switch_view)
                if view_info.pass_system_scope:
                    resolved_deps.append(system_scope)
                if view_info.pass_layout:
                    resolved_deps.append(layout)

                # 3. Render
                if view_info.is_async:
                    res = await view_info.render_fn(*resolved_deps, **kwargs)
                    if hasattr(res, "render"):
                        await res.render()
                else:
                    res = view_info.render_fn(*resolved_deps, **kwargs)
                    if hasattr(res, "render"):
                        res.render()

    # Shared Layout Build
    content_area = layout.build(switch_view)

    # Initial View (Restore from SessionContext if available)
    saved_view = SessionContext.get("active_view", "dashboard")
    saved_filter = SessionContext.get("active_filter_work_item")

    init_kwargs = {}
    if saved_filter:
        init_kwargs["filter_work_item"] = saved_filter

    await switch_view(saved_view, **init_kwargs)


ui.run_with(app, title="DocuFlow Portal", storage_secret="docuflow_nicegui_shh")

if __name__ in {"__main__", "__mp_main__"}:
    import uvicorn

    uvicorn.run("docuflow.main:app", host="0.0.0.0", port=_port, reload=False)
