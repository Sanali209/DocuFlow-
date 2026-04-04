"""
TaskBoardView — главный экран task board для оператора и бригадира.

Вид Оператора: корзина, батчи, прогресс, статусы.
Вид Бригадира: все узлы, батчинг инструменты, приоритеты.
"""
from typing import Optional
from nicegui import ui
from sqlmodel import Session, select

from docuflow.domain.entities.production import (
    TaskItem,
    TaskItemStatus,
    WorkerBucketEntry,
)
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.features.task_board.batch_engine import BatchEngine
from docuflow.features.view_presets.system import ViewPresetSystem
from docuflow.lib.widgets import StatusBadge, ExplorerButton
from docuflow.lib.widgets.bucket_panel import BucketPanel


class TaskBoardView:
    """
    Главный экран Task Board.
    
    Props:
        session: Session — сессия БД
        system: TaskBoardSystem — система управления задачами
        preset_system: ViewPresetSystem — система пресетов
        user: str — текущий пользователь
        node_id: str — ID узла (лазера)
        role: str — роль: "operator" или "foreman"
    """
    
    def __init__(
        self,
        session: Session,
        system: TaskBoardSystem,
        preset_system: ViewPresetSystem,
        user: str = "admin",
        node_id: str = "LASER_1",
        role: str = "operator",
    ):
        self.session = session
        self.system = system
        self.preset_system = preset_system
        self.user = user
        self.node_id = node_id
        self.role = role
    
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
    
    def _switch_role(self, role: str) -> None:
        """Переключает роль."""
        self.role = role
        self.render.refresh()
    
    # ==================== ВИД ОПЕРАТОРА ====================
    
    def _render_operator_view(self) -> None:
        """Рендерит вид оператора."""
        # Выбираем узел
        self._render_node_selector()
        
        # Корзина
        BucketPanel(
            session=self.session,
            system=self.system,
            node_id=self.node_id,
            user=self.user,
        ).render()
        
        # Передача смены
        with ui.row().classes("w-full justify-end mt-4"):
            ui.button("Сдать смену", icon="swap_horiz", on_click=self._show_handover_dialog).props("color=orange rounded-xl")

    def _show_handover_dialog(self):
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[400px] gap-4"):
            ui.label("Сдача смены").classes("text-xl font-bold text-orange-400")
            recv_operator = ui.input("Имя сменщика (кому передать)").props("dark standout rounded").classes("w-full")
            note = ui.textarea("Заметка по работе / материалу").props("dark standout rounded").classes("w-full")
            with ui.row().classes("w-full justify-between items-center"):
                ui.button("Отмена", on_click=dialog.close).props("flat text-color=slate-400")
                ui.button("ПОДТВЕРДИТЬ СДАЧУ", on_click=lambda: self._execute_handover(recv_operator.value, note.value, dialog)).props("color=orange rounded-xl").classes("font-bold")
        dialog.open()

    def _execute_handover(self, recv_operator: str, note: str, dialog):
        if not recv_operator:
            ui.notify("Укажите кому сдаете смену", type="warning")
            return
        self.system.handover(self.node_id, recv_operator, str(note) if note else "Смена закрыта без комментариев")
        ui.notify("Смена успешно передана", type="positive")
        dialog.close()
        self.render.refresh()

    
    def _render_node_selector(self) -> None:
        """Рендерит выбор узла."""
        nodes = self._get_available_nodes()
        
        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label("Узел:").classes("text-gray-600")
            ui.select(
                options={n: n for n in nodes},
                value=self.node_id,
                on_change=lambda e: self._select_node(e.value),
            ).classes("w-48")
    
    def _select_node(self, node_id: str) -> None:
        """Выбирает узел."""
        self.node_id = node_id
        self.render.refresh()
    
    # ==================== ВИД БРИГАДИРА ====================
    
    def _render_foreman_view(self) -> None:
        """Рендерит вид бригадира."""
        with ui.tabs().classes("w-full mb-4") as tabs:
            all_nodes_tab = ui.tab("Все узлы")
            batching_tab = ui.tab("Батчинг")
            unassigned_tab = ui.tab("Неназначенные")
        
        with ui.tab_panels(tabs, value=all_nodes_tab).classes("w-full"):
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
            with ui.card().classes("w-full mb-4 p-4"):
                with ui.row().classes("items-center justify-between mb-2"):
                    ui.label(f"🔹 {node_id}").classes("text-h6")
                    node_status = self._get_node_status(node_id)
                    ui.badge(node_status).props(f'color={self._status_color(node_status)}')
                
                # Показываем батчи узла
                bucket_entries = self.system.get_bucket(node_id)
                if bucket_entries:
                    batches = self._group_by_batch(bucket_entries)
                    for batch_id, tasks in batches.items():
                        with ui.row().classes("gap-2 items-center ml-4 mb-2"):
                            StatusBadge(tasks[0].status).render() if tasks else None
                            ui.label(f"Батч {batch_id[:8]}...")
                            ui.label(f"{len(tasks)} задач")
                else:
                    ui.label("Нет активных батчей").classes("text-gray-400 ml-4")
    
    def _render_batching_panel(self) -> None:
        """Панель батчинга."""
        with ui.row().classes("gap-4 mb-4"):
            ui.button(
                "🔄 Авто-батчинг",
                on_click=self._run_auto_batching,
            ).props("color=blue")
        
        # Непривязанные задачи
        unassigned = self._get_unassigned_tasks()
        
        if unassigned:
            ui.label(f"Непривязанных задач: {len(unassigned)}").classes("mb-4")
            
            with ui.table(
                columns=[
                    {"name": "id", "label": "ID", "field": "id"},
                    {"name": "file_name", "label": "Файл", "field": "file_name"},
                    {"name": "sheet_qty", "label": "Листов", "field": "sheet_qty"},
                    {"name": "status", "label": "Статус", "field": "status"},
                ],
                rows=[
                    {
                        "id": t.id,
                        "file_name": t.file_name,
                        "sheet_qty": t.sheet_qty or "-",
                        "status": t.status.value,
                    }
                    for t in unassigned
                ],
                selection="multiple",
            ).classes("w-full") as table:
                pass
        else:
            ui.label("Все задачи назначены").classes("text-gray-500")
    
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
                        ui.label(f"Листов: {task.sheet_qty or '-'}").classes("text-sm text-gray-500")
                    
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
            ui.notify("Нет задач для батчинга", type="info")
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
                batch_group_id=batch_id,
                node_id=self.node_id,
                operator=self.user
            )
            ui.notify(f"Батч назначен на {self.node_id} (Worker: {self.user})", type="positive")
            self.render.refresh()
            
    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================
    
    def _get_available_nodes(self) -> list[str]:
        """Получает список доступных узлов."""
        # TODO: Получать из конфигурации или БД
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
        """Получает неназначенные задачи."""
        return list(self.session.exec(
            select(TaskItem).where(
                TaskItem.assigned_to_node.is_(None),
                TaskItem.status.in_([
                    TaskItemStatus.PLANNED,
                ]),
            )
        ).all())
    
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