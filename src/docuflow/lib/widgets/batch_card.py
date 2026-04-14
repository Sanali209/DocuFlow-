"""
BatchCard — карточка батча для отображения в корзине оператора.

Показывает: материал, количество листов, estimated_minutes, drift%.
"""

from typing import Any

from nicegui import ui

from docuflow.domain.entities.production import TaskItem, TaskItemStatus, WorkLog, WorkLogType
from docuflow.lib.base_widget import BaseDocuWidget


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
        system_provider: Any — провайдер систем для динамического разрешения
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
        node_id: str = "LASER_1",
        user: str = "admin",
        system_provider: Any = None,
        on_start=None,
        on_pause=None,
        on_resume=None,
        on_complete=None,
        on_block=None,
    ):
        super().__init__(system_provider)
        self.batch_group_id = batch_group_id
        self.tasks = tasks
        self.drift_percent = drift_percent
        self.session = session
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
                    if self.session:
                        self._render_batch_stock_alert()

                with ui.row().classes("items-center gap-2"):
                    # Task Magnet (Suggestions)
                    ui.button(icon="auto_awesome", on_click=self._show_matching_suggestions).props(
                        "flat round color=indigo-400 size=sm"
                    )
                    ui.tooltip("Найти задачи с таким же материалом")

                    # Logistics Request Button
                    ui.button(icon="local_shipping", on_click=self._request_material).props(
                        "flat round color=orange-400 size=sm"
                    ).classes("animate-bounce")
                    ui.tooltip("Запросить подачу металла со склада")

                    self._render_drift_badge()

            # Статистика
            with ui.row().classes("gap-4 mb-4 text-gray-600"):
                ui.label(f"Листов: {completed_sheets}/{total_sheets}")
                ui.label(f"⏱ {estimated_minutes} мин")

            # Прогресс-бар
            progress = completed_sheets / total_sheets if total_sheets > 0 else 0
            ui.linear_progress(value=progress).props("stripe color=green").classes("mb-4")

            # Список задач
            for task in self.tasks:
                TaskItemRow(
                    task=task,
                    session=self.session,
                    on_start=self.on_start,
                    on_pause=self.on_pause,
                    on_resume=self.on_resume,
                    on_complete=self.on_complete,
                    on_block=self.on_block,
                ).render()

    def _render_optimization_monitor(self) -> None:
        """Автоматически проверяет наличие похожих задач и выводит алерт."""

        async def check_and_render(container):
            from docuflow.features.task_board.system import TaskBoardSystem

            try:
                system = await self.get_system(TaskBoardSystem)
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
                            "w-full items-center justify-between bg-indigo-900/20 p-2 mb-2 rounded border border-indigo-500/30 animate-pulse"
                        ):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("auto_awesome", color="indigo-400")
                                ui.label(
                                    f"Оптимизация: в очереди еще {len(matches)} задач под этот металл"
                                ).classes("text-xs font-bold text-indigo-300")
                            ui.button("ЗАБРАТЬ", on_click=self._show_matching_suggestions).props(
                                "size=xs color=indigo unelevated rounded"
                            )
            except Exception:
                pass  # Silent fail for background check

        monitor_container = ui.column().classes("w-full")
        ui.timer(0.5, lambda: check_and_render(monitor_container), once=True)

    def _show_matching_suggestions(self) -> None:
        """Показывает диалог с подходящими задачами."""

        async def load_and_show():
            from docuflow.features.task_board.system import TaskBoardSystem

            try:
                system = await self.get_system(TaskBoardSystem)
                if not self.tasks:
                    return

                first_task = self.tasks[0]
                matches = system.get_matching_unassigned_tasks(
                    first_task.mat_type_id, first_task.thickness
                )

                if not matches:
                    ui.notify("Похожих задач в очереди нет", type="info")
                    return

                with ui.dialog() as dialog, ui.card().classes("p-6 w-[500px]"):
                    ui.label("🧲 Подходящие задачи").classes("text-h6 mb-2")
                    ui.label(
                        "Эти задачи используют такой же материал. Вы можете забрать их себе."
                    ).classes("text-sm text-gray-500 mb-4")

                    with ui.column().classes("w-full gap-2"):
                        for task in matches:
                            with ui.row().classes(
                                "w-full items-center justify-between p-2 bg-gray-50 rounded border border-gray-100"
                            ):
                                with ui.column().classes("gap-0"):
                                    ui.label(task.file_name).classes("font-bold text-sm")
                                    ui.label(f"Листов: {task.sheet_qty}").classes(
                                        "text-[10px] text-gray-400"
                                    )

                                ui.button(
                                    icon="add_circle",
                                    on_click=lambda t=task: self._pull_suggested_task(t, dialog),
                                ).props("flat color=green")

                    with ui.row().classes("w-full justify-end mt-4"):
                        ui.button("Закрыть", on_click=dialog.close).props("flat")
                dialog.open()
            except Exception as e:
                ui.notify(f"Ошибка загрузки предложений: {e}", type="negative")

        ui.timer(0, load_and_show, once=True)

    async def _pull_suggested_task(self, task, dialog) -> None:
        """Забирает предложенную задачу на текущий узел."""

        async def do_pull():
            from docuflow.features.task_board.system import TaskBoardSystem

            system = await self.get_system(TaskBoardSystem)
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

            ui.notify(f"Запрос на подачу отправлен: {self._get_material_type()}", type="warning")
            if self.tasks:
                import datetime

                log = WorkLog(
                    work_item_id=self.tasks[0].work_item_id,
                    task_item_id=self.tasks[0].id,
                    log_type=WorkLogType.STATUS_CHANGE.value,
                    message=f"Запрошена логистика: {message}",
                    author=self.user,
                    created_at=datetime.datetime.now(),
                    node_id=self.node_id,
                )
                self.session.add(log)
                self.session.commit()

        self.safe_action(do_request, error_prefix="Ошибка отправки запроса")

    def _render_batch_stock_alert(self) -> None:
        """Check and render batch-level stock alerts."""
        from docuflow.features.task_board.batch_engine import BatchEngine

        engine = BatchEngine(self.session)
        alerts = engine.check_stock_alerts(self.tasks)

        if alerts:
            with ui.row().classes(
                "items-center gap-1 text-orange-600 bg-orange-50 px-2 rounded-full"
            ):
                ui.icon("inventory_2", size="xs")
                ui.label("STOCK_ALERT").classes("text-[10px] font-bold")
                ui.tooltip(f"В запасе найдены детали: {', '.join(a.sku for a in alerts[:3])}...")

    def _get_material_type(self) -> str:
        """Получает тип материала из первой задачи."""
        if self.tasks:
            first_task = self.tasks[0]
            return getattr(first_task, "mat_type", first_task.file_name or "Батч")
        return "Пустой батч"

    def _render_drift_badge(self) -> None:
        """Рендерит бейдж drift% с цветовой кодировкой."""
        drift = self.drift_percent
        color = "green" if drift < 0 else "yellow" if drift < 20 else "red"
        label = f"{'+' if drift >= 0 else ''}{drift:.1f}%"
        ui.badge(label).props(f"color={color}")


