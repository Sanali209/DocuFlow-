"""
BucketPanel — корзина оператора с батчами.

Отображает все батчи, назначенные оператору на узле.
"""

from nicegui import ui
from sqlmodel import Session

from docuflow.domain.entities.production import (
    TaskItem,
    WorkerBucketEntry,
)
from docuflow.features.task_board.system import TaskBoardSystem


class BucketPanel:
    """
    Панель корзины оператора.

    Props:
        session: Session — сессия БД
        system: TaskBoardSystem — система управления задачами
        node_id: str — ID узла (лазера)
        user: str — текущий пользователь
    """

    def __init__(
        self,
        session: Session,
        system: TaskBoardSystem,
        node_id: str,
        user: str,
    ):
        self.session = session
        self.system = system
        self.node_id = node_id
        self.user = user

    def render(self) -> None:
        """Рендерит панель корзины."""
        bucket_entries = self.system.get_bucket(self.node_id)

        if not bucket_entries:
            self._render_empty_bucket()
            return

        # Группируем по batch_group_id
        batches = self._group_by_batch(bucket_entries)

        with ui.column().classes("w-full"):
            # Заголовок
            with ui.row().classes("items-center justify-between mb-4"):
                ui.label(f"📥 Корзина: {self.user} @ {self.node_id}").classes("text-h6")
                ui.label(f"{len(batches)} батчей").classes("text-gray-500")

        # Карточки батчей
        for batch_group_id, tasks in batches.items():
            drift = self._calculate_batch_drift(tasks)

            # Lazy import
            from .batch_card import BatchCard

            BatchCard(
                batch_group_id=batch_group_id,
                tasks=tasks,
                drift_percent=drift,
                on_start=self._on_start_task,
                on_pause=self._on_pause_task,
                on_resume=self._on_resume_task,
                on_complete=self._on_complete_task,
                on_block=self._on_block_task,
            ).render()

    def _render_empty_bucket(self) -> None:
        """Рендерит пустую корзину."""
        with ui.card().classes("w-full p-8 text-center"):
            ui.icon("inbox").classes("text-6xl text-gray-300 mb-4")
            ui.label("Корзина пуста").classes("text-h6 text-gray-500")
            ui.label("Нет назначенных батчей").classes("text-gray-400")

    def _group_by_batch(self, entries: list[WorkerBucketEntry]) -> dict[str, list[TaskItem]]:
        """
        Группирует записи корзины по batch_group_id.

        Returns:
            dict[batch_group_id, list[TaskItem]]
        """
        batches: dict[str, list[TaskItem]] = {}

        for entry in entries:
            task = self.session.get(TaskItem, entry.task_item_id)
            if task:
                batch_id = entry.batch_group_id or f"single_{task.id}"
                if batch_id not in batches:
                    batches[batch_id] = []
                batches[batch_id].append(task)

        return batches

    def _calculate_batch_drift(self, tasks: list[TaskItem]) -> float:
        """Вычисляет drift для батча."""
        total_estimated = sum(t.estimated_minutes or 0 for t in tasks)
        total_actual = sum(t.actual_minutes or 0 for t in tasks)

        if total_estimated == 0:
            return 0.0

        return (total_actual - total_estimated) / total_estimated * 100

    # === Callbacks ===

    def _on_start_task(self, task_id: int) -> None:
        """Обработчик кнопки 'Начать'."""
        self.system.start_task(task_id)
        ui.notify("Задача начата", type="positive")
        ui.run_javascript("location.reload()")

    def _on_pause_task(self, task_id: int) -> None:
        """Обработчик кнопки 'Пауза' — открывает диалог причины."""
        PauseDialog(task_id, self.system).render()

    def _on_resume_task(self, task_id: int) -> None:
        """Обработчик кнопки 'Возобновить'."""
        self.system.resume_task(task_id)
        ui.notify("Задача возобновлена", type="positive")
        ui.run_javascript("location.reload()")

    def _on_complete_task(self, task_id: int) -> None:
        """Обработчик кнопки 'Завершить' — открывает диалог."""
        CompleteDialog(task_id, self.system).render()

    def _on_block_task(self, task_id: int) -> None:
        """Обработчик кнопки 'Заблокировать' — открывает диалог причины."""
        BlockDialog(task_id, self.system).render()


