"""
BatchCard — карточка батча для отображения в корзине оператора.

Показывает: материал, количество листов, estimated_minutes, drift%.
"""

from typing import Any

from loguru import logger
from nicegui import ui

from docuflow.domain.entities.production import TaskItem, TaskItemStatus, WorkLog, WorkLogType
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.ui_utils import NotifyHelper, get_action_color


class BatchCard(BaseDocuWidget):
    """
    Карточка батча с задачами внутри.

    Props:
        batch_group_id: str — ID батча
        tasks: list[TaskItem] — задачи в батче
        drift_percent: float — отклонение от оценки (%)
        session: Session — сессия БД для проверки STOCK_ALERT
        node_id: str — ID узла (лазера)
        user: str — текущий пользователь
        system_scope: Any — провайдер систем для динамического разрешения
        on_start: callable — callback для кнопки "Начать"
        on_pause: callable — callback для кнопки "Пауза"
        on_resume: callable — callback для кнопки "Возобновить"
        on_complete: callable — callback для кнопки "Завершить"
        on_block: callable — callback для кнопки "Заблокировать"
    """

    def __init__(
        self,
        batch_group_id: str,
        tasks: list[TaskItem],
        drift_percent: float = 0.0,
        session=None,
        node_id: str | None = None,
        user: str = "admin",
        system_scope: Any = None,
        on_start=None,
        on_pause=None,
        on_resume=None,
        on_complete=None,
        on_block=None,
    ):
        super().__init__(system_scope)
        self.batch_group_id = batch_group_id
        self.tasks = tasks
        self.drift_percent = drift_percent
        self.node_id = node_id
        self.user = user
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_complete = on_complete
        self.on_block = on_block

    def render(self) -> None:
        """Рендерит карточку батча."""
        if not self.tasks:
            return

        # Вычисляем общую информацию
        mat_type = self._get_material_type()
        total_sheets = sum(t.sheet_qty or 0 for t in self.tasks)
        estimated_minutes = sum(t.estimated_minutes or 0 for t in self.tasks)
        completed_sheets = sum(t.sheets_done or 0 for t in self.tasks)

        with ui.card().classes("w-full mb-4 p-4"):
            # --- PROACTIVE OPTIMIZATION MONITOR ---
            self._render_optimization_monitor()

            # Заголовок батча
            with ui.row().classes("items-center justify-between mb-2 w-full"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(f"📦 {mat_type}").classes("text-h6")
                    # Stock Alert Indicator
                    self._render_batch_stock_alert()

                with ui.row().classes("items-center gap-2"):
                    # Task Magnet (Suggestions)
                    ui.button(icon="auto_awesome", on_click=self._show_matching_suggestions).props(
                        "flat round color=teal-400 size=sm"
                    )
                    ui.tooltip("Find tasks with same material")

                    # Logistics Request Button
                    ui.button(icon="local_shipping", on_click=self._request_material).props(
                        "flat round color=orange-400 size=sm"
                    )
                    ui.tooltip("Request material from warehouse")

                    self._render_drift_badge()

            # Статистика
            with ui.row().classes("gap-4 mb-4 text-gray-300"):
                ui.label(f"Листов: {completed_sheets}/{total_sheets}").classes("text-gray-300")
                ui.label(f"⏱ {estimated_minutes} мин").classes("text-gray-300")

            # Прогресс-бар
            progress = completed_sheets / total_sheets if total_sheets > 0 else 0
            ui.linear_progress(value=progress).props("stripe color=green").classes("mb-4")

            # Список задач
            for task in self.tasks:
                TaskItemRow(
                    task=task,
                    on_start=self.on_start,
                    on_pause=self.on_pause,
                    on_resume=self.on_resume,
                    on_complete=self.on_complete,
                    on_block=self.on_block,
                    system_scope=self.system_scope,
                ).render()

    def _render_optimization_monitor(self) -> None:
        """Автоматически проверяет наличие похожих задач и выводит алерт."""

        async def check_and_render(container):
            from docuflow.features.task_board.system import TaskBoardSystem

            try:
                async with self.scope() as req:
                    system = await req.get(TaskBoardSystem)
                    if not self.tasks:
                        return

                    first_task = self.tasks[0]
                    if not first_task.mat_type_id:
                        return

                    matches = system.get_matching_unassigned_tasks(
                        first_task.mat_type_id, first_task.thickness
                    )

                    if matches:
                        with container:
                            with ui.row().classes(
                                "w-full items-center justify-between bg-teal-900/20 p-2 mb-2 rounded border border-teal-500/30"
                            ):
                                with ui.row().classes("items-center gap-2"):
                                    ui.icon("auto_awesome", color="teal-400")
                                    ui.label(
                                        f"Optimisation: {len(matches)} tasks in queue for this metal"
                                    ).classes("text-xs font-bold text-teal-300")
                                ui.button("CLAIM", on_click=self._show_matching_suggestions).props(
                                    "size=xs color=teal unelevated rounded"
                                )
            except Exception:
                logger.debug("Batch optimization check failed, ignoring")

        monitor_container = ui.column().classes("w-full")
        ui.timer(0.5, lambda: check_and_render(monitor_container), once=True)

    def _show_matching_suggestions(self) -> None:
        """Показывает диалог с подходящими задачами."""

        async def load_and_show():
            from docuflow.features.task_board.system import TaskBoardSystem

            try:
                async with self.scope() as req:
                    system = await req.get(TaskBoardSystem)
                    if not self.tasks:
                        return

                    first_task = self.tasks[0]
                    matches = system.get_matching_unassigned_tasks(
                        first_task.mat_type_id, first_task.thickness
                    )

                    if not matches:
                        NotifyHelper.info("Похожих задач в очереди нет")
                        return

                    with ui.dialog() as dialog, ui.card().classes("p-6 w-[500px]"):
                        ui.label("🧲 Подходящие задачи").classes("text-h6 mb-2")
                        ui.label(
                            "Эти задачи используют такой же материал. Вы можете забрать их себе."
                        ).classes("text-sm text-slate-400 mb-4")

                        with ui.column().classes("w-full gap-2"):
                            for task in matches:
                                with ui.row().classes(
                                    "w-full items-center justify-between p-2 bg-gray-50 rounded border border-gray-100"
                                ):
                                    with ui.column().classes("gap-0"):
                                        ui.label(task.file_name).classes(
                                            "font-bold text-sm text-gray-200"
                                        )
                                        ui.label(f"Листов: {task.sheet_qty}").classes(
                                            "text-[10px] text-slate-400"
                                        )

                                    ui.button(
                                        icon="add_circle",
                                        on_click=lambda t=task: self._pull_suggested_task(t, dialog),
                                    ).props("flat color=green")

                        with ui.row().classes("w-full justify-end mt-4"):
                            ui.button("Закрыть", on_click=dialog.close).props("flat")
                    dialog.open()
            except Exception as e:
                NotifyHelper.error(f"Ошибка загрузки предложений: {e}")

        ui.timer(0, load_and_show, once=True)

    async def _pull_suggested_task(self, task, dialog) -> None:
        """Забирает предложенную задачу на текущий узел."""

        async def do_pull():
            from docuflow.features.task_board.system import TaskBoardSystem

            async with self.scope() as req:
                system = await req.get(TaskBoardSystem)
                await system.assign_task_to_node(task.id, self.node_id, self.user)
            dialog.close()
            # Trigger global refresh via JS for now
            ui.run_javascript("window.location.reload()")

        self.safe_action(do_pull, f"Задача {task.file_name} добавлена в очередь", "Ошибка захвата")

    def _request_material(self) -> None:
        """Отправляет запрос на склад (через инциденты/логистику)."""

        async def do_request():
            wi_name = "Батч"
            if self.tasks and hasattr(self.tasks[0], "work_item") and self.tasks[0].work_item:
                wi_name = self.tasks[0].work_item.folder_name

            message = f"[LOGISTICS_REQUEST] Требуется подача металла для {wi_name} на {self.node_id}. Оператор: {self.user}"

            NotifyHelper.warning(f"Запрос на подачу отправлен: {self._get_material_type()}")
            if self.tasks:
                import datetime

                from sqlmodel import Session

                async with self.scope() as req:
                    session = await req.get(Session)
                    log = WorkLog(
                        work_item_id=self.tasks[0].work_item_id,
                        task_item_id=self.tasks[0].id,
                        log_type=WorkLogType.STATUS_CHANGE.value,
                        message=f"Запрошена логистика: {message}",
                        author=self.user,
                        created_at=datetime.datetime.now(),
                        node_id=self.node_id,
                    )
                    session.add(log)
                    session.commit()

        self.safe_action(do_request, error_prefix="Ошибка отправки запроса")

    def _render_batch_stock_alert(self) -> None:
        """Check and render batch-level stock alerts."""

        async def check_alerts(container):
            from sqlmodel import Session

            from docuflow.features.task_board.batch_engine import BatchEngine

            async with self.scope() as req:
                session = await req.get(Session)
                engine = BatchEngine(session)
                alerts = engine.check_stock_alerts(self.tasks)

                if alerts:
                    with container:
                        with ui.row().classes(
                            "items-center gap-1 text-orange-600 bg-orange-50 px-2 rounded-full"
                        ):
                            ui.icon("inventory_2", size="xs")
                            ui.label("STOCK_ALERT").classes("text-[10px] font-bold")
                            ui.tooltip(
                                f"В запасе найдены детали: {', '.join(a.sku for a in alerts[:3])}..."
                            )

        container = ui.row().classes("items-center gap-1")
        ui.timer(0.1, lambda: check_alerts(container), once=True)

    def _get_material_type(self) -> str:
        """Получает тип материала из первой задачи."""
        if self.tasks:
            first_task = self.tasks[0]
            return getattr(first_task, "mat_type", first_task.file_name or "Батч")
        return "Пустой батч"

    def _render_drift_badge(self) -> None:
        """Рендерит бейдж drift% с цветовой кодировкой."""
        from docuflow.lib.widgets.ui_utils import get_kpi_color

        drift = self.drift_percent
        color = get_kpi_color(drift)
        label = f"{'+' if drift >= 0 else ''}{drift:.1f}%"
        ui.badge(label).props(f"color={color}")


class TaskItemRow:
    """
    Строка задачи с прогресс-баром и кнопками действий.
    """

    def __init__(
        self,
        task: TaskItem,
        on_start=None,
        on_pause=None,
        on_resume=None,
        on_complete=None,
        on_block=None,
        system_scope: Any = None,
    ):
        self.task = task
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_complete = on_complete
        self.on_block = on_block
        self.system_scope = system_scope

    def render(self) -> None:
        """Рендерит строку задачи."""
        with ui.row().classes("items-center gap-2 mb-2 p-2 bg-gray-50 rounded w-full"):
            self._render_part_preview()
            from .status_badge import StatusBadge

            StatusBadge(self.task.status, size="sm").render()

            with ui.column().classes("flex-grow truncate gap-0"):
                ui.label(self.task.file_name).classes("truncate font-medium text-gray-200")
                self._render_task_stock_alert()

            progress = self.task.sheets_done / (self.task.sheet_qty or 1)
            ui.linear_progress(value=progress).props("stripe").classes("w-32")
            ui.label(f"{self.task.sheets_done}/{self.task.sheet_qty}").classes(
                "text-sm text-gray-300"
            )
            self._render_action_buttons()

    def _render_task_stock_alert(self) -> None:
        """Check and render task-specific stock alerts."""

        async def check_alerts(container):
            from sqlmodel import Session

            from docuflow.features.task_board.batch_engine import BatchEngine

            async with self.system_scope() as req:
                session = await req.get(Session)
                engine = BatchEngine(session)
                alerts = engine.check_stock_alerts([self.task])
                if alerts:
                    with container:
                        with ui.row().classes("items-center gap-1 text-orange-600"):
                            ui.icon("inventory_2", size="xs")
                            ui.label(f"В запасе: {', '.join(a.sku for a in alerts)}").classes(
                                "text-[10px]"
                            )

        container = ui.row().classes("items-center gap-1")
        ui.timer(0.1, lambda: check_alerts(container), once=True)

    def _render_action_buttons(self) -> None:
        """Рендерит кнопки действий."""
        status = self.task.status
        if status == TaskItemStatus.PLANNED and self.on_start:
            ui.button("▶ Начать", on_click=lambda: self.on_start(self.task.id)).props(
                f"size=sm color={get_action_color('start')}"
            )
        elif status == TaskItemStatus.IN_PROGRESS:
            if self.on_pause:
                ui.button("⏸ Пауза", on_click=lambda: self.on_pause(self.task.id)).props(
                    f"size=sm color={get_action_color('pause')}"
                )
            if self.on_complete:
                ui.button("✅ Завершить", on_click=lambda: self.on_complete(self.task.id)).props(
                    f"size=sm color={get_action_color('complete')}"
                )
        elif status == TaskItemStatus.ON_HOLD and self.on_resume:
            ui.button("▶ Возобновить", on_click=lambda: self.on_resume(self.task.id)).props(
                f"size=sm color={get_action_color('resume')}"
            )

        if (
            status not in (TaskItemStatus.DONE, TaskItemStatus.CANCELLED, TaskItemStatus.BLOCKED)
            and self.on_block
        ):
            ui.button("🔒", on_click=lambda: self.on_block(self.task.id)).props(
                f"size=sm color={get_action_color('block')} flat"
            )

    def _render_part_preview(self) -> None:
        """Рендерит миниатюру детали."""
        if self.task.parts:
            from .part_preview import PartPreview

            PartPreview(self.task.parts[0], size="sm").render()
        else:
            ui.icon("extension").classes("text-2xl text-gray-300 w-8 h-8")
