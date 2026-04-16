"""
WorkItemCard — детальная карточка наряда (modal).

Отображает метаданные наряда, список задач (TaskItems) и лог событий (WorkLog).
Позволяет совершать действия: регистрация документа, блокировка.
"""

from typing import Any

from nicegui import ui

from docuflow.domain.entities.production import (
    TaskItem,
    WorkItem,
    WorkItemStatus,
    WorkLog,
)
from docuflow.features.work_items.system import WorkItemSystem
from docuflow.lib.base_widget import BaseDocuWidget


class WorkItemCard(BaseDocuWidget):
    """
    Детальная карточка наряда (диалоговое окно).

    Props:
        work_item: WorkItem — объект наряда
        system: WorkItemSystem — система для выполнения действий
        user: str — имя текущего пользователя
        on_navigate: callable — функция переключения экранов
        system_provider: Any — провайдер для свежих систем
    """

    def __init__(
        self,
        work_item: WorkItem,
        system: WorkItemSystem,
        user: str = "admin",
        on_navigate: Any = None,
        system_provider: Any = None,
    ):
        super().__init__(system_provider)
        self.work_item = work_item
        self.system = system
        self.user = user
        self.on_navigate = on_navigate

    def render(self) -> None:
        """Рендерит и открывает диалог с карточкой."""
        with (
            ui.dialog() as dialog,
            ui.card().classes(
                "w-[700px] max-w-none bg-slate-950 border border-slate-800 p-0 overflow-hidden"
            ),
        ):
            # Custom Header
            with ui.row().classes(
                "w-full items-center justify-between p-6 bg-slate-800/60 border-b border-slate-700/50"
            ):
                with ui.row().classes("items-center gap-3"):
                    ui.icon("assignment", size="32px").classes("text-teal-400")
                    with ui.column().classes("gap-0"):
                        ui.label(self.work_item.folder_name).classes("text-xl font-bold text-white")
                        ui.label(
                            f"ID: {self.work_item.id} • {self.work_item.work_item_type.upper()}"
                        ).classes("text-[10px] text-slate-500 uppercase tracking-widest")

                with ui.row().classes("items-center gap-4"):
                    # Lazy import to avoid circular dependencies
                    from .status_badge import StatusBadge

                    StatusBadge(self.work_item.status).render()
                    ui.button(icon="close", on_click=dialog.close).props(
                        "flat round color=slate-400"
                    )

            with ui.scroll_area().classes("h-[70vh] w-full p-6"):
                # Metadata Grid (High Contrast)
                with ui.grid(columns=3).classes(
                    "w-full gap-6 mb-8 p-6 bg-slate-800/50 rounded-2xl border border-slate-700/50"
                ):
                    self._info_item("Наряд", self.work_item.sidra_number or "—")
                    self._info_item("Тип", self.work_item.work_item_type)
                    self._info_item("Шаг Сидры (Тор)", self.work_item.sidra_step or "—")
                    self._info_item("Проект ID", str(self.work_item.project_id))

                    if self.work_item.doc_received_at:
                        self._info_item(
                            "Документация",
                            self.work_item.doc_received_at.strftime("%d.%m.%Y %H:%M"),
                        )

                    with ui.column().classes("col-span-3 gap-1 mt-2"):
                        ui.label("ПУТЬ К ФАЙЛАМ").classes(
                            "text-[10px] text-teal-400 font-black tracking-tighter"
                        )
                        ui.label(self.work_item.folder_path).classes(
                            "text-xs text-slate-300 font-mono break-all bg-slate-900/50 p-2 rounded border border-slate-700/50"
                        )

                # Action Buttons
                with ui.row().classes("gap-3 mb-8"):
                    from .explorer_button import ExplorerButton

                    ExplorerButton(
                        path=self.work_item.folder_path,
                        label="ОТКРЫТЬ ПАПКУ",
                    ).render()

                    if self.on_navigate:
                        ui.button(
                            "🎯 К ЗАДАЧАМ",
                            on_click=lambda: self._go_to_task_board(dialog),
                        ).props("color=indigo-500 unelevated rounded-xl").classes("font-bold")

                    if self.work_item.status in (WorkItemStatus.NEW, WorkItemStatus.PENDING_CUTS):
                        ui.button(
                            "✅ ПОЛУЧИТЬ ДОКУМЕНТ",
                            on_click=lambda: self._register_document(dialog),
                        ).props("color=emerald-500 unelevated rounded-xl").classes("font-bold")

                # Tasks Section
                with ui.column().classes("w-full gap-4"):
                    ui.label("СОСТАВ НАЗАДА (GNC ФАЙЛЫ)").classes(
                        "text-xs font-black text-slate-500 tracking-widest"
                    )
                    self._render_tasks_table()

                # History Section
                ui.separator().classes("my-8 bg-slate-700/50")
                ui.label("ЖУРНАЛ СОБЫТИЙ").classes(
                    "text-xs font-black text-slate-500 tracking-widest mb-4"
                )
                self._render_work_log()

            # Footer
            with ui.row().classes(
                "w-full justify-end p-4 bg-slate-800/40 border-t border-slate-700/50"
            ):
                ui.button("ЗАКРЫТЬ", on_click=dialog.close).props("flat color=slate-400").classes(
                    "text-xs font-bold"
                )

        dialog.open()

    def _info_item(self, label: str, value: str, classes: str = "") -> None:
        """Helper for rendering metadata pairs with high contrast."""
        with ui.column().classes(f"gap-0 {classes}"):
            ui.label(label.upper()).classes(
                "text-[10px] text-teal-400 font-black tracking-tighter mb-1"
            )
            ui.label(value).classes("text-sm text-slate-100 font-semibold")

    @ui.refreshable
    def _render_tasks_table(self) -> None:
        """Рендерит таблицу задач внутри наряда с возможностью захвата."""
        columns = [
            {"name": "file_name", "label": "Файл GNC", "field": "file_name", "align": "left"},
            {"name": "sheet_qty", "label": "Листов", "field": "sheet_qty"},
            {"name": "status", "label": "Статус", "field": "status"},
            {"name": "actions", "label": "", "field": "id", "align": "right"},
        ]

        # Fetch tasks using the current session
        from sqlmodel import select

        tasks = self.system.session.exec(
            select(TaskItem).where(TaskItem.work_item_id == self.work_item.id)
        ).all()

        table = ui.table(columns=columns, rows=[t.model_dump() for t in tasks]).classes("w-full")

        # Add 'Assign to Me' action slot
        table.add_slot(
            "body-cell-actions",
            """
            <q-td :props="props">
                <q-btn flat round dense color="orange" icon="install_desktop"
                       @click="$parent.$emit('pull_task', props.row)"
                       v-if="props.row.status === 'NEW' || props.row.status === 'PLANNED'" />
            </q-td>
            """,
        )

        async def handle_pull(task_row):
            async def do_pull():
                from docuflow.features.task_board.system import TaskBoardSystem

                system = await self.get_system(TaskBoardSystem)
                node_id = system.config.node_id
                await system.assign_task_to_node(task_row["id"], node_id, self.user)
                ui.notify(
                    f"Файл {task_row['file_name']} добавлен в вашу корзину ({node_id})",
                    type="positive",
                )
                self._render_tasks_table.refresh()

            self.safe_action(do_pull, error_prefix="Ошибка захвата")

        table.on("pull_task", lambda e: handle_pull(e.args))

    def _render_work_log(self) -> None:
        """Рендерит лог аудита."""
        from sqlmodel import select

        logs = self.system.session.exec(
            select(WorkLog)
            .where(WorkLog.work_item_id == self.work_item.id)
            .order_by(WorkLog.created_at.desc())
        ).all()

        if not logs:
            ui.label("Log empty").classes("text-slate-400 italic")
            return

        with ui.column().classes("w-full gap-2"):
            for log in logs:
                with ui.row().classes("w-full items-start gap-4 text-sm"):
                    ui.label(log.created_at.strftime("%d.%m %H:%M")).classes("text-slate-500 w-24")
                    ui.label(log.message).classes("flex-grow")
                    if log.author:
                        ui.label(log.author).classes("text-blue-400")

    def _go_to_task_board(self, dialog) -> None:
        """Переходит к доске задач с фильтром по текущему наряду."""
        dialog.close()
        if self.on_navigate:
            ui.timer(
                0.1,
                lambda: self.on_navigate("task_board", filter_work_item=self.work_item.id),
                once=True,
            )

    def _register_document(self, dialog) -> None:
        """Действие: Регистрация получения документа."""

        async def do_register():
            system = await self.get_system(WorkItemSystem)
            self.work_item = system.register_document(self.work_item.id, self.user)
            dialog.close()

        self.safe_action(do_register, "Документ успешно зарегистрирован", "Ошибка регистрации")

    def _block_work_item(self, dialog) -> None:
        """Действие: Блокировка наряда."""

        async def do_block():
            system = await self.get_system(WorkItemSystem)
            system.update_status(
                self.work_item.id,
                WorkItemStatus.BLOCKED,
                reason_note="Заблокировано вручную из карточки",
            )
            dialog.close()

        self.safe_action(do_block, "Наряд заблокирован", "Ошибка")
