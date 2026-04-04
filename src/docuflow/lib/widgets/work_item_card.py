"""
WorkItemCard — детальная карточка наряда (modal).

Отображает метаданные наряда, список задач (TaskItems) и лог событий (WorkLog).
Позволяет совершать действия: регистрация документа, блокировка.
"""
from typing import Optional
from nicegui import ui

from docuflow.domain.entities.production import (
    WorkItem,
    WorkItemStatus,
    WorkItemType,
    WorkLog,
    WorkLogType,
)
from docuflow.features.work_items.system import WorkItemSystem



class WorkItemCard:
    """
    Карточка наряда (modal или side panel).
    
    Props:
        work_item: WorkItem — наряд
        system: WorkItemSystem — система управления
        user: str — текущий пользователь (для логирования)
    """
    
    def __init__(
        self,
        work_item: WorkItem,
        system: WorkItemSystem,
        user: str = "admin",
    ):
        self.work_item = work_item
        self.system = system
        self.user = user
    
    def render(self) -> None:
        """Рендерит и открывает диалог с карточкой."""
        with ui.dialog() as dialog, ui.card().classes("w-[600px] max-w-none"):
            # Header
            with ui.row().classes("w-full items-center justify-between mb-4"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("assignment").classes("text-2xl text-blue-500")
                    ui.label(self.work_item.folder_name).classes("text-h6")
                
                # Lazy import to avoid circular dependencies
                from .status_badge import StatusBadge
                StatusBadge(self.work_item.status).render()
                
                ui.button(icon="close", on_click=dialog.close).props("flat round")
            
            with ui.scroll_area().classes("h-[70vh] w-full pr-4"):
                # Metadata Grid
                with ui.grid(columns=2).classes("w-full gap-4 mb-6 p-4 bg-gray-50 rounded"):
                    self._info_item("Наряд", self.work_item.sidra_number or "—")
                    self._info_item("Тип", self.work_item.work_item_type)
                    self._info_item("Шаг Сидры (Тор)", self.work_item.sidra_step or "—")
                    self._info_item("Проект ID", str(self.work_item.project_id))
                    
                    if self.work_item.doc_received_at:
                        self._info_item("Документация", self.work_item.doc_received_at.strftime('%d.%m.%Y %H:%M'))
                    
                    self._info_item("Путь", self.work_item.folder_path, classes="col-span-2 text-xs text-gray-500 italic")

                # Action Buttons
                with ui.row().classes("gap-2 mb-6"):
                    # Lazy import to avoid circular dependencies
                    from .explorer_button import ExplorerButton
                    ExplorerButton(
                        path=self.work_item.folder_path,
                        label="открыть папку",
                    ).render()
                    
                    if self.work_item.status in (WorkItemStatus.NEW, WorkItemStatus.PENDING_CUTS):
                        ui.button(
                            "✅ Получить документ",
                            on_click=lambda: self._register_document(dialog),
                        ).props("color=green outlined")
                    
                    if self.work_item.status != WorkItemStatus.BLOCKED:
                        ui.button(
                            "🔒 Блокировать",
                            on_click=lambda: self._block_work_item(dialog),
                        ).props("color=red flat")
                
                # Tasks Section
                ui.label("Прожиг (Задачи):").classes("text-subtitle1 font-bold mt-4 mb-2")
                self._render_tasks_table()
                
                # History Section
                ui.separator().classes("my-6")
                ui.label("История изменений:").classes("text-subtitle1 font-bold mb-2")
                self._render_work_log()
            
            # Footer
            with ui.row().classes("w-full justify-end mt-4"):
                ui.button("Закрыть", on_click=dialog.close).props("flat")
        
        dialog.open()

    def _info_item(self, label: str, value: str, classes: str = "") -> None:
        """Helper for rendering metadata pairs."""
        with ui.column().classes(f"gap-0 {classes}"):
            ui.label(label).classes("text-caption text-gray-500 uppercase font-bold")
            ui.label(value).classes("text-body1")
    
    def _render_tasks_table(self) -> None:
        """Рендерит таблицу задач."""
        tasks = self.work_item.tasks
        if not tasks:
            ui.label("Нет данных о задачах").classes("italic text-gray-400")
            return
            
        columns = [
            {"name": "step", "label": "Шаг", "field": "step_index", "align": "left"},
            {"name": "file", "label": "Файл GNC", "field": "file_name", "align": "left"},
            {"name": "status", "label": "Статус", "field": "status", "align": "center"},
            {"name": "qty", "label": "Листов", "field": "sheet_qty", "align": "right"},
        ]
        
        rows = [
            {
                "step_index": t.step_index or "-",
                "file_name": t.file_name,
                "status": t.status,
                "sheet_qty": t.sheet_qty or "-",
            }
            for t in tasks
        ]
        
        with ui.table(columns=columns, rows=rows).classes("w-full shadow-none border").props("flat dense hide-pagination"):
            # Custom status column rendering
            with ui.td(key="status") as td:
                ui.badge().bind_text_from(td, "value")
    
    def _render_work_log(self) -> None:
        """Рендерит историю событий."""
        from sqlmodel import select
        logs = self.system.db_session.exec(select(WorkLog).where(WorkLog.work_item_id == self.work_item.id)).all()
        if not logs:
            ui.label("История пуста").classes("italic text-gray-400")
            return
            
        with ui.column().classes("w-full gap-2"):
            for log in sorted(logs, key=lambda l: l.created_at, reverse=True):
                with ui.row().classes("w-full items-start gap-4 p-2 border-b border-gray-100 last:border-0"):
                    ui.label(log.created_at.strftime("%H:%M")).classes("text-caption text-gray-500 w-12")
                    with ui.column().classes("gap-0 flex-grow"):
                        ui.label(log.message).classes("text-body2")
                        ui.label(f"👤 {log.author}").classes("text-[10px] text-gray-400 uppercase")
                    
                    # Icons for log types
                    icon = "info"
                    color = "blue"
                    if log.log_type == WorkLogType.STATUS_CHANGE.value:
                        icon = "swap_horiz"
                        color = "orange"
                    elif log.log_type == WorkLogType.SCAN_ERROR.value:
                        icon = "error"
                        color = "red"
                    
                    ui.icon(icon).classes(f"text-sm text-{color}-400")

    def _register_document(self, dialog: ui.dialog) -> None:
        """Обработка регистрации документа."""
        try:
            self.system.register_physical_document(self.work_item.id, author=self.user)
            ui.notify(f"Документ зарегистрирован", type="positive")
            dialog.close()
            # Note: The view should refresh items
        except Exception as e:
            ui.notify(f"Ошибка: {e}", type="negative")

    def _block_work_item(self, dialog: ui.dialog) -> None:
        """Блокировка наряда."""
        try:
            self.system.update_production_status(
                self.work_item.id, 
                new_status=WorkItemStatus.BLOCKED,
                reason_note="Заблокировано вручную из карточки"
            )
            ui.notify(f"Наряд заблокирован", type="warning")
            dialog.close()
        except Exception as e:
            ui.notify(f"Ошибка: {e}", type="negative")