class PauseDialog:
    """Диалог ввода причины паузы."""

    def __init__(self, task_id: int, system: TaskBoardSystem):
        self.task_id = task_id
        self.system = system

    def render(self) -> None:
        """Рендерит диалог."""
        with ui.dialog() as dialog, ui.card().classes("w-96 p-4"):
            ui.label("⏸ Пауза задачи").classes("text-h6 mb-4")

            reason = ui.textarea(
                label="Причина паузы",
                placeholder="Укажите причину...",
            ).classes("w-full mb-4")

            with ui.row().classes("justify-end gap-2"):
                ui.button("Отмена", on_click=dialog.close).props("flat")
                ui.button(
                    "Подтвердить",
                    on_click=lambda: self._confirm(reason.value, dialog),
                ).props("color=orange")

        dialog.open()

    def _confirm(self, reason: str, dialog) -> None:
        """Подтверждает паузу."""
        if not reason:
            ui.notify("Укажите причину паузы", type="warning")
            return

        self.system.pause_task(self.task_id, reason)
        ui.notify("Задача поставлена на паузу", type="warning")
        dialog.close()
        ui.run_javascript("location.reload()")


class CompleteDialog:
    """Диалог завершения задачи."""

    def __init__(self, task_id: int, system: TaskBoardSystem):
        self.task_id = task_id
        self.system = system
        self.task = system.session.get(TaskItem, task_id)

    def render(self) -> None:
        """Рендерит диалог."""
        with ui.dialog() as dialog, ui.card().classes("w-96 p-4"):
            ui.label("✅ Завершить задачу").classes("text-h6 mb-4")

            if self.task:
                ui.label(f"Файл: {self.task.file_name}").classes("mb-2")
                ui.label(f"План: {self.task.sheet_qty} листов").classes("mb-4")

            sheets_done = ui.number(
                "Листов порезано",
                value=self.task.sheet_qty if self.task else 0,
                min=0,
            ).classes("w-full mb-4")

            qty_produced = ui.number(
                "Деталей произведено",
                value=0,
                min=0,
            ).classes("w-full mb-4")

            create_pallet = ui.checkbox("Создать поддон (паллету)").classes("mb-4")

            with ui.row().classes("justify-end gap-2"):
                ui.button("Отмена", on_click=dialog.close).props("flat")
                ui.button(
                    "Завершить",
                    on_click=lambda: self._confirm(
                        int(sheets_done.value or 0),
                        int(qty_produced.value or 0),
                        create_pallet.value,
                        dialog,
                    ),
                ).props("color=green")

        dialog.open()

    def _confirm(self, sheets_done: int, qty_produced: int, create_pallet: bool, dialog) -> None:
        """Подтверждает завершение."""
        self.system.complete_task(
            self.task_id, sheets_done, qty_produced, create_pallet=create_pallet
        )
        ui.notify("Задача завершена", type="positive")
        dialog.close()
        ui.run_javascript("location.reload()")


class BlockDialog:
    """Диалог блокировки задачи."""

    def __init__(self, task_id: int, system: TaskBoardSystem):
        self.task_id = task_id
        self.system = system

    def render(self) -> None:
        """Рендерит диалог."""
        with ui.dialog() as dialog, ui.card().classes("w-96 p-4"):
            ui.label("🔒 Блокировка задачи").classes("text-h6 mb-4")

            reason = ui.textarea(
                label="Причина блокировки",
                placeholder="Укажите причину...",
            ).classes("w-full mb-4")

            with ui.row().classes("justify-end gap-2"):
                ui.button("Отмена", on_click=dialog.close).props("flat")
                ui.button(
                    "Заблокировать",
                    on_click=lambda: self._confirm(reason.value, dialog),
                ).props("color=red")

        dialog.open()

    def _confirm(self, reason: str, dialog) -> None:
        """Подтверждает блокировку."""
        if not reason:
            ui.notify("Укажите причину блокировки", type="warning")
            return

        self.system.block_task(self.task_id, reason)
        ui.notify("Задача заблокирована", type="warning")
        dialog.close()
        ui.run_javascript("location.reload()")
