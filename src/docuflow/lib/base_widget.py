from collections.abc import Callable
from typing import Any, TypeVar

from nicegui import ui

from docuflow.application.base import BaseSystem

T = TypeVar("T", bound=BaseSystem)


class BaseDocuWidget:
    """
    Базовый класс для всех виджетов DocuFlow.
    Предоставляет унифицированные методы для выполнения действий и доступа к системам.
    """

    def __init__(self, system_provider: Any = None):
        self.system_provider = system_provider

    async def get_system(self, system_cls: type[T]) -> T:
        """Типизированное получение системы через провайдер."""
        if not self.system_provider:
            raise RuntimeError("System provider is not set for this widget.")
        return await self.system_provider(system_cls)

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
            try:
                await action_fn()
                if success_msg:
                    ui.notify(success_msg, type="positive")
            except Exception as e:
                ui.notify(f"{error_prefix}: {e}", type="negative")

        ui.timer(0, wrapped_action, once=True)
