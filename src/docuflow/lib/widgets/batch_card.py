"""
BatchCard — карточка батча для отображения в корзине оператора.

Показывает: материал, количество листов, estimated_minutes, drift%.
"""

from nicegui import ui

from docuflow.domain.entities.production import TaskItem, TaskItemStatus


class BatchCard:
    """
    Карточка батча с задачами внутри.

    Props:
        batch_group_id: str — ID батча
        tasks: list[TaskItem] — задачи в батче
        drift_percent: float — отклонение от оценки (%)
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
        on_start=None,
        on_pause=None,
        on_resume=None,
        on_complete=None,
        on_block=None,
    ):
        self.batch_group_id = batch_group_id
        self.tasks = tasks
        self.drift_percent = drift_percent
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_complete = on_complete
        self.on_block = on_block

    def render(self) -> None:
        """Рендерит карточку батча."""
        # Вычисляем общую информацию
        mat_type = self._get_material_type()
        total_sheets = sum(t.sheet_qty or 0 for t in self.tasks)
        estimated_minutes = sum(t.estimated_minutes or 0 for t in self.tasks)
        completed_sheets = sum(t.sheets_done or 0 for t in self.tasks)

        with ui.card().classes("w-full mb-4 p-4"):
            # Заголовок батча
            with ui.row().classes("items-center justify-between mb-2"):
                ui.label(f"📦 {mat_type}").classes("text-h6")
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
                    on_start=self.on_start,
                    on_pause=self.on_pause,
                    on_resume=self.on_resume,
                    on_complete=self.on_complete,
                    on_block=self.on_block,
                ).render()

    def _get_material_type(self) -> str:
        """Получает тип материала из первой задачи."""
        if self.tasks:
            first_task = self.tasks[0]
            # Пытаемся получить из work_item или task_item
            if hasattr(first_task, "work_item") and first_task.work_item:
                return first_task.work_item.mat_type or "Не указан"
            return first_task.file_name or "Батч"
        return "Пустой батч"

    def _render_drift_badge(self) -> None:
        """Рендерит бейдж drift% с цветовой кодировкой."""
        drift = self.drift_percent

        if drift < 0:
            color = "green"
            label = f"{drift:.1f}% ↑"
        elif drift < 20:
            color = "yellow"
            label = f"+{drift:.1f}%"
        else:
            color = "red"
            label = f"+{drift:.1f}% ⚠"

        ui.badge(label).props(f"color={color}")


class TaskItemRow:
    """
    Строка задачи с прогресс-баром и кнопками действий.

    Props:
        task: TaskItem — задача
        on_start, on_pause, on_resume, on_complete, on_block: callbacks
    """

    def __init__(
        self,
        task: TaskItem,
        on_start=None,
        on_pause=None,
        on_resume=None,
        on_complete=None,
        on_block=None,
    ):
        self.task = task
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_complete = on_complete
        self.on_block = on_block

    def render(self) -> None:
        """Рендерит строку задачи."""
        with ui.row().classes("items-center gap-2 mb-2 p-2 bg-gray-50 rounded"):
            # Превью детали (SVG)
            self._render_part_preview()

            # Статус
            # Lazy import
            from .status_badge import StatusBadge

            StatusBadge(self.task.status, size="sm").render()

            # Имя файла
            ui.label(self.task.file_name).classes("flex-grow truncate")

            # Прогресс
            progress = self.task.sheets_done / (self.task.sheet_qty or 1)
            ui.linear_progress(value=progress).props("stripe").classes("w-32")
            ui.label(f"{self.task.sheets_done}/{self.task.sheet_qty}").classes(
                "text-sm text-gray-600"
            )

            # Кнопки действий
            self._render_action_buttons()

    def _render_action_buttons(self) -> None:
        """Рендерит кнопки действий в зависимости от статуса."""
        status = self.task.status

        if status == TaskItemStatus.PLANNED:
            if self.on_start:
                ui.button(
                    "▶ Начать",
                    on_click=lambda: self.on_start(self.task.id),
                ).props("size=sm color=green")

        elif status == TaskItemStatus.IN_PROGRESS:
            if self.on_pause:
                ui.button(
                    "⏸ Пауза",
                    on_click=lambda: self.on_pause(self.task.id),
                ).props("size=sm color=orange")
            if self.on_complete:
                ui.button(
                    "✅ Завершить",
                    on_click=lambda: self.on_complete(self.task.id),
                ).props("size=sm color=green")

        elif status == TaskItemStatus.ON_HOLD:
            if self.on_resume:
                ui.button(
                    "▶ Возобновить",
                    on_click=lambda: self.on_resume(self.task.id),
                ).props("size=sm color=green")

        # Кнопка блокировки (всегда доступна кроме DONE/CANCELLED)
        if status not in (TaskItemStatus.DONE, TaskItemStatus.CANCELLED, TaskItemStatus.BLOCKED):
            if self.on_block:
                ui.button(
                    "🔒",
                    on_click=lambda: self.on_block(self.task.id),
                ).props("size=sm color=red flat")

    def _render_part_preview(self) -> None:
        """Рендерит миниатюру детали (SVG) с помощью глобального виджета."""
        if self.task.parts:
            # Используем глобальный виджет превью
            # Lazy import
            from .part_preview import PartPreview

            PartPreview(self.task.parts[0], size="sm").render()
        else:
            ui.icon("extension").classes("text-2xl text-gray-300 w-8 h-8")
