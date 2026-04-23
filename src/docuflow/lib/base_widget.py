from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar

from nicegui import ui

from docuflow.application.base import BaseSystem

T = TypeVar("T", bound=BaseSystem)


class BaseDocuWidget:
    """
    Базовый класс для всех виджетов DocuFlow.
    Предоставляет унифицированные методы для выполнения действий и доступа к системам.
    """

    def __init__(self, system_scope: Any = None):
        self.system_scope = system_scope

    @asynccontextmanager
    async def scope(self):
        """Provides a safe request scope for resolving and using systems."""
        if not self.system_scope:
            raise RuntimeError("System scope is not set for this widget.")
        async with self.system_scope() as req:
            yield req

    async def get_system(self, system_cls: type[T]) -> T:
        """Типизированное получение системы через провайдер (Legacy)."""
        if not self.system_scope:
            raise RuntimeError("System scope is not set for this widget.")
        async with self.system_scope() as req:
            return await req.get(system_cls)

    def safe_action(
        self, action_fn: Callable, success_msg: str | None = None, error_prefix: str = "Ошибка"
    ):
        """
        Безопасно выполняет асинхронное действие с уведомлением об успехе или ошибке.

        Args:
            action_fn: Асинхронная функция действия.
            success_msg: Сообщение при успехе.
            error_prefix: Префикс для сообщения об ошибке.
        """

        async def wrapped_action():
            from docuflow.lib.widgets.ui_utils import NotifyHelper
            try:
                await action_fn()
                if success_msg:
                    NotifyHelper.success(success_msg)
            except Exception as e:
                NotifyHelper.error(f"{error_prefix}: {e}")

        ui.timer(0, wrapped_action, once=True)