class TaskItemRow:
    """
    Строка задачи с прогресс-баром и кнопками действий.
    """

    def __init__(
        self,
        task: TaskItem,
        session=None,
        on_start=None,
        on_pause=None,
        on_resume=None,
        on_complete=None,
        on_block=None,
    ):
        self.task = task
        self.session = session
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_complete = on_complete
        self.on_block = on_block

    def render(self) -> None:
        """Рендерит строку задачи."""
        with ui.row().classes("items-center gap-2 mb-2 p-2 bg-gray-50 rounded w-full"):
            self._render_part_preview()
            from .status_badge import StatusBadge

            StatusBadge(self.task.status, size="sm").render()

            with ui.column().classes("flex-grow truncate gap-0"):
                ui.label(self.task.file_name).classes("truncate font-medium")
                if self.session:
                    self._render_task_stock_alert()

            progress = self.task.sheets_done / (self.task.sheet_qty or 1)
            ui.linear_progress(value=progress).props("stripe").classes("w-32")
            ui.label(f"{self.task.sheets_done}/{self.task.sheet_qty}").classes(
                "text-sm text-gray-600"
            )
            self._render_action_buttons()

    def _render_task_stock_alert(self) -> None:
        """Check and render task-specific stock alerts."""
        from docuflow.features.task_board.batch_engine import BatchEngine

        engine = BatchEngine(self.session)
        alerts = engine.check_stock_alerts([self.task])
        if alerts:
            with ui.row().classes("items-center gap-1 text-orange-600"):
                ui.icon("inventory_2", size="xs")
                ui.label(f"В запасе: {', '.join(a.sku for a in alerts)}").classes("text-[10px]")

    def _render_action_buttons(self) -> None:
        """Рендерит кнопки действий."""
        status = self.task.status
        if status == TaskItemStatus.PLANNED and self.on_start:
            ui.button("▶ Начать", on_click=lambda: self.on_start(self.task.id)).props(
                "size=sm color=green"
            )
        elif status == TaskItemStatus.IN_PROGRESS:
            if self.on_pause:
                ui.button("⏸ Пауза", on_click=lambda: self.on_pause(self.task.id)).props(
                    "size=sm color=orange"
                )
            if self.on_complete:
                ui.button("✅ Завершить", on_click=lambda: self.on_complete(self.task.id)).props(
                    "size=sm color=green"
                )
        elif status == TaskItemStatus.ON_HOLD and self.on_resume:
            ui.button("▶ Возобновить", on_click=lambda: self.on_resume(self.task.id)).props(
                "size=sm color=green"
            )

        if (
            status not in (TaskItemStatus.DONE, TaskItemStatus.CANCELLED, TaskItemStatus.BLOCKED)
            and self.on_block
        ):
            ui.button("🔒", on_click=lambda: self.on_block(self.task.id)).props(
                "size=sm color=red flat"
            )

    def _render_part_preview(self) -> None:
        """Рендерит миниатюру детали."""
        if self.task.parts:
            from .part_preview import PartPreview

            PartPreview(self.task.parts[0], size="sm").render()
        else:
            ui.icon("extension").classes("text-2xl text-gray-300 w-8 h-8")
