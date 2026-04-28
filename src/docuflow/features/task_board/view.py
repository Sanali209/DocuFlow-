from typing import Any

from nicegui import ui
from sqlmodel import Session

from docuflow.domain.entities.production import WorkerBucketEntry
from docuflow.features.core.layout import SessionContext
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.bucket_panel import BucketPanel
from docuflow.lib.widgets.handover_banner import HandoverBanner
from docuflow.lib.widgets.handover_form import HandoverForm
from docuflow.lib.widgets.hierarchy_table import HierarchyTable
from docuflow.lib.widgets.ui_utils import NotifyHelper


def register_task_board_view():
    """Register the task board view in the global registry."""
    ViewRegistry.register(
        ViewInfo(
            name="task_board",
            label="Task Board",
            icon="assignment",
            render_fn=task_board_view_wrapper,
            pass_user=True,
            pass_system_scope=True,
            pass_layout=True,
            is_async=True,
        )
    )


async def task_board_view_wrapper(user: str, system_scope: Any, layout: Any, **kwargs):
    """Wrapper to instantiate and render the TaskBoardView."""
    view = TaskBoardView(system_scope, user=user, layout=layout, **kwargs)
    await view.render()  # type: ignore[call-arg]


class TaskBoardView(BaseDocuWidget):
    def __init__(
        self,
        system_scope: Any,
        user: str = "admin",
        layout: Any = None,
        node_id: str | None = None,
        role: str = "operator",
        filter_work_item_id: int | None = None,
        **kwargs,
    ):
        super().__init__(system_scope)
        self.user = user
        self.layout = layout
        self.node_id = node_id
        self.role = role or SessionContext.get("task_board_role", "operator")
        self.filter_work_item_id = filter_work_item_id or kwargs.get("filter_work_item_id")

    @ui.refreshable
    async def render(self) -> None:
        """Рендерит основной view."""
        async with self.scope() as req:
            from docuflow.features.admin.system import AdminSystem

            admin_system = await req.get(AdminSystem)
            nodes = admin_system.get_workplace_node_ids()

            with ui.column().classes("w-full p-4"):
                # Check if workplaces are configured
                if not nodes:
                    with ui.column().classes("w-full p-8 items-center"):
                        ui.label("⚠️ Рабочие места не настроены").classes(
                            "text-2xl font-bold text-yellow-400"
                        )
                        ui.label("Перейдите в Admin → BINDINGS для настройки").classes(
                            "text-slate-400"
                        )
                        ui.button(
                            "Открыть Admin",
                            icon="settings",
                            on_click=lambda: ui.navigate.to("/admin"),
                        ).classes("mt-4 vibrant-btn")
                    return

                with ui.tabs().classes("w-full mb-4") as tabs:
                    production_tab = ui.tab("Производство")
                    basket_tab = ui.tab("Моя корзина")

                with ui.tab_panels(tabs, value=production_tab).classes("w-full"):
                    with ui.tab_panel(production_tab):
                        await HierarchyTable(
                            user_id=self.user,
                            view_name="task_board_production",
                            system_scope=self.system_scope,
                        ).render()

                    with ui.tab_panel(basket_tab):
                        with ui.column().classes("w-full gap-4"):
                            self._render_node_selector(nodes)
                            await self._render_handover_banner(req)
                            BucketPanel(
                                node_id=self.node_id if self.node_id else "UNKNOWN",
                                user=self.user,
                                system_scope=self.system_scope,
                            ).render()  # type: ignore[call-arg]
                            HandoverForm(
                                node_id=self.node_id if self.node_id else "UNKNOWN",
                                on_submit=self._execute_handover,
                                on_toggle=self.render.refresh,
                                system_scope=self.system_scope,
                            ).render()

    def _render_role_switcher(self) -> None:
        """Рендерит переключатель роли."""
        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label("Роль:").classes("text-slate-500")
            ui.toggle(
                {"operator": "Оператор", "foreman": "Бригадир"},
                value=self.role,
                on_change=lambda e: self._switch_role(e.value),
            )

            if self.filter_work_item_id:
                with ui.badge("Активен фильтр по наряду").props(
                    "color=orange outline icon=filter_alt"
                ):
                    ui.button(icon="close", on_click=self._clear_filter).props("flat dense size=xs")

    def _clear_filter(self) -> None:
        """Очищает фильтр наряда."""
        self.filter_work_item_id: Any = None
        self.render.refresh()

    def _switch_role(self, role: str) -> None:
        """Переключает роль."""
        self.role = role
        SessionContext.set("task_board_role", role)
        self.render.refresh()

    async def _render_handover_banner(self, req: Any) -> None:
        """Рендерит баннер входящей заметки о передаче смены."""
        if not self.node_id:
            return
        tb_system = await req.get(TaskBoardSystem)
        bucket_entries = tb_system.get_bucket(self.node_id)

        for entry in bucket_entries:
            if entry.handover_note and entry.assigned_user == self.user:

                async def do_accept(e: WorkerBucketEntry = entry) -> None:
                    async with self.scope() as req2:
                        session = await req2.get(Session)
                        e.handover_note = None
                        session.add(e)
                        session.commit()
                    self.render.refresh()

                HandoverBanner(
                    from_operator=entry.handover_from or "Unknown",
                    note=entry.handover_note,
                    on_accept=do_accept,
                    system_scope=self.system_scope,
                ).render()

    async def _execute_handover(self, recv_operator: str, note: str) -> None:
        """Выполняет передачу смены."""
        if not recv_operator:
            NotifyHelper.warning("Укажите кому сдаете смену")
            return

        if not self.node_id:
            NotifyHelper.warning("Рабочее место не выбрано")
            return

        async with self.scope() as req:
            tb_system = await req.get(TaskBoardSystem)
            tb_system.handover(
                self.node_id,
                recv_operator,
                note if note else "Смена закрыта без комментариев",
            )

        NotifyHelper.success("Смена успешно передана")
        self.render.refresh()

    def _render_node_selector(self, nodes) -> None:
        """Рендерит выбор узла."""
        if not nodes:
            return

        # Initialize node_id if not set
        if not self.node_id:
            self.node_id = nodes[0]

        from docuflow.lib.widgets.input import SelectLabel

        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label("Рабочее место:").classes("text-slate-500")
            default_node = self.node_id if self.node_id and self.node_id in nodes else nodes[0]

            SelectLabel(
                label="",
                options=nodes,
                value=default_node,
                on_change=lambda e: self._select_node(e.value),
            ).render().classes("w-48")

    async def _select_node(self, node_id: str) -> None:
        """Выбирает узел."""
        if not node_id or not isinstance(node_id, str):
            return

        self.node_id = node_id
        self.render.refresh()
