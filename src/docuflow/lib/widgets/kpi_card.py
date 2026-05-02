"""
KPICard - metric card for dashboard.

Displays: icon, value, label, subtitle.
"""

from nicegui import ui


class KPICard:
    """Карточка KPI метрики.

    Args:
        label: str — верхний лейбл (small, muted)
        value: str — главное значение (big, bold)
        subtitle: str — нижний subtitle (small, muted)
        icon: str — название иконки Material Icons
        icon_color: str — цвет иконки (default: teal)
        accent_color: str — цвет акцента для glow эффекта
    """

    def __init__(
        self,
        label: str,
        value: str,
        subtitle: str = "",
        icon: str = "",
        icon_color: str = "teal",
        accent_color: str = "",
    ) -> None:
        self.label = label
        self.value = value
        self.subtitle = subtitle
        self.icon = icon
        self.icon_color = icon_color
        self.accent_color = accent_color

    def render(self) -> None:
        """Рендерит KPI карточку."""
        base_classes: str = "card p-6 relative overflow-hidden"
        if self.accent_color:
            base_classes += f" border-l-4 border-{self.accent_color}"

        with ui.column().classes(base_classes):
            if self.icon:
                with ui.row().classes("items-center gap-2 mb-2"):
                    ui.icon(self.icon, size="20px", color=self.icon_color)
                    ui.label(self.label).classes(
                        "text-slate-400 font-bold text-xs tracking-tighter uppercase"
                    )
            else:
                ui.label(self.label).classes(
                    "text-slate-400 font-bold text-xs tracking-tighter uppercase mb-2"
                )

            ui.label(self.value).classes("text-3xl font-black text-white mt-1")

            if self.subtitle:
                ui.label(self.subtitle).classes(
                    "text-slate-400 text-[10px] mt-3 uppercase font-bold"
                )


class KPIGrid:
    """Сетка KPI карточек.

    Args:
        kpis: list[KPICard] — список KPI карточек
        gap: str — gap класс (default: "gap-4")
    """

    def __init__(self, kpis: list["KPICard"] | None = None, gap: str = "gap-4") -> None:
        self.kpis = kpis or []
        self.gap = gap

    def render(self) -> None:
        """Рендерит сетку KPI."""
        with ui.row().classes(f"w-full {self.gap} flex-wrap"):
            for kpi in self.kpis:
                with ui.column().classes("flex-1 min-w-[200px]"):
                    kpi.render()

    def add(self, kpi: "KPICard") -> "KPIGrid":
        """Добавляет KPI карточку."""
        self.kpis.append(kpi)
        return self
