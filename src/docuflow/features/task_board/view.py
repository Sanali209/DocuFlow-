"""
TaskBoardView — главный экран task board для оператора и бригадира.

Вид Оператора: корзина, батчи, прогресс, статусы.
Вид Бригадира: все узлы, батчинг инструменты, приоритеты.
"""

from typing import Any

from nicegui import ui
from sqlmodel import Session, select

from docuflow.domain.entities.production import (
    TaskItem,
    TaskItemStatus,
    WorkerBucketEntry,
)
from docuflow.features.core.views import ViewInfo, ViewRegistry
from docuflow.features.task_board.batch_engine import BatchEngine
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.features.view_presets.system import ViewPresetSystem
from docuflow.lib.widgets import StatusBadge
from docuflow.lib.widgets.bucket_panel import BucketPanel


def register_task_board_view():
    """Register the task board view in the global registry."""
    from docuflow.features.admin.system import AdminSystem

    ViewRegistry.register(
        ViewInfo(
            name="task_board",
            label="Task Board",
            icon="assignment",
            render_fn=TaskBoardView,
            dependencies=[Session, TaskBoardSystem, ViewPresetSystem, AdminSystem],
            pass_user=True,
            pass_system_provider=True,
        )
    )


class TaskBoardView:
    """
    Главный экран Task Board.

    Props:
        session: Session — сессия БД
        system: TaskBoardSystem — система управления задачами
        preset_system: ViewPresetSystem — система пресетов
        admin_system: Any — система администрирования
        user: str — текущий пользователь
        node_id: str — ID узла (лазера)
        role: str — роль: "operator" или "foreman"
        filter_work_item_id: int | None — фильтр по наряду
        system_provider: Any — провайдер для свежих систем
    """

    def __init__(
        self,
        session: Session,
        system: TaskBoardSystem,
        preset_system: ViewPresetSystem,
        admin_system: Any = None,
        user: str = "admin",
        node_id: str = "LASER_1",
        role: str = "operator",
        filter_work_item_id: int | None = None,
        system_provider: Any = None,
    ):
        self.session = session
        self.system = system
        self.preset_system = preset_system
        self.admin_system = admin_system
        self.user = user
        self.node_id = node_id
        self.role = role
        self.filter_work_item_id = filter_work_item_id
        self.system_provider = system_provider

    @ui.refreshable
    def render(self) -> None:
        """Рендерит основной view."""
        with ui.column().classes("w-full p-4"):
            # Переключатель роли
            self._render_role_switcher()

            if self.role == "operator":
                self._render_operator_view()
            else:
                self._render_foreman_view()

    def _render_role_switcher(self) -> None:
        """Рендерит переключатель роли."""
        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label("Роль:").classes("text-gray-600")
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
        self.filter_work_item_id = None
        self.render.refresh()

    def _switch_role(self, role: str) -> None:
        """Переключает роль."""
        self.role = role
        self.render.refresh()

    # ==================== ВИД ОПЕРАТОРА ====================

    def _render_operator_view(self) -> None:
        """Рендерит вид оператора."""
        with ui.column().classes("w-full gap-4"):
            # Выбираем узел
            self._render_node_selector()

            # Корзина оператора
            BucketPanel(
                session=self.session,
                system=self.system,
                node_id=self.node_id,
                user=self.user,
                system_provider=self.system_provider,
            ).render()

            # Передача смены
            with ui.row().classes("w-full justify-end mt-4"):
                ui.button(
                    "Сдать смену", icon="swap_horiz", on_click=self._show_handover_dialog
                ).props("color=orange rounded-xl")

    def _show_handover_dialog(self):
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[400px] gap-4"):
            ui.label("Сдача смены").classes("text-xl font-bold text-orange-400")
            recv_operator = (
                ui.input("Имя сменщика (кому передать)")
                .props("dark standout rounded")
                .classes("w-full")
            )
            note = (
                ui.textarea("Заметка по работе / материалу")
                .props("dark standout rounded")
                .classes("w-full")
            )
            with ui.row().classes("w-full justify-between items-center"):
                ui.button("Отмена", on_click=dialog.close).props("flat text-color=slate-400")
                ui.button(
                    "ПОДТВЕРДИТЬ СДАЧУ",
                    on_click=lambda: self._execute_handover(
                        recv_operator.value, note.value, dialog
                    ),
                ).props("color=orange rounded-xl").classes("font-bold")
        dialog.open()

    def _execute_handover(self, recv_operator: str, note: str, dialog):
        if not recv_operator:
            ui.notify("Укажите кому сдаете смену", type="warning")
            return
        self.system.handover(
            self.node_id, recv_operator, str(note) if note else "Смена закрыта без комментариев"
        )
        ui.notify("Смена успешно передана", type="positive")
        dialog.close()
        self.render.refresh()

    def _render_node_selector(self) -> None:
        """Рендерит выбор узла."""
        nodes = self._get_available_nodes()

        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label("Рабочее место:").classes("text-gray-600")
            ui.select(
                options={n: n for n in nodes},
                value=self.node_id,
                on_change=lambda e: self._select_node(e.value),
            ).classes("w-48")

    def _select_node(self, node_id: str) -> None:
        """Выбирает узел и проверяет заметки о передаче смены."""
        self.node_id = node_id

        # Проверка заметок о передаче смены
        bucket_entries = self.system.get_bucket(node_id)
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
                    self.session.add(e)
            self.session.commit()

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

    def _render_foreman_view(self) -> None:
        """Рендерит вид бригадира."""
        # Если есть фильтр наряда, открываем вкладку 'Неназначенные' по умолчанию
        default_tab_name = "Неназначенные" if self.filter_work_item_id else "Все узлы"

        with ui.tabs().classes("w-full mb-4") as tabs:
            all_nodes_tab = ui.tab("Все узлы")
            batching_tab = ui.tab("Батчинг")
            unassigned_tab = ui.tab("Неназначенные")

        with ui.tab_panels(tabs, value=default_tab_name).classes("w-full"):
            with ui.tab_panel(all_nodes_tab):
                self._render_all_nodes_panel()

            with ui.tab_panel(batching_tab):
                self._render_batching_panel()

            with ui.tab_panel(unassigned_tab):
                self._render_unassigned_panel()

    def _render_all_nodes_panel(self) -> None:
        """Панель всех узлов."""
        nodes = self._get_available_nodes()

        for node_id in nodes:
            # Получаем батчи и задачи для расчета KPI
            bucket_entries = self.system.get_bucket(node_id)
            batches = self._group_by_batch(bucket_entries)

            # Расчет среднего Drift % по узлу
            node_drift = self._calculate_node_drift(bucket_entries)

            with (
                ui.card()
                .classes("w-full mb-4 p-4 border-l-4")
                .style(f"border-color: {self._status_color(self._get_node_status(node_id))}")
            ):
                with ui.row().classes("items-center justify-between mb-2"):
                    with ui.row().classes("items-center gap-2"):
                        ui.label(f"🔹 {node_id}").classes("text-h6")
                        node_status = self._get_node_status(node_id)
                        ui.badge(node_status).props(f"color={self._status_color(node_status)}")

                    # KPI Drift Badge
                    self._render_kpi_drift(node_drift)

                # Показываем батчи узла
                if batches:
                    for batch_id, tasks in batches.items():
                        with ui.row().classes(
                            "gap-2 items-center ml-4 mb-2 hover:bg-gray-50 p-1 rounded cursor-pointer"
                        ):
                            StatusBadge(tasks[0].status).render() if tasks else None

                            # Deep Link to WorkItem
                            if tasks and tasks[0].work_item_id:
                                ui.link(f"Наряд: {tasks[0].work_item_id}", "#").on(
                                    "click",
                                    lambda t=tasks[0]: self._show_work_item_by_id(t.work_item_id),
                                ).classes("font-bold text-blue-600")

                            ui.label(f"Батч {batch_id[:8]}...").classes("text-sm text-gray-500")
                            ui.label(f"({len(tasks)} задач)").classes("text-xs")
                else:
                    ui.label("Нет активных батчей").classes("text-gray-400 ml-4")

    def _calculate_node_drift(self, bucket_entries: list[WorkerBucketEntry]) -> float:
        """Вычисляет средний Drift % для всех задач на узле."""
        total_estimated = 0
        total_actual = 0
        for entry in bucket_entries:
            task = self.session.get(TaskItem, entry.task_item_id)
            if task and task.status == TaskItemStatus.DONE:
                total_estimated += task.estimated_minutes or 0
                total_actual += task.actual_minutes or 0

        if total_estimated == 0:
            return 0.0
        return (total_actual - total_estimated) / total_estimated * 100

    def _render_kpi_drift(self, drift: float) -> None:
        """Рендерит KPI бейдж отклонения."""
        color = "green" if drift <= 5 else "orange" if drift <= 20 else "red"
        icon = "trending_up" if drift > 0 else "trending_down"

        with ui.row().classes(
            f"items-center gap-1 text-{color}-600 bg-{color}-50 px-2 py-1 rounded-full"
        ):
            ui.icon(icon, size="xs")
            ui.label(f"DRIFT: {drift:.1f}%").classes("text-xs font-bold")
            ui.tooltip("Отклонение фактического времени от планового")

    def _show_work_item_by_id(self, work_item_id: int) -> None:
        """Открывает карточку наряда по ID (Deep Link)."""
        # Resolve WorkItem from session
        from docuflow.domain.entities.production import WorkItem
        from docuflow.features.work_items.system import WorkItemSystem
        from docuflow.lib.widgets.work_item_card import WorkItemCard

        work_item = self.session.get(WorkItem, work_item_id)

        if work_item:
            from docuflow.infrastructure.config import Config

            wi_system = WorkItemSystem(Config(), self.session, None)
            WorkItemCard(
                work_item, wi_system, self.user, system_provider=self.system_provider
            ).render()
        else:
            ui.notify(f"Наряд {work_item_id} не найден", type="negative")

    def _render_batching_panel(self) -> None:
        """Панель батчинга."""
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
        unassigned = self._get_unassigned_tasks()

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

                    mat = self.session.get(MaterialType, t.mat_type_id)
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
            ui.label("Все задачи назначены или батчированы").classes("text-gray-500")

    def _handle_selection_change(self, e):
        """Show/hide merge button based on selection."""
        if e.selection and len(e.selection) >= 1:
            self.merge_button.classes(remove="hidden")
        else:
            self.merge_button.classes(add="hidden")

    def _create_manual_batch(self) -> None:
        """Создает батч из выбранных задач вручную."""
        selected_ids = [row["id"] for row in self.unassigned_table.selection]
        if not selected_ids:
            return

        engine = BatchEngine(self.session)
        batch_id = engine.create_batch(selected_ids)
        ui.notify(f"Создан ручной батч {batch_id[:8]}...", type="positive")
        self.render.refresh()

    def _render_unassigned_panel(self) -> None:
        """Панель неназначенных задач."""
        unassigned = self._get_unassigned_tasks()

        if not unassigned:
            with ui.card().classes("w-full p-8 text-center"):
                ui.icon("check_circle").classes("text-6xl text-green-300 mb-4")
                ui.label("Все задачи назначены").classes("text-h6 text-gray-500")
            return

        for task in unassigned:
            with ui.card().classes("w-full mb-2 p-4"):
                with ui.row().classes("items-center justify-between"):
                    with ui.column():
                        ui.label(task.file_name).classes("font-medium")
                        ui.label(f"Листов: {task.sheet_qty or '-'}").classes(
                            "text-sm text-gray-500"
                        )

                    StatusBadge(task.status).render()

                    ui.button(
                        "📥 Взять в корзину",
                        on_click=lambda t=task: self._assign_task_to_node(t.id),
                    ).props("size=sm color=blue")

    def _run_auto_batching(self) -> None:
        """Запускает авто-батчинг."""
        engine = BatchEngine(self.session)
        unassigned = self._get_unassigned_tasks()

        if not unassigned:
            ui.notify("Нет задач для батчина", type="info")
            return

        groups = engine.compute(unassigned)
        engine.apply_batches(groups)
        ui.notify(f"Создано {len(groups)} батчей", type="positive")
        self.render.refresh()

    async def _assign_task_to_node(self, task_id: int) -> None:
        """Назначает задачу (и весь её батч) на узел оператора."""
        task = self.session.get(TaskItem, task_id)
        if task:
            # Assign single ID if no batch is formed
            batch_id = task.batch_group_id or f"single_{task.id}"
            if not task.batch_group_id:
                task.batch_group_id = batch_id
                self.session.add(task)
                self.session.commit()

            await self.system.lock_batch(
                batch_group_id=batch_id, node_id=self.node_id, operator=self.user
            )
            ui.notify(f"Батч назначен на {self.node_id} (Worker: {self.user})", type="positive")
            self.render.refresh()

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def _get_available_nodes(self) -> list[str]:
        """Получает список доступных узлов из реестра рабочих мест."""
        if self.admin_system:
            workplaces = self.admin_system.get_all_workplaces()
            if workplaces:
                return [w.node_id for w in workplaces]

        # Fallback if no admin system or no workplaces registered yet
        return ["LASER_1", "LASER_2", "LASER_3", "LASER_4"]

    def _get_node_status(self, node_id: str) -> str:
        """Получает статус узла."""
        bucket = self.system.get_bucket(node_id)
        if not bucket:
            return "Свободен"

        tasks = []
        for entry in bucket:
            task = self.session.get(TaskItem, entry.task_item_id)
            if task:
                tasks.append(task)

        if any(t.status == TaskItemStatus.IN_PROGRESS for t in tasks):
            return "Режет"
        elif any(t.status == TaskItemStatus.ON_HOLD for t in tasks):
            return "На паузе"
        else:
            return "Ожидание"

    def _status_color(self, status: str) -> str:
        """Возвращает цвет для статуса узла."""
        colors = {
            "Свободен": "gray",
            "Режет": "green",
            "На паузе": "orange",
            "Ожидание": "blue",
        }
        return colors.get(status, "gray")

    def _get_unassigned_tasks(self) -> list[TaskItem]:
        """Получает неназначенные задачи с учетом фильтра наряда."""
        statement = select(TaskItem).where(
            TaskItem.assigned_to_node.is_(None),
            TaskItem.status.in_([TaskItemStatus.PLANNED, TaskItemStatus.NEW]),
        )

        if self.filter_work_item_id:
            statement = statement.where(TaskItem.work_item_id == self.filter_work_item_id)

        return list(self.session.exec(statement).all())

    def _group_by_batch(self, entries: list[WorkerBucketEntry]) -> dict[str, list[TaskItem]]:
        """Группирует записи по batch_group_id."""
        batches: dict[str, list[TaskItem]] = {}

        for entry in entries:
            task = self.session.get(TaskItem, entry.task_item_id)
            if task:
                batch_id = entry.batch_group_id or f"single_{task.id}"
                if batch_id not in batches:
                    batches[batch_id] = []
                batches[batch_id].append(task)

        return batches
