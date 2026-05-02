"""
BucketPanel — корзина оператора с батчами.

Отображает все батчи, назначенные оператору на узле.
"""

from typing import Any

from loguru import logger
from nicegui import ui
from sqlmodel import Session

from docuflow.domain.entities.production import (
    TaskItem,
    TaskItemStatus,
    WorkerBucketEntry,
)
from docuflow.features.task_board.system import TaskBoardSystem
from docuflow.lib.base_widget import BaseDocuWidget
from docuflow.lib.widgets.ui_utils import NotifyHelper


class BucketPanel(BaseDocuWidget):
    """
    Панель корзины оператора.

    Props:
        node_id: str — ID узла (лазера)
        user: str — текущий пользователь
        system_scope: Any — провайдер для получения свежих систем
    """

    def __init__(
        self,
        node_id: str,
        user: str,
        system_scope: Any,
    ) -> None:
        super().__init__(system_scope)
        self.node_id = node_id
        self.user = user

    @ui.refreshable
    async def render(self) -> None:
        """Рендерит панель корзины с разделением на очереди."""
        # Validate node_id
        if not self.node_id or not isinstance(self.node_id, str):
            logger.warning(f"BucketPanel.render: invalid node_id={self.node_id!r}")
            with ui.column().classes("w-full p-4 items-center"):
                ui.label("⚠️ Рабочее место не выбрано").classes("text-yellow-400 font-bold")
            return

        logger.debug(f"BucketPanel.render: node_id={self.node_id!r}")

        async with self.scope() as req:
            session: Session = await req.get(Session)
            system: TaskBoardSystem = await req.get(TaskBoardSystem)
            bucket_entries: list[WorkerBucketEntry] = system.get_bucket(self.node_id)

            if not bucket_entries:
                self._render_empty_bucket()
                return

            # Группируем по task_group_id
            batches = self._group_by_task_group(session, bucket_entries)

            # Разделяем на Активные (есть хоть одна задача IN_PROGRESS) и Предстоящие
            active_batches: dict[str, list[TaskItem]] = {}
            upcoming_batches: dict[str, list[TaskItem]] = {}

            for bid, tasks in batches.items():
                if any(t.status == TaskItemStatus.IN_PROGRESS for t in tasks):
                    active_batches[bid] = tasks
                else:
                    upcoming_batches[bid] = tasks

            with ui.column().classes("w-full gap-6"):
                # --- SECTION: ACTIVE ---
                if active_batches:
                    ui.label("🔥 В РАБОТЕ СЕЙЧАС").classes(
                        "text-xs font-black text-orange-500 tracking-widest"
                    )
                    for bid, tasks in active_batches.items():
                        self._render_batch_card(session, system, bid, tasks, is_active=True)

                # --- SECTION: UPCOMING ---
                if upcoming_batches:
                    with ui.row().classes("items-center gap-2 mt-4"):
                        ui.label("⏳ ОЧЕРЕДЬ НА ПОДГОТОВКУ").classes(
                            "text-xs font-black text-slate-500 tracking-widest"
                        )
                        ui.badge(str(len(upcoming_batches))).props("color=slate-700 size=xs")

                    for bid, tasks in upcoming_batches.items():
                        self._render_batch_card(session, system, bid, tasks, is_active=False)

    def _render_batch_card(
        self,
        session: Session,
        system: TaskBoardSystem,
        task_group_id: str,
        tasks: list[TaskItem],
        is_active: bool = False,
    ) -> None:
        """Вспомогательный метод для рендера карточки группы задач."""
        drift: float = self._calculate_batch_drift(tasks)

        # Ленивый импорт
        from .batch_card import BatchCard

        with ui.column().classes("w-full relative"):
            # Добавляем визуальный акцент для активного батча
            card_classes: str = (
                "border-l-8 border-orange-500 shadow-xl scale-[1.02]" if is_active else ""
            )

            with ui.card().classes(card_classes):
                BatchCard(
                    task_group_id=task_group_id,
                    tasks=tasks,
                    drift_percent=drift,
                    node_id=self.node_id,
                    user=self.user,
                    system_scope=self.system_scope,
                    on_start=self._on_start_task,
                    on_pause=self._on_pause_task,
                    on_resume=self._on_resume_task,
                    on_complete=self._on_complete_task,
                    on_block=self._on_block_task,
                ).render()

            # Если батч не активен, даем возможность "поднять" его (приоритет)
            if not is_active and len(tasks) > 0:
                with ui.row().classes("absolute -top-3 right-4"):
                    ui.button(
                        icon="expand_less", on_click=lambda: NotifyHelper.info("Приоритет повышен")
                    ).props("round flat size=sm color=slate-400 bg-white shadow-sm")

    def _render_empty_bucket(self) -> None:
        """Рендерит пустую корзину."""
        with ui.card().classes("w-full p-8 text-center"):
            ui.icon("inbox").classes("text-6xl text-slate-400 mb-4")
            ui.label("Корзина пуста").classes("text-h6 text-slate-300")
            ui.label("Нет назначенных батчей").classes("text-slate-500")

    def _group_by_task_group(
        self, session: Session, entries: list[WorkerBucketEntry]
    ) -> dict[str, list[TaskItem]]:
        """
        Группирует записи корзины по task_group_id (через TaskItem).

        Returns:
            dict[task_group_id_str, list[TaskItem]]
        """
        batches: dict[str, list[TaskItem]] = {}

        entry: WorkerBucketEntry
        for entry in entries:
            task: TaskItem | None = session.get(TaskItem, entry.task_item_id)
            if task:
                group_id: str = (
                    str(task.task_group_id) if task.task_group_id else f"single_{task.id}"
                )
                if group_id not in batches:
                    batches[group_id] = []
                batches[group_id].append(task)

        return batches

    def _calculate_batch_drift(self, tasks: list[TaskItem]) -> float:
        """Вычисляет drift для батча."""
        total_estimated: int = sum(t.estimated_minutes or 0 for t in tasks)
        total_actual: int = sum(t.actual_minutes or 0 for t in tasks)

        if total_estimated == 0:
            return 0.0

        return (total_actual - total_estimated) / total_estimated * 100

    # === Callbacks ===

    def _on_start_task(self, task_id: int) -> None:
        """Обработчик кнопки 'Начать'."""

        async def do_start() -> None:
            async with self.scope() as req:
                system: TaskBoardSystem = await req.get(TaskBoardSystem)
                system.start_task(task_id)
            self.render.refresh()

        self.safe_action(do_start, "Задача начата")

    def _on_pause_task(self, task_id: int) -> None:
        """Обработчик кнопки 'Пауза' — открывает диалог причины."""
        from .bucket_panel_dialogs import PauseDialog

        async def show() -> None:
            await PauseDialog(
                task_id,
                on_success=self.render.refresh,
                system_scope=self.system_scope,
            ).render()

        ui.timer(0, show, once=True)

    def _on_resume_task(self, task_id: int) -> None:
        """Обработчик кнопки 'Возобновить'."""

        async def do_resume() -> None:
            async with self.scope() as req:
                system: TaskBoardSystem = await req.get(TaskBoardSystem)
                system.resume_task(task_id)
            await self.render.refresh()

        self.safe_action(do_resume, "Задача возобновлена")

    def _on_complete_task(self, task_id: int) -> None:
        """Обработчик кнопки 'Завершить' — открывает диалог."""
        from .bucket_panel_dialogs import CompleteDialog

        async def show() -> None:
            await CompleteDialog(
                task_id,
                on_success=self.render.refresh,
                system_scope=self.system_scope,
            ).render()

        ui.timer(0, show, once=True)

    def _on_block_task(self, task_id: int) -> None:
        """Обработчик кнопки 'Заблокировать' — открывает диалог причины."""
        from .bucket_panel_dialogs import BlockDialog

        async def show() -> None:
            await BlockDialog(
                task_id,
                on_success=self.render.refresh,
                system_scope=self.system_scope,
            ).render()

        ui.timer(0, show, once=True)
