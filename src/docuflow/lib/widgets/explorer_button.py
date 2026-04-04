"""
ExplorerButton — кнопка "📂 Открыть в Explorer".

Открывает папку в проводнике Windows через subprocess.Popen.
"""
import subprocess
from pathlib import Path
from nicegui import ui


class ExplorerButton:
    """
    Кнопка для открытия папки в проводнике Windows.
    
    Props:
        path: str | Path — путь к папке
        label: str — текст кнопки (по умолчанию "📂")
        tooltip: str — подсказка
    """
    
    def __init__(self, path: str | Path, label: str = "📂", tooltip: str = "Открыть в Explorer"):
        self.path = Path(path) if isinstance(path, str) else path
        self.label = label
        self.tooltip = tooltip
    
    def render(self) -> ui.button:
        """Рендерит кнопку."""
        return (
            ui.button(self.label)
            .props(f'flat round tooltip="{self.tooltip}"')
            .on_click(self._open_explorer)
        )
    
    def _open_explorer(self) -> None:
        """Открывает папку в проводнике."""
        try:
            subprocess.Popen(["explorer.exe", str(self.path)])
        except Exception as e:
            ui.notify(f"Ошибка открытия папки: {e}", type="negative")