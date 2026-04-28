"""
Диалоговые окна для корзины оператора.
"""

from typing import Any

from nicegui import ui

from docuflow.domain.entities.production import TaskItem
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.ui_utils import NotifyHelper


class PauseDialog(BaseDocuWidget):
    """Диалог ввода причины паузы."""

    def __init__(
        self,
        task_id: int,
        on_success: Any = None,
        system_scope: Any = None,
    ):
        super().__init__(system_scope)
        self.task_id = task_id
        self.on_success = on_success

    async def render(self) -> None:
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
            NotifyHelper.warning("Укажите причину паузы")
            return

        async def do_confirm():
            async with self.scope() as req:
                system = await req.get(TaskBoardSystem)
                system.pause_task(self.task_id, reason)

                if is_mat_issue:
                    system.report_material_incident(self.task_id, reason)

                if is_breakdown:
                    system.report_material_incident(self.task_id, f"[BREAKDOWN] {reason}")

            dialog.close()
            if self.on_success:
                if hasattr(self.on_success, "refresh") and callable(self.on_success.refresh):
                    await self.on_success.refresh()  # type: ignore[misc]
                elif callable(self.on_success):
                    await self.on_success()  # type: ignore[misc]

        self.safe_action(do_confirm, "Задача поставлена на паузу", "Ошибка")


class CompleteDialog(BaseDocuWidget):
    """Диалог завершения задачи."""

    def __init__(
        self,
        task_id: int,
        on_success: Any = None,
        system_scope: Any = None,
    ):
        super().__init__(system_scope)
        self.task_id = task_id
        self.on_success = on_success

    async def render(self) -> None:
        """Рендерит диалог."""
        from sqlmodel import Session

        async with self.scope() as req:
            session = await req.get(Session)
            task = session.get(TaskItem, self.task_id)

            with ui.dialog() as dialog, ui.card().classes("w-96 p-4"):
                ui.label("✅ Завершить задачу").classes("text-h6 mb-4")

                if task:
                    ui.label(f"Файл: {task.file_name}").classes("mb-2")
                    ui.label(f"План: {task.sheet_qty} листов").classes("mb-4")

                sheets_done = ui.number(
                    "Листов порезано",
                    value=task.sheet_qty if task else 0,
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
            async with self.scope() as req:
                system = await req.get(TaskBoardSystem)
                system.complete_task(
                    self.task_id, sheets_done, qty_produced, create_pallet=create_pallet
                )
            dialog.close()
            if self.on_success:
                if hasattr(self.on_success, "refresh") and callable(self.on_success.refresh):
                    await self.on_success.refresh()  # type: ignore[misc]
                elif callable(self.on_success):
                    await self.on_success()  # type: ignore[misc]

        self.safe_action(do_confirm, "Задача завершена", "Ошибка")


class BlockDialog(BaseDocuWidget):
    """Диалог блокировки задачи."""

    def __init__(
        self,
        task_id: int,
        on_success: Any = None,
        system_scope: Any = None,
    ):
        super().__init__(system_scope)
        self.task_id = task_id
        self.on_success = on_success

    async def render(self) -> None:
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
            NotifyHelper.warning("Укажите причину блокировки")
            return

        async def do_confirm():
            async with self.scope() as req:
                system = await req.get(TaskBoardSystem)
                system.block_task(self.task_id, reason)
            dialog.close()
            if self.on_success:
                if hasattr(self.on_success, "refresh") and callable(self.on_success.refresh):
                    await self.on_success.refresh()  # type: ignore[misc]
                elif callable(self.on_success):
                    await self.on_success()  # type: ignore[misc]

        self.safe_action(do_confirm, "Задача заблокирована", "Ошибка")
