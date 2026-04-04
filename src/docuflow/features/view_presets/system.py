"""
ViewPresetSystem — управление пресетами видов (Notion-style).

Реализует CRUD для пресетов, управление активными пресетами,
разделение личных и глобальных пресетов.

Архитектура: Vertical Slice (features/view_presets/system.py)
"""
import json
from typing import Optional, List
from sqlmodel import Session, select

from docuflow.domain.entities.production import ViewPreset
from docuflow.application.base import BaseSystem
from docuflow.infrastructure.config import Config


class ViewPresetSystem(BaseSystem):
    """
    Система управления пресетами видов.
    
    Vertical Slice: features/view_presets/system.py
    
    Основные операции:
    - create — создание пресета
    - list — получение списка пресетов (global + personal)
    - get_active — получение активного пресета
    - set_active — установка активного пресета
    - delete — удаление пресета (с проверкой прав)
    """
    
    def __init__(self, config: Config, session: Session):
        """
        Инициализация ViewPresetSystem.
        
        Args:
            config: Конфигурация приложения
            session: SQLModel сессия для работы с БД
        """
        super().__init__(config)
        self.session = session
    
    def create(
        self,
        module: str,
        owner: str,
        name: str,
        preset_json: dict,
        is_default: bool = False,
    ) -> ViewPreset:
        """
        Создаёт новый пресет.
        
        Args:
            module: Название модуля (например, "work_items", "task_board")
            owner: Владелец ("global" или username)
            name: Имя пресета
            preset_json: Конфигурация пресета (view_type, columns, filters, sort, group_by)
            is_default: Является ли пресетом по умолчанию
        
        Returns:
            ViewPreset — созданный пресет
        """
        preset = ViewPreset(
            module=module,
            owner=owner,
            name=name,
            preset_json=json.dumps(preset_json, ensure_ascii=False),
            is_default=is_default,
        )
        
        self.session.add(preset)
        self.session.commit()
        self.session.refresh(preset)
        
        return preset
    
    def list(self, module: str, owner: str) -> List[ViewPreset]:
        """
        Возвращает список пресетов для модуля и пользователя.
        
        Args:
            module: Название модуля
            owner: Имя пользователя
        
        Returns:
            List[ViewPreset] — список пресетов (global + personal)
        """
        stmt = select(ViewPreset).where(
            ViewPreset.module == module,
            (ViewPreset.owner == "global") | (ViewPreset.owner == owner)
        )
        
        return list(self.session.exec(stmt).all())
    
    def get_active(self, module: str, owner: str) -> Optional[ViewPreset]:
        """
        Получает активный пресет для модуля и пользователя.
        
        Args:
            module: Название модуля
            owner: Имя пользователя
        
        Returns:
            Optional[ViewPreset] — активный пресет или None
        """
        # Сначала ищем personal active
        stmt = select(ViewPreset).where(
            ViewPreset.module == module,
            ViewPreset.owner == owner,
            ViewPreset.is_default == True
        )
        preset = self.session.exec(stmt).first()
        
        if preset:
            return preset
        
        # Если нет personal active, ищем global default
        stmt = select(ViewPreset).where(
            ViewPreset.module == module,
            ViewPreset.owner == "global",
            ViewPreset.is_default == True
        )
        return self.session.exec(stmt).first()
    
    def set_active(self, module: str, owner: str, preset_id: int) -> ViewPreset:
        """
        Устанавливает активный пресет.
        
        Args:
            module: Название модуля
            owner: Имя пользователя
            preset_id: ID пресета
        
        Returns:
            ViewPreset — активный пресет
        
        Raises:
            ValueError: если пресет не найден
        """
        # Сбрасываем все default для этого модуля и пользователя
        stmt = select(ViewPreset).where(
            ViewPreset.module == module,
            ViewPreset.owner == owner,
        )
        presets = self.session.exec(stmt).all()
        for p in presets:
            p.is_default = False
            self.session.add(p)
        
        # Устанавливаем новый default
        preset = self.session.get(ViewPreset, preset_id)
        if preset is None:
            raise ValueError(f"Пресет с ID {preset_id} не найден")
        
        if preset.module != module:
            raise ValueError(f"Пресет не принадлежит модулю {module}")
        
        if preset.owner != owner and preset.owner != "global":
            raise ValueError(f"Пресет не принадлежит пользователю {owner}")
        
        preset.is_default = True
        self.session.add(preset)
        self.session.commit()
        self.session.refresh(preset)
        
        return preset
    
    def delete(self, preset_id: int, owner: str) -> None:
        """
        Удаляет пресет.
        
        Args:
            preset_id: ID пресета
            owner: Имя пользователя (для проверки прав)
        
        Raises:
            ValueError: если пресет не найден
            PermissionError: если нет прав на удаление
        """
        preset = self.session.get(ViewPreset, preset_id)
        if preset is None:
            raise ValueError(f"Пресет с ID {preset_id} не найден")
        
        # Проверка прав: нельзя удалять global пресеты обычным пользователям
        if preset.owner == "global" and owner != "admin":
            raise PermissionError("Нельзя удалять глобальные пресеты")
        
        # Проверка прав: можно удалять только свои пресеты
        if preset.owner != "global" and preset.owner != owner:
            raise PermissionError("Нельзя удалять чужие пресеты")
        
        self.session.delete(preset)
        self.session.commit()
    
    def get_preset_json(self, preset: ViewPreset) -> dict:
        """
        Возвращает конфигурацию пресета как словарь.
        
        Args:
            preset: Пресет
        
        Returns:
            dict — конфигурация пресета
        """
        return json.loads(preset.preset_json)