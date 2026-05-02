"""
ViewPresetSystem — управление пресетами видов (Notion-style).

Реализует CRUD для пресетов, управление активными пресетами,
разделение личных и глобальных пресетов.
"""

import json
from collections.abc import Sequence

from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from docuflow.application.base import BaseSystem
from docuflow.domain.entities.production import ViewPreset
from docuflow.infrastructure.config import Config


class ViewPresetSystem(BaseSystem):
    """
    Система управления пресетами видов.

    Основные операции:
    - create — создание пресета
    - list — получение списка пресетов (global + personal)
    - get_active — получение активного пресета
    - set_active — установка активного пресета
    - delete — удаление пресета (с проверкой прав)
    """

    def __init__(self, config: Config, session: Session) -> None:
        """
        Инициализация ViewPresetSystem.

        Args:
            config: Конфигурация приложения
            session: SQLModel сессия для работы с БД
        """
        super().__init__(config, session)

    def create(
        self,
        view_name: str,
        user_id: str,
        name: str,
        filters_json: dict,
        is_default: bool = False,
    ) -> ViewPreset:
        """
        Создаёт новый пресет.

        Args:
            view_name: Название вида (например, "work_items", "task_board")
            user_id: Владелец ("global" или username)
            name: Имя пресета
            filters_json: Конфигурация фильтров
            is_default: Является ли пресетом по умолчанию

        Returns:
            ViewPreset — созданный пресет
        """
        preset: ViewPreset = ViewPreset(
            view_name=view_name,
            user_id=user_id,
            name=name,
            filters_json=json.dumps(filters_json, ensure_ascii=False),
            is_default=is_default,
        )

        self.db_session.add(preset)
        self.db_session.commit()
        self.db_session.refresh(preset)

        return preset

    def list_presets(self, view_name: str, user_id: str) -> list[ViewPreset]:
        """
        Возвращает список пресетов для вида и пользователя.

        Args:
            view_name: Название вида
            user_id: Имя пользователя

        Returns:
            List[ViewPreset] — список пресетов (global + personal)
        """
        stmt: SelectOfScalar[ViewPreset] = select(ViewPreset).where(
            ViewPreset.view_name == view_name,
            (ViewPreset.user_id == "global") | (ViewPreset.user_id == user_id),
        )

        return list(self.db_session.exec(stmt).all())

    def list_global(self) -> list[ViewPreset]:
        """Returns all global presets across all views."""
        stmt: SelectOfScalar[ViewPreset] = select(ViewPreset).where(ViewPreset.user_id == "global")
        return list(self.db_session.exec(stmt).all())

    def get_active(self, view_name: str, user_id: str) -> ViewPreset | None:
        """
        Получает активный пресет для вида и пользователя.

        Args:
            view_name: Название вида
            user_id: Имя пользователя

        Returns:
            Optional[ViewPreset] — активный пресет или None
        """
        # Сначала ищем personal active
        stmt: SelectOfScalar[ViewPreset] = select(ViewPreset).where(
            ViewPreset.view_name == view_name,
            ViewPreset.user_id == user_id,
            ViewPreset.is_default.is_(True),  # type: ignore[attr-defined]
        )
        preset: ViewPreset | None = self.db_session.exec(stmt).first()

        if preset:
            return preset

        # Если нет personal active, ищем global default
        global_stmt: SelectOfScalar[ViewPreset] = select(ViewPreset).where(
            ViewPreset.view_name == view_name,
            ViewPreset.user_id == "global",
            ViewPreset.is_default.is_(True),  # type: ignore[attr-defined]
        )
        return self.db_session.exec(global_stmt).first()

    def set_active(self, view_name: str, user_id: str, preset_id: int) -> ViewPreset:
        """
        Устанавливает активный пресет.

        Args:
            view_name: Название вида
            user_id: Имя пользователя
            preset_id: ID пресета

        Returns:
            ViewPreset — активный пресет

        Raises:
            ValueError: если пресет не найден
        """
        # Сбрасываем все default для этого вида и пользователя
        stmt: SelectOfScalar[ViewPreset] = select(ViewPreset).where(
            ViewPreset.view_name == view_name,
            ViewPreset.user_id == user_id,
        )
        presets: Sequence[ViewPreset] = self.db_session.exec(stmt).all()
        p: ViewPreset
        for p in presets:
            p.is_default = False
            self.db_session.add(p)

        # Устанавливаем новый default
        preset: ViewPreset | None = self.db_session.get(ViewPreset, preset_id)
        if preset is None:
            raise ValueError(f"Пресет с ID {preset_id} не найден")

        if preset.view_name != view_name:
            raise ValueError(f"Пресет не принадлежит виду {view_name}")

        if preset.user_id != user_id and preset.user_id != "global":
            raise ValueError(f"Пресет не принадлежит пользователю {user_id}")

        preset.is_default = True
        self.db_session.add(preset)
        self.db_session.commit()
        self.db_session.refresh(preset)

        return preset

    def delete_preset(self, preset_id: int, user_id: str) -> None:
        """
        Удаляет пресет.

        Args:
            preset_id: ID пресета
            user_id: Имя пользователя (для проверки прав)

        Raises:
            ValueError: если пресет не найден
            PermissionError: если нет прав на удаление
        """
        preset: ViewPreset | None = self.db_session.get(ViewPreset, preset_id)
        if preset is None:
            raise ValueError(f"Пресет с ID {preset_id} не найден")

        # Проверка прав: нельзя удалять global пресеты обычным пользователям
        if preset.user_id == "global" and user_id != "admin":
            raise PermissionError("Нельзя удалять глобальные пресеты")

        # Проверка прав: можно удалять только свои пресеты
        if preset.user_id != "global" and preset.user_id != user_id:
            raise PermissionError("Нельзя удалять чужие пресеты")

        self.db_session.delete(preset)
        self.db_session.commit()

    def get_preset_json(self, preset: ViewPreset) -> dict:
        """
        Возвращает конфигурацию пресета как словарь.

        Args:
            preset: Пресет

        Returns:
            dict — конфигурация пресета
        """
        return json.loads(preset.filters_json)
