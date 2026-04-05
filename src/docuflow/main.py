import traceback
from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI
from loguru import logger
from nicegui import ui
from sqlmodel import Session

from docuflow.features.admin.system import AdminSystem
from docuflow.features.admin.view import admin_view
from docuflow.features.auth.system import AuthSystem
from docuflow.features.auth.view import login_view

# Import Vertical Slice Features
from docuflow.features.core.layout import MainLayout, get_current_user, theme_setup
from docuflow.features.dashboard.view import dashboard_view
from docuflow.features.docs.portal import DocumentationPortal
from docuflow.features.folder_scanner.view import folder_scanner_view
from docuflow.features.inventory.system import InventorySystem
from docuflow.features.inventory.view import warehouse_view
from docuflow.features.view_presets.system import ViewPresetSystem
from docuflow.features.work_items.system import WorkItemSystem
from docuflow.features.work_items.view import WorkItemsView
from docuflow.infrastructure.config import Config
from docuflow.infrastructure.di import AppProvider
from docuflow.sdk import SDK

# 1. GLOBAL CONTAINER & SDK
_config = Config()
_app_provider = AppProvider(_config)
_fastapi_provider = FastapiProvider()
_container = make_async_container(_app_provider, _fastapi_provider)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Manage SDK and P2P lifecycle."""
    from sqlalchemy import Engine
    from sqlmodel import SQLModel

    # Ensure all models are loaded for DDL generation
    from docuflow.sdk import SDK

    try:
        # 1. Initialize Database Schema
        async with _container() as request_container:
            engine = await request_container.get(Engine)
            SQLModel.metadata.create_all(engine)

            # 2. Resolve SDK (Ensuring it exists for all runners)
            sdk_instance = await request_container.get(SDK)
            fastapi_app.state.sdk = sdk_instance

        # 3. Initialize SettingsRegistry with AdminSystem
        async with _container() as request_container:
            from docuflow.domain.settings import registry

            admin_system = await request_container.get(AdminSystem)
            registry.init(admin_system)
            logger.info("SettingsRegistry initialized with AdminSystem.")

        # 4. Bootstrap P2P and Identity
        # Resolve SDK from the container (app-scoped) and ensure identity
        sdk_instance = await request_container.get(SDK)
        fastapi_app.state.sdk = sdk_instance
        # Sanity check: resolving from the app container should return the same SDK
        try:
            sdk_from_app = await _container.get(SDK)
            if sdk_from_app is not sdk_instance:
                logger.warning("SDK identity mismatch between request resolution and app container")
        except Exception:
            # If resolution from top-level container fails, continue with resolved instance
            logger.debug("Could not resolve SDK from top-level container for identity check")

        await sdk_instance.on_startup()
        async with _container() as request_container:
            auth_system = await request_container.get(AuthSystem)
            auth_system.bootstrap_admin()
            logger.info("Admin bootstrap check complete.")
    except Exception:
        traceback.print_exc()
        raise
    yield
    await sdk_instance.on_shutdown()


# 2. FASTAPI INSTANCE
app = FastAPI(lifespan=lifespan)
setup_dishka(_container, app)


# 3. ROUTING & VIEWS
@ui.page("/login")
async def login_page():
    theme_setup()
    async with _container() as request_container:
        auth_system = await request_container.get(AuthSystem)
        login_view(auth_system)


@ui.page("/")
async def index_page():
    user = get_current_user()
    if not user:
        return ui.navigate.to("/login")

    theme_setup()
    layout = MainLayout(title="DocuFlow Portal", config=_config)

    async def switch_view(view_name: str):
        content_area.clear()
        with content_area:
            async with _container() as request_container:
                if view_name == "dashboard":
                    admin_system = await request_container.get(AdminSystem)
                    from docuflow.application.bus.orchestrator import P2POrchestrator

                    orchestrator = await request_container.get(P2POrchestrator)
                    await dashboard_view(orchestrator, admin_system)
                elif view_name == "warehouse":
                    inventory_system = await request_container.get(InventorySystem)
                    await warehouse_view(inventory_system)
                elif view_name == "admin":
                    admin_system = await request_container.get(AdminSystem)
                    await admin_view(admin_system)
                elif view_name == "work_items":
                    work_item_system = await request_container.get(WorkItemSystem)
                    preset_system = await request_container.get(ViewPresetSystem)
                    view = WorkItemsView(
                        system=work_item_system,
                        preset_system=preset_system,
                        user=user.get("username", "admin"),
                    )
                    view.render()
                elif view_name == "task_board":
                    from docuflow.features.task_board.system import TaskBoardSystem
                    from docuflow.features.task_board.view import TaskBoardView

                    task_board_system = await request_container.get(TaskBoardSystem)
                    preset_system = await request_container.get(ViewPresetSystem)
                    session = await request_container.get(Session)
                    view = TaskBoardView(
                        session=session,
                        system=task_board_system,
                        preset_system=preset_system,
                        user=user.get("username", "admin"),
                    )
                    view.render()
                elif view_name == "scanner":
                    from sqlalchemy import Engine

                    engine = await request_container.get(Engine)
                    sdk = await request_container.get(SDK)
                    await folder_scanner_view(sdk, _config, engine)
                elif view_name == "parts":
                    from docuflow.features.parts.system import PartLibrarySystem
                    from docuflow.features.parts.view import PartLibraryView

                    parts_system = await request_container.get(PartLibrarySystem)
                    view = PartLibraryView(parts_system)
                    await view.render()
                elif view_name == "consumables":
                    from docuflow.features.consumables.system import ConsumableSystem
                    from docuflow.features.consumables.view import ConsumableView

                    consumable_system = await request_container.get(ConsumableSystem)
                    view = ConsumableView(consumable_system)
                    await view.render()
                elif view_name == "chat":
                    from docuflow.features.chat.system import ChatSystem
                    from docuflow.features.chat.view import ChatView

                    chat_system = await request_container.get(ChatSystem)
                    view = ChatView(chat_system)
                    await view.render_portal()
                elif view_name == "incidents":
                    from docuflow.features.chat.incident_view import IncidentView
                    from docuflow.features.chat.incidents import IncidentSystem

                    incident_system = await request_container.get(IncidentSystem)
                    view = IncidentView(incident_system)
                    await view.render_dashboard()
                elif view_name == "reports":
                    from docuflow.features.reports.system import ReportSystem
                    from docuflow.features.reports.view import ReportsView

                    report_system = await request_container.get(ReportSystem)
                    view = ReportsView(report_system)
                    await view.render_portal()
                elif view_name == "analytics":
                    from docuflow.features.analytics.view import analytics_view

                    session = await request_container.get(Session)
                    await analytics_view(session)
                elif view_name == "production":
                    from docuflow.features.production.system import ProductionSystem
                    from docuflow.features.production.view import production_view

                    prod_system = await request_container.get(ProductionSystem)
                    await production_view(prod_system, current_user=user.get("username", "admin"))
                elif view_name == "projects":
                    from docuflow.features.projects.system import ProjectSystem
                    from docuflow.features.projects.view import ProjectManagementView

                    project_system = await request_container.get(ProjectSystem)
                    work_item_system = await request_container.get(WorkItemSystem)
                    view = ProjectManagementView(
                        project_system=project_system, work_item_system=work_item_system
                    )
                    view.render()
                elif view_name == "docs":
                    portal = DocumentationPortal()
                    portal.build_portal()

    # Shared Layout Build
    content_area = layout.build(switch_view)

    # Initial View
    await switch_view("dashboard")


# 6. INTEGRATION & CONFIG
ui.run_with(app, title="DocuFlow Portal", storage_secret="docuflow_nicegui_shh")

if __name__ in {"__main__", "__mp_main__"}:
    import os

    import uvicorn

    port = int(os.getenv("DOCUFLOW_PORT", "8082"))
    uvicorn.run("docuflow.main:app", host="0.0.0.0", port=port, reload=False)
