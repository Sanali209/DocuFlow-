"""
UI Utilities - Loading states, empty states, confirm dialogs.

Functional design improvements for better UX.
"""

from collections.abc import Callable
from typing import Any

from nicegui import ui


class LoadingSpinner:
    """Simple loading spinner with optional text."""

    def __init__(self, text: str = "Loading...", size: str = "md"):
        self.text = text
        self.size = size

    def render(self) -> None:
        """Renders loading state."""
        size_map = {"sm": "24px", "md": "48px", "lg": "64px"}
        icon_size = size_map.get(self.size, size_map["md"])

        with ui.column().classes("items-center justify-center gap-4 p-8"):
            ui.spinner(size=icon_size, color="teal").classes("")
            if self.text:
                ui.label(self.text).classes("text-slate-400 text-sm")


class LoadingSkeleton:
    """Skeleton loader for cards/rows while data loads."""

    def __init__(
        self,
        lines: int = 3,
        line_class: str = "h-4 rounded",
        gap: str = "gap-2",
    ):
        self.lines = lines
        self.line_class = line_class
        self.gap = gap

    def render(self) -> None:
        """Renders skeleton animation."""
        with ui.column().classes(f"w-full {self.gap}"):
            for i in range(self.lines):
                width = "w-full" if i == 0 else f"w-{(100 - (i * 15))}%"
                ui.element("div").classes(
                    f"{self.line_class} {width} bg-slate-700/50 animate-pulse"
                )


class SkeletonCard:
    """Skeleton card for dashboard KPIs."""

    def __init__(self, label: str = ""):
        self.label = label

    def render(self) -> None:
        """Renders a skeleton KPI card."""
        with ui.column().classes("card p-6"):
            if self.label:
                ui.element("div").classes("w-24 h-3 bg-slate-700/50 rounded animate-pulse")
            ui.element("div").classes("w-32 h-8 bg-slate-700/50 rounded mt-4 animate-pulse")
            ui.element("div").classes("w-20 h-2 bg-slate-700/50 rounded mt-4 animate-pulse")


class EmptyState:
    """Empty state with icon and optional action button."""

    def __init__(
        self,
        icon: str = "inbox",
        title: str = "No data",
        subtitle: str = "",
        action_label: str = "",
        on_action: Callable | None = None,
    ):
        self.icon = icon
        self.title = title
        self.subtitle = subtitle
        self.action_label = action_label
        self.on_action = on_action

    def render(self) -> None:
        """Renders empty state."""
        with ui.column().classes("items-center justify-center p-8 gap-4"):
            ui.icon(self.icon, size="48px", color="slate-600")
            ui.label(self.title).classes("text-lg font-bold text-slate-300")
            if self.subtitle:
                ui.label(self.subtitle).classes("text-sm text-slate-500")
            if self.action_label and self.on_action:
                ui.button(self.action_label, icon="add", on_click=self.on_action).props(
                    "color=teal"
                )


class ErrorState:
    """Error state with retry button."""

    def __init__(
        self,
        message: str = "Error loading data",
        on_retry: Callable | None = None,
    ):
        self.message = message
        self.on_retry = on_retry

    def render(self) -> None:
        """Renders error state."""
        with ui.column().classes("items-center justify-center p-8 gap-4"):
            ui.icon("error_outline", size="48px", color="red-400")
            ui.label(self.message).classes("text-lg text-red-400")
            if self.on_retry:
                ui.button("Retry", icon="refresh", on_click=self.on_retry).props(
                    "outline color=red"
                )


class ConfirmDialog:
    """Confirmation dialog for critical actions."""

    def __init__(
        self,
        title: str = "Confirm",
        message: str = "Are you sure?",
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        confirm_color: str = "red",
        on_confirm: Callable | None = None,
        on_cancel: Callable | None = None,
    ):
        self.title = title
        self.message = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.confirm_color = confirm_color
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

    def render(self) -> Any:
        """Renders confirmation dialog."""
        with ui.dialog() as dialog, ui.card().classes("card p-6 w-[400px]"):
            ui.label(self.title).classes("text-xl font-bold text-white mb-4")

            with ui.row().classes("gap-2 mb-4"):
                ui.icon("warning", color="orange-400")
                ui.label(self.message).classes("text-slate-300")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    self.cancel_label,
                    on_click=lambda: (dialog.close(), self.on_cancel() if self.on_cancel else None),
                ).props("flat")
                ui.button(
                    self.confirm_label,
                    on_click=lambda: (
                        dialog.close(),
                        self.on_confirm() if self.on_confirm else None,
                    ),
                ).props(f"color={self.confirm_color}")

        return dialog


class NotifyHelper:
    """Helper for consistent notifications."""

    @staticmethod
    def success(message: str) -> None:
        ui.notify(message, type="positive", position="top-right")

    @staticmethod
    def error(message: str) -> None:
        ui.notify(message, type="negative", position="top-right")

    @staticmethod
    def warning(message: str) -> None:
        ui.notify(message, type="warning", position="top-right")

    @staticmethod
    def info(message: str) -> None:
        ui.notify(message, type="info", position="top-right")


def get_kpi_color(value: float, thresholds: dict[float, str] | None = None) -> str:
    """Returns a Quasar color string based on value thresholds.

    Default logic:
    - < 5: emerald (excellent)
    - < 20: orange (warning)
    - >= 20: red (critical)
    """
    t = thresholds or {0: "emerald", 5: "orange", 20: "red"}
    # Sort keys descending to check from highest threshold
    for limit in sorted(t.keys(), reverse=True):
        if value >= limit:
            return t[limit]
    return "grey"


def get_node_status_color(status: str) -> str:
    """Returns a Quasar color string for node status (Cyrillic)."""
    colors = {
        "Свободен": "gray",
        "Режет": "green",
        "На паузе": "orange",
        "Ожидание": "blue",
    }
    return colors.get(status, "gray")


def get_action_color(action: str) -> str:
    """Returns a Quasar color string for standard action buttons."""
    colors = {
        "start": "green",
        "pause": "orange",
        "complete": "green",
        "resume": "green",
        "block": "red",
        "claim": "teal",
    }
    return colors.get(action.lower(), "gray")


def get_role_indicator_color(is_leader: bool) -> str:
    """Returns Tailwind color string for cluster role indicators."""
    return "emerald-400" if is_leader else "indigo-400"


def get_sync_indicator_color(is_active: bool) -> str:
    """Returns Tailwind color string for sync/scan active indicators."""
    return "emerald-400" if is_active else "slate-500"
