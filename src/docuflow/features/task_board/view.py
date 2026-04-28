from functools import partial
from typing import Any

from nicegui import ui
from sqlmodel import Session

from docuflow.domain.entities.production import (
    TaskItem,
    WorkerBucketEntry,
)
from docuflow.features.core.layout import SessionContext
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.features.task_board.batch_engine import BatchEngine
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets import StatusBadge
from docuflow.lib.widgets.bucket_panel import BucketPanel
from docuflow.lib.widgets.hierarchy_table import HierarchyTable
from docuflow.lib.widgets.ui_utils import NotifyHelper, get_kpi_color, get_node_status_color


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
                        self._render_node_selector(nodes)
                        BucketPanel(
                            node_id=self.node_id if self.node_id else "UNKNOWN",
                            user=self.user,
                            system_scope=self.system_scope,
                        ).render()  # type: ignore[call-arg]
                        with ui.row().classes("w-full justify-end mt-4"):
                            ui.button(
                                "Сдать смену",
                                icon="swap_horiz",
                                on_click=self._show_handover_dialog,
                            ).props("color=orange rounded-xl")

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

    # ==================== ВИД ОПЕРАТОРА ====================

    async def _render_operator_view(self, req, nodes) -> None:
        """Рендерит вид оператора."""
        with ui.column().classes("w-full gap-4"):
            # Выбираем узел (инициализирует self.node_id)
            self._render_node_selector(nodes)

            # Корзина оператора - передаем явно node_id
            BucketPanel(
                node_id=self.node_id if self.node_id else "UNKNOWN",
                user=self.user,
                system_scope=self.system_scope,
            ).render()  # type: ignore[call-arg]

            # Передача смены
            with ui.row().classes("w-full justify-end mt-4"):
                ui.button(
                    "Сдать смену", icon="swap_horiz", on_click=self._show_handover_dialog
                ).props("color=orange rounded-xl")

    def _show_handover_dialog(self):
        from docuflow.lib.widgets.input import InputLabel, TextareaLabel

        with ui.dialog() as dialog, ui.card().classes("p-6 w-[400px] gap-4"):
            ui.label("Сдача смены").classes("text-xl font-bold text-orange-400")

            recv_operator_widget = InputLabel(
                label="Имя сменщика (кому передать)", placeholder="Введите имя..."
            ).render()

            note_widget = TextareaLabel(
                label="Заметка по работе / материалу", placeholder="Добавьте детали..."
            ).render()

            with ui.row().classes("w-full justify-between items-center"):
                ui.button("Отмена", on_click=dialog.close).props("flat text-color=slate-400")
                ui.button(
                    "ПОДТВЕРДИТЬ СДАЧУ",
                    on_click=lambda: self._execute_handover(
                        recv_operator_widget.value, note_widget.value, dialog
                    ),
                ).props("color=orange rounded-xl").classes("font-bold")
        dialog.open()

    async def _execute_handover(self, recv_operator: str, note: str, dialog):
        if not recv_operator:
            NotifyHelper.warning("Укажите кому сдаете смену")
            return

        async with self.scope() as req:
            tb_system = await req.get(TaskBoardSystem)
            tb_system.handover(
                self.node_id, recv_operator, str(note) if note else "Смена закрыта без комментариев"
            )

        NotifyHelper.success("Смена успешно передана")
        dialog.close()
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
        """Выбирает узел и проверяет заметки о передаче смены."""
        if not node_id or not isinstance(node_id, str):
            return

        self.node_id = node_id

        async with self.scope() as req:
            tb_system = await req.get(TaskBoardSystem)
            session = await req.get(Session)

            # Проверка заметок о передаче смены
            bucket_entries = tb_system.get_bucket(node_id)
            handover_notes = [
                e.handover_note
                for e in bucket_entries
                if e.handover_note and e.assigned_user == self.user
            ]

            if handover_notes:
                self._show_handover_alert(handover_notes[0])
                # Очищаем заметки после прочтения, чтобы не показывать снова
                for e in bucket_entries:
                    if e.handover_note:
                        e.handover_note = None
                        session.add(e)
                session.commit()

        self.render.refresh()

    def _show_handover_alert(self, note: str) -> None:
        """Показывает диалог с заметкой от предыдущей смены."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("p-6 w-[450px] bg-orange-50 border-2 border-orange-200"),
        ):
            with ui.row().classes("items-center gap-2 mb-2"):
                ui.icon("info", color="orange").classes("text-2xl")
                ui.label("Заметка от предыдущей смены").classes("text-lg font-bold text-orange-800")

            ui.label(note).classes("text-body1 text-orange-900 mb-4 whitespace-pre-wrap italic")

            with ui.row().classes("w-full justify-end"):
                ui.button("ПРИНЯТО", on_click=dialog.close).props(
                    "color=orange rounded-xl"
                ).classes("font-bold")
        dialog.open()

    # ==================== ВИД БРИГАДИРА ====================

    async def _render_foreman_view(self, req, nodes) -> None:
        """Рендерит вид бригадира."""
        # Если есть фильтр наряда, открываем вкладку 'Неназначенные' по умолчанию
        default_tab_name = "Неназначенные" if self.filter_work_item_id else "Все узлы"

        with ui.tabs().classes("w-full mb-4") as tabs:
            all_nodes_tab = ui.tab("Все узлы")
            batching_tab = ui.tab("Батчинг")
            unassigned_tab = ui.tab("Неназначенные")

        with ui.tab_panels(tabs, value=default_tab_name).classes("w-full"):
            with ui.tab_panel(all_nodes_tab):
                await self._render_all_nodes_panel(req, nodes)

            with ui.tab_panel(batching_tab):
                await self._render_batching_panel(req)

            with ui.tab_panel(unassigned_tab):
                await self._render_unassigned_panel(req)

    async def _render_all_nodes_panel(self, req, nodes) -> None:
        """Панель всех узлов."""
        tb_system = await req.get(TaskBoardSystem)
        session = await req.get(Session)

        for node_id in nodes:
            # Получаем батчи и задачи для расчета KPI
            bucket_entries = tb_system.get_bucket(node_id)
            batches = self._group_by_batch(session, bucket_entries)

            # Расчет среднего Drift % по узлу
            node_drift = tb_system.get_node_drift(node_id)
            node_status = tb_system.get_node_status(node_id)

            with (
                ui.card()
                .classes("w-full mb-4 p-4 border-l-4")
                .style(f"border-color: {get_node_status_color(node_status)}")
            ):
                with ui.row().classes("items-center justify-between mb-2"):
                    with ui.row().classes("items-center gap-2"):
                        ui.label(f"🔹 {node_id}").classes("text-h6")
                        ui.badge(node_status).props(f"color={get_node_status_color(node_status)}")

                    # KPI Drift Badge
                    self._render_kpi_drift(node_drift)

                # Показываем батчи узла
                if batches:
                    for batch_id, tasks in batches.items():
                        with ui.row().classes(
                            "gap-2 items-center ml-4 mb-2 "
                            "hover:bg-gray-50 p-1 rounded cursor-pointer"
                        ):
                            StatusBadge(tasks[0].status).render() if tasks else None

                            # Deep Link to WorkItem
                            if tasks and tasks[0].work_item_id:
                                wi_id = tasks[0].work_item_id
                                ui.link(f"Наряд: {wi_id}", "#").on(
                                    "click",
                                    partial(self._show_work_item_by_id, wi_id),
                                ).classes("font-bold text-blue-600")

                            ui.label(f"Батч {batch_id[:8]}...").classes("text-sm text-slate-500")
                            ui.label(f"({len(tasks)} задач)").classes("text-xs")
                else:
                    ui.label("Нет активных батчей").classes("text-slate-400 ml-4")

    def _render_kpi_drift(self, drift: float) -> None:
        """Рендерит KPI бейдж отклонения."""
        color = get_kpi_color(drift)
        icon = "trending_up" if drift > 0 else "trending_down"

        with ui.row().classes(
            f"items-center gap-1 text-{color}-600 bg-{color}-50 px-2 py-1 rounded-full"
        ):
            ui.icon(icon, size="xs")
            ui.label(f"DRIFT: {drift:.1f}%").classes("text-xs font-bold")
            ui.tooltip("Отклонение фактического времени от планового")

    async def _show_work_item_by_id(self, work_item_id: int) -> None:
        """Открывает карточку наряда по ID (Deep Link)."""
        # Resolve WorkItem from session
        from docuflow.domain.entities.production import WorkItem
        from docuflow.lib.widgets.work_item_card import WorkItemCard

        async with self.scope() as req:
            session = await req.get(Session)
            work_item = session.get(WorkItem, work_item_id)

            if work_item:
                await WorkItemCard(
                    work_item, None, self.user, system_scope=self.system_scope
                ).render()
            else:
                NotifyHelper.error(f"Наряд {work_item_id} не найден")

    async def _render_batching_panel(self, req) -> None:
        """Панель батчинга."""
        tb_system = await req.get(TaskBoardSystem)
        session = await req.get(Session)

        with ui.row().classes("gap-4 mb-4"):
            ui.button(
                "🔄 Авто-батчинг",
                on_click=self._run_auto_batching,
            ).props("color=blue")

            # Button for manual batching
            self.merge_button = (
                ui.button(
                    "🔗 Объединить в батч",
                    on_click=self._create_manual_batch,
                )
                .props("color=orange")
                .classes("hidden")
            )

        # Непривязанные задачи
        unassigned = tb_system.get_unassigned_tasks(self.filter_work_item_id)

        if unassigned:
            ui.label(f"Непривязанных задач: {len(unassigned)}").classes("mb-4")

            # Batching table with multi-selection
            columns = [
                {"name": "id", "label": "ID", "field": "id"},
                {"name": "file_name", "label": "Файл", "field": "file_name", "align": "left"},
                {"name": "sheet_qty", "label": "Листов", "field": "sheet_qty"},
                {"name": "status", "label": "Статус", "field": "status"},
                {"name": "mat", "label": "Материал", "field": "mat"},
            ]

            rows = []
            for t in unassigned:
                mat_code = "—"
                if t.mat_type_id:
                    from docuflow.domain.entities.production import MaterialType

                    mat = session.get(MaterialType, t.mat_type_id)
                    if mat:
                        mat_code = mat.code

                rows.append(
                    {
                        "id": t.id,
                        "file_name": t.file_name,
                        "sheet_qty": t.sheet_qty or "-",
                        "status": t.status.value,
                        "mat": mat_code,
                    }
                )

            self.unassigned_table = ui.table(
                columns=columns,
                rows=rows,
                selection="multiple",
                on_select=self._handle_selection_change,
            ).classes("w-full")
        else:
            ui.label("Все задачи назначены или батчированы").classes("text-slate-500")

    def _handle_selection_change(self, e):
        """Show/hide merge button based on selection."""
        # Store selected IDs for later use
        self._selected_unassigned_ids = []
        if e.selection:
            # Handle both dict and row object
            for item in e.selection:
                if hasattr(item, "id"):
                    self._selected_unassigned_ids.append(item.id)
                elif isinstance(item, dict) and "id" in item:
                    self._selected_unassigned_ids.append(item["id"])

        if hasattr(self, "_selected_unassigned_ids") and self._selected_unassigned_ids:
            self.merge_button.classes(remove="hidden")
        else:
            self.merge_button.classes(add="hidden")

    async def _create_manual_batch(self) -> None:
        """Создает батч из выбранных задач вручную."""
        # Use stored selection from handler
        if not hasattr(self, "_selected_unassigned_ids") or not self._selected_unassigned_ids:
            NotifyHelper.warning("Выберите задачи для создания батча")
            return

        selected_ids = self._selected_unassigned_ids
        async with self.scope() as req:
            session = await req.get(Session)
            engine = BatchEngine(session)
            batch_id = engine.create_batch(selected_ids)
            NotifyHelper.success(f"Создан ручной батч {batch_id[:8]}...")
        self.render.refresh()

    async def _render_unassigned_panel(self, req) -> None:
        """Панель неназначенных задач."""
        tb_system = await req.get(TaskBoardSystem)
        unassigned = tb_system.get_unassigned_tasks(self.filter_work_item_id)

        if not unassigned:
            with ui.card().classes("w-full p-8 text-center"):
                ui.icon("check_circle").classes("text-6xl text-green-300 mb-4")
                ui.label("Все задачи назначены").classes("text-h6 text-slate-500")
            return

        for task in unassigned:
            with ui.card().classes("w-full mb-2 p-4"):
                with ui.row().classes("items-center justify-between"):
                    with ui.column():
                        ui.label(task.file_name).classes("font-medium")
                        ui.label(f"Листов: {task.sheet_qty or '-'}").classes(
                            "text-sm text-slate-500"
                        )

                    StatusBadge(task.status).render()

                    tid = task.id
                    ui.button(
                        "📥 Взять в корзину",
                        on_click=partial(self._assign_task_to_node, tid),
                    ).props("size=sm color=blue")

    async def _run_auto_batching(self) -> None:
        """Запускает авто-батчинг."""
        async with self.scope() as req:
            session = await req.get(Session)
            tb_system = await req.get(TaskBoardSystem)
            engine = BatchEngine(session)
            unassigned = tb_system.get_unassigned_tasks(self.filter_work_item_id)

            if not unassigned:
                NotifyHelper.info("Нет задач для батчина")
                return

            groups = engine.compute(unassigned)
            engine.apply_batches(groups)
            NotifyHelper.success(f"Создано {len(groups)} батчей")
        self.render.refresh()

    async def _assign_task_to_node(self, task_id: int) -> None:
        """Назначает задачу (и весь её батч) на узел оператора."""
        async with self.scope() as req:
            session = await req.get(Session)
            tb_system = await req.get(TaskBoardSystem)
            task = session.get(TaskItem, task_id)
            if task:
                # Assign single ID if no batch is formed
                batch_id = task.batch_group_id or f"single_{task.id}"
                if not task.batch_group_id:
                    task.batch_group_id = batch_id
                    session.add(task)
                    session.commit()

                await tb_system.lock_batch(
                    batch_group_id=batch_id, node_id=self.node_id, operator=self.user
                )
                NotifyHelper.success(f"Батч назначен на {self.node_id} (Worker: {self.user})")
        self.render.refresh()

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def _group_by_batch(
        self, session, entries: list[WorkerBucketEntry]
    ) -> dict[str, list[TaskItem]]:
        """Группирует записи по batch_group_id."""
        batches: dict[str, list[TaskItem]] = {}

        for entry in entries:
            task = session.get(TaskItem, entry.task_item_id)
            if task:
                batch_id = entry.batch_group_id or f"single_{task.id}"
                if batch_id not in batches:
                    batches[batch_id] = []
                batches[batch_id].append(task)

        return batches
