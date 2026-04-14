"""
Диалоговые окна для корзины оператора.
"""

from typing import Any

from nicegui import ui

from docuflow.domain.entities.production import TaskItem
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.lib.base_widget import BaseDocuWidget


class PauseDialog(BaseDocuWidget):
    """Диалог ввода причины паузы."""

    def __init__(
        self,
        task_id: int,
        system: TaskBoardSystem,
        on_success: Any = None,
        system_provider: Any = None,
    ):
        super().__init__(system_provider)
        self.task_id = task_id
        self.system = system
        self.on_success = on_success

    def render(self) -> None:
        """Рендерит диалог."""
        with ui.dialog() as dialog, ui.card().classes("w-96 p-4"):
            ui.label("⏸ Пауза задачи").classes("text-h6 mb-4")

            reason = ui.textarea(
                label="Причина паузы",
                placeholder="Укажите причину...",
            ).classes("w-full mb-4")

            # Чекбокс для сообщения об инциденте с материалом
            mat_issue = ui.checkbox("Проблема с материалом (брак/нехватка)").classes("mb-2")

            # Чекбокс для поломки оборудования
            breakdown_issue = ui.checkbox("Поломка оборудования (BREAKDOWN)").classes("mb-4")

            with ui.row().classes("justify-end gap-2"):
                ui.button("Отмена", on_click=dialog.close).props("flat")
                ui.button(
                    "Подтвердить",
                    on_click=lambda: self._confirm(
                        reason.value, mat_issue.value, breakdown_issue.value, dialog
                    ),
                ).props("color=orange")

        dialog.open()

    def _confirm(self, reason: str, is_mat_issue: bool, is_breakdown: bool, dialog) -> None:
        """Подтверждает паузу и сообщает об инциденте если нужно."""
        if not reason:
            ui.notify("Укажите причину паузы", type="warning")
            return

        async def do_confirm():
            system = await self.get_system(TaskBoardSystem)
            system.pause_task(self.task_id, reason)

            if is_mat_issue:
                system.report_material_incident(self.task_id, reason)

            if is_breakdown:
                system.report_material_incident(self.task_id, f"[BREAKDOWN] {reason}")

            dialog.close()
            if self.on_success:
                self.on_success()

        self.safe_action(do_confirm, "Задача поставлена на паузу", "Ошибка")


class CompleteDialog(BaseDocuWidget):
    """Диалог завершения задачи."""

    def __init__(
        self,
        task_id: int,
        system: TaskBoardSystem,
        on_success: Any = None,
        system_provider: Any = None,
    ):
        super().__init__(system_provider)
        self.task_id = task_id
        self.system = system
        self.on_success = on_success
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

        async def do_confirm():
            system = await self.get_system(TaskBoardSystem)
            system.complete_task(
                self.task_id, sheets_done, qty_produced, create_pallet=create_pallet
            )
            dialog.close()
            if self.on_success:
                self.on_success()

        self.safe_action(do_confirm, "Задача завершена", "Ошибка")


class BlockDialog(BaseDocuWidget):
    """Диалог блокировки задачи."""

    def __init__(
        self,
        task_id: int,
        system: TaskBoardSystem,
        on_success: Any = None,
        system_provider: Any = None,
    ):
        super().__init__(system_provider)
        self.task_id = task_id
        self.system = system
        self.on_success = on_success

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

        async def do_confirm():
            system = await self.get_system(TaskBoardSystem)
            system.block_task(self.task_id, reason)
            dialog.close()
            if self.on_success:
                self.on_success()

        self.safe_action(do_confirm, "Задача заблокирована", "Ошибка")
