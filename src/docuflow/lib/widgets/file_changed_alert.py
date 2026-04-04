"""
FileChangedAlert — баннер "Файл изменился на сети".

Показывает уведомление, когда файл изменился на сетевом диске.
"""
from nicegui import ui


class FileChangedAlert:
    """
    Баннер уведомления об изменении файла.
    
    Props:
        file_name: str — имя файла
        file_path: str — путь к файлу
        on_refresh: callable — callback для обновления
    """
    
    def __init__(self, file_name: str, file_path: str, on_refresh=None):
        self.file_name = file_name
        self.file_path = file_path
        self.on_refresh = on_refresh
    
    def render(self) -> ui.card:
        """Рендерит баннер уведомления."""
        with ui.card().classes("bg-orange-100 border-l-4 border-orange-500 p-4") as card:
            with ui.row().classes("items-center gap-2"):
                ui.icon("warning").classes("text-orange-500")
                ui.label(f"Файл изменился: {self.file_name}").classes("text-orange-800 font-medium")
                
                if self.on_refresh:
                    ui.button("Обновить", on_click=self.on_refresh).props("flat color=orange")
                
                ui.button("Закрыть", on_click=card.delete).props("flat color=gray")
        
        return card