"""
StatusIndicator — точка-индикатор статуса (онлайн/офлайн).

Используется для: node status, connection status, sync status.
"""

from nicegui import ui


class StatusIndicator:
    """Status indicator dot.

    Args:
        status: str - "online", "offline", "syncing", "warning", "error"
        size: str - dot size (sm, md, lg)
        show_label: bool - show text label
    """

    def __init__(
        self,
        status: str = "offline",
        size: str = "md",
        show_label: bool = False,
    ):
        self.status = status
        self.size = size
        self.show_label = show_label

    def render(self) -> None:
        """Renders indicator."""
        color_map = {
            "online": "positive",
            "offline": "grey-6",
            "syncing": "info",
            "warning": "warning",
            "error": "negative",
        }

        size_map = {
            "sm": "w-2 h-2",
            "md": "w-3 h-3",
            "lg": "w-4 h-4",
        }

        color = color_map.get(self.status, "grey-6")
        dot_size = size_map.get(self.size, size_map["md"])

        with ui.row().classes("items-center gap-2"):
            ui.badge().props(f"color={color} round").classes(f"bg-{color} {dot_size} p-0")

            if self.show_label:
                label_map = {
                    "online": "Online",
                    "offline": "Offline",
                    "syncing": "Syncing",
                    "warning": "Warning",
                    "error": "Error",
                }
                ui.label(label_map.get(self.status, "Unknown")).classes(
                    f"text-xs font-medium text-{color}"
                )


class StatusDot:
    """Simple dot without label.

    Args:
        color: str - teal, emerald, amber, red, grey
        size: str - sm, md, lg
    """

    def __init__(self, color: str = "teal", size: str = "md"):
        self.color = color
        self.size = size

    def render(self) -> ui.badge:
        """Renders dot."""
        size_map = {
            "sm": "w-2 h-2",
            "md": "w-3 h-3",
            "lg": "w-4 h-4",
        }

        return (
            ui.badge()
            .props("color={self.color} round")
            .classes(f"bg-{self.color} {size_map.get(self.size, size_map['md'])} p-0")
        )
